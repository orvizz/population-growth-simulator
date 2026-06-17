"""
Matrices controller — HTTP concerns only.

Parses requests, delegates to MatrixService, returns records.
No business logic, no DB access.
"""
import io
import json
import zipfile

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from api.records import BatchImportResult, MatrixRecord, MatrixShareRecord, MatrixSummaryRecord, UserRecord
from api.schemas import MatrixCreate, MatrixShareCreate, MatrixUpdate
from api.deps import get_current_user, get_matrix_service, get_optional_user
from api.services.matrix_service import MatrixService

router = APIRouter(prefix="/v1/matrices", tags=["matrices"])


@router.get("", response_model=list[MatrixSummaryRecord])
def list_matrices(
    species: str | None = Query(None, description="Partial species name (case-insensitive)"),
    kingdom: str | None = Query(None),
    country_code: str | None = Query(None),
    source_type: str | None = Query(None, description="'compadre' or 'custom'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserRecord | None = Depends(get_optional_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.list_matrices(
        caller_id=current_user.id if current_user else None,
        species=species,
        kingdom=kingdom,
        country_code=country_code,
        source_type=source_type,
        skip=skip,
        limit=limit,
    )


@router.post("/import", response_model=BatchImportResult)
async def import_matrices(
    files: list[UploadFile] = File(...),
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    """Import one or more JSON files or a single ZIP containing JSON files."""
    file_tuples: list[tuple[str, bytes]] = []
    for f in files:
        raw = await f.read()
        if (f.filename or "").lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".json") and not name.startswith("__MACOSX"):
                        file_tuples.append((name, zf.read(name)))
        else:
            file_tuples.append((f.filename or "file.json", raw))
    return service.import_matrices(file_tuples, user_id=current_user.id)


@router.get("/{matrix_id}/export")
def export_matrix(
    matrix_id: int,
    fmt: str = Query("json", alias="format", description="'json' or 'csv'"),
    current_user: UserRecord | None = Depends(get_optional_user),
    service: MatrixService = Depends(get_matrix_service),
):
    """Download a matrix as a JSON or CSV file."""
    user_id = current_user.id if current_user else None
    if fmt == "csv":
        csv_str, filename = service.export_csv(matrix_id, user_id)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    data = service.export_json(matrix_id, user_id)
    species = data.get("species_accepted") or f"matrix_{matrix_id}"
    filename = species.replace(" ", "_").replace("/", "_") + ".json"
    return Response(
        content=json.dumps(data),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/count")
def count_matrices(
    species: str | None = Query(None),
    kingdom: str | None = Query(None),
    source_type: str | None = Query(None),
    current_user: UserRecord | None = Depends(get_optional_user),
    service: MatrixService = Depends(get_matrix_service),
):
    total = service.count_matrices(
        caller_id=current_user.id if current_user else None,
        species=species,
        kingdom=kingdom,
        source_type=source_type,
    )
    return {"total": total}


@router.get("/{matrix_id}", response_model=MatrixRecord)
def get_matrix(
    matrix_id: int,
    current_user: UserRecord | None = Depends(get_optional_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.get_matrix(matrix_id,
                              caller_id=current_user.id if current_user else None)


@router.post("", response_model=MatrixRecord, status_code=status.HTTP_201_CREATED)
def create_matrix(
    body: MatrixCreate,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.create_matrix(body, owner_id=current_user.id)


@router.patch("/{matrix_id}", response_model=MatrixRecord)
def update_matrix(
    matrix_id: int,
    body: MatrixUpdate,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.update_matrix(matrix_id, body, user_id=current_user.id)


@router.delete("/{matrix_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_matrix(
    matrix_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    service.delete_matrix(matrix_id, user_id=current_user.id)


# ---------------------------------------------------------------------------
# Share endpoints
# ---------------------------------------------------------------------------

@router.get("/{matrix_id}/shares", response_model=list[MatrixShareRecord])
def list_shares(
    matrix_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.list_shares(matrix_id, user_id=current_user.id)


@router.post(
    "/{matrix_id}/shares",
    response_model=MatrixShareRecord,
    status_code=status.HTTP_201_CREATED,
)
def add_share(
    matrix_id: int,
    body: MatrixShareCreate,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    return service.share_matrix(matrix_id, body, user_id=current_user.id)


@router.delete("/{matrix_id}/shares/{shared_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_share(
    matrix_id: int,
    shared_user_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: MatrixService = Depends(get_matrix_service),
):
    service.unshare_matrix(matrix_id, shared_user_id=shared_user_id, user_id=current_user.id)
