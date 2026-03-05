"""
Seed population_matrices from pre-processed COMPADRE data.

Usage:
    python -m db.seed_compadre
    python -m db.seed_compadre --rdata  # re-parse from .RData (slow, first time only)
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from db.models import PopulationMatrix
from db.session import SessionLocal

DATA_DIR = Path(__file__).parent.parent / "growt-simulator-app" / "data"
RDATA_PATH = DATA_DIR / "COMPADRE_v.6.25.8.0.RData"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_PARQUET = PROCESSED_DIR / "metadata.parquet"
MATRICES_JSON = PROCESSED_DIR / "matrices.json"

BATCH_SIZE = 500


def load_from_processed():
    df = pd.read_parquet(METADATA_PARQUET)
    with open(MATRICES_JSON) as f:
        matrices = json.load(f)
    return df, matrices


def load_from_rdata():
    import rdata

    print("Parsing RData (this takes a minute)...")
    parsed = rdata.parser.parse_file(str(RDATA_PATH))
    converted = rdata.conversion.convert(parsed)
    db = converted["compadre"]

    metadata = db[np.str_("metadata")]
    raw_mats = db[np.str_("mat")]
    raw_classes = db[np.str_("matrixClass")]

    matrices = {}
    for i, m in enumerate(raw_mats):
        m_id = str(int(m[np.str_("MatrixID")][0]))
        matrices[m_id] = {
            "matA": m[np.str_("matA")].values.tolist(),
            "matU": m[np.str_("matU")].values.tolist(),
            "matF": m[np.str_("matF")].values.tolist(),
            "class_names": raw_classes[i]["MatrixClassAuthor"].tolist(),
        }
    return metadata, matrices


def _nan_to_none(val):
    """Convert NaN/NaT to None so JSON serialisation works."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    return val


def _sanitize_matrix(mat):
    """Recursively replace float NaN with None in nested lists (JSONB rejects NaN)."""
    if isinstance(mat, list):
        return [_sanitize_matrix(v) for v in mat]
    if isinstance(mat, float) and (mat != mat):  # NaN check without importing math
        return None
    return mat


def build_record(row: pd.Series, matrices: dict) -> PopulationMatrix | None:
    m_id = str(int(row["MatrixID"]))
    mat = matrices.get(m_id)
    if mat is None:
        return None

    extra = {
        "MatrixID": int(row["MatrixID"]),
        "Authors": _nan_to_none(row.get("Authors")),
        "YearPublication": _nan_to_none(row.get("YearPublication")),
        "DOI_ISBN": _nan_to_none(row.get("DOI_ISBN")),
        "Continent": _nan_to_none(row.get("Continent")),
        "OrganismType": _nan_to_none(row.get("OrganismType")),
        "MatrixComposite": _nan_to_none(row.get("MatrixComposite")),
        "MatrixTreatment": _nan_to_none(row.get("MatrixTreatment")),
        "StudyDuration": _nan_to_none(row.get("StudyDuration")),
        "MatrixDimension": _nan_to_none(row.get("MatrixDimension")),
        "SurvivalIssue": _nan_to_none(row.get("SurvivalIssue")),
    }

    return PopulationMatrix(
        source_type="compadre",
        owner_id=None,
        species_accepted=_nan_to_none(row.get("SpeciesAccepted")),
        common_name=_nan_to_none(row.get("CommonName")),
        kingdom=_nan_to_none(row.get("Kingdom")),
        country_code=_nan_to_none(row.get("Country")),
        matrix_a=_sanitize_matrix(mat["matA"]),
        matrix_u=_sanitize_matrix(mat["matU"]),
        matrix_f=_sanitize_matrix(mat["matF"]),
        stage_names=mat["class_names"],
        metadata_=extra,
    )


def seed(use_rdata: bool = False):
    if use_rdata:
        df, matrices = load_from_rdata()
    else:
        print("Loading from pre-processed files...")
        df, matrices = load_from_processed()

    total = len(df)
    print(f"Seeding {total} records into population_matrices...")

    inserted = 0
    skipped = 0

    with SessionLocal() as session:
        batch = []
        for _, row in df.iterrows():
            record = build_record(row, matrices)
            if record is None:
                skipped += 1
                continue
            batch.append(record)

            if len(batch) >= BATCH_SIZE:
                session.add_all(batch)
                session.commit()
                inserted += len(batch)
                print(f"  {inserted}/{total}", end="\r")
                batch = []

        if batch:
            session.add_all(batch)
            session.commit()
            inserted += len(batch)

    print(f"\nDone. Inserted: {inserted}, skipped (no matrix data): {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rdata", action="store_true", help="Parse from .RData instead of processed files")
    args = parser.parse_args()
    seed(use_rdata=args.rdata)
