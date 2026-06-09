"""
Seed population_matrices from COMADRE JSON data.

Usage:
    python -m db.seed_comadre
"""
import argparse
import json
from pathlib import Path

from db.models import PopulationMatrix
from db.session import SessionLocal

DATA_DIR = Path(__file__).parent.parent / "data"
COMADRE_JSON = DATA_DIR / "COMADRE_v.4.21.8.0.json"

BATCH_SIZE = 500


def _sanitize_matrix(mat):
    """Recursively replace float NaN with None in nested lists (JSONB rejects NaN)."""
    if isinstance(mat, list):
        return [_sanitize_matrix(v) for v in mat]
    if isinstance(mat, float) and (mat != mat):
        return None
    return mat


def load_comadre():
    print(f"Loading {COMADRE_JSON.name}...")
    with open(COMADRE_JSON, encoding="utf-8") as f:
        data = json.load(f)

    metadata = data["metadata"]

    matrices_by_id = {}
    for m in data["mat"]:
        m_id = int(m["MatrixID"][0])
        matrices_by_id[m_id] = m

    classes_by_id = {}
    for class_list in data["matrixClass"]:
        if not class_list:
            continue
        m_id = int(class_list[0]["MatrixID"])
        classes_by_id[m_id] = [c["MatrixClassAuthor"] for c in class_list]

    return metadata, matrices_by_id, classes_by_id


def build_record(row: dict, matrices_by_id: dict, classes_by_id: dict) -> PopulationMatrix | None:
    m_id = int(row["MatrixID"])
    mat = matrices_by_id.get(m_id)
    if mat is None:
        return None

    extra = {
        "MatrixID": m_id,
        "Authors": row.get("Authors"),
        "YearPublication": row.get("YearPublication"),
        "DOI_ISBN": row.get("DOI_ISBN"),
        "Continent": row.get("Continent"),
        "OrganismType": row.get("OrganismType"),
        "MatrixComposite": row.get("MatrixComposite"),
        "MatrixTreatment": row.get("MatrixTreatment"),
        "StudyDuration": row.get("StudyDuration"),
        "MatrixDimension": row.get("MatrixDimension"),
        "SurvivalIssue": row.get("SurvivalIssue"),
    }

    return PopulationMatrix(
        source_type="comadre",
        owner_id=None,
        species_accepted=row.get("SpeciesAccepted"),
        common_name=row.get("CommonName"),
        kingdom=row.get("Kingdom"),
        country_code=row.get("Country"),
        matrix_a=_sanitize_matrix(mat.get("matA")),
        matrix_u=_sanitize_matrix(mat.get("matU")),
        matrix_f=_sanitize_matrix(mat.get("matF")),
        stage_names=classes_by_id.get(m_id),
        metadata_=extra,
        visibility="public",
    )


def seed():
    metadata, matrices_by_id, classes_by_id = load_comadre()

    total = len(metadata)
    print(f"Seeding {total} records into population_matrices...")

    inserted = 0
    skipped = 0

    with SessionLocal() as session:
        batch = []
        for row in metadata:
            record = build_record(row, matrices_by_id, classes_by_id)
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
    argparse.ArgumentParser(description="Seed COMADRE data").parse_args()
    seed()
