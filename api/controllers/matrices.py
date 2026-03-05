"""
Matrices controller — HTTP concerns only.

Parses requests, delegates to MatrixService, returns records.
No business logic, no DB access.
"""
from fastapi import APIRouter, Depends, Query, status

from api.records import MatrixRecord, MatrixSummaryRecord, UserRecord
from api.schemas import MatrixCreate, MatrixUpdate
from api.deps import get_current_user, get_matrix_service
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
    service: MatrixService = Depends(get_matrix_service),
):
    return service.list_matrices(
        species=species,
        kingdom=kingdom,
        country_code=country_code,
        source_type=source_type,
        skip=skip,
        limit=limit,
    )


@router.get("/{matrix_id}", response_model=MatrixRecord)
def get_matrix(matrix_id: int, service: MatrixService = Depends(get_matrix_service)):
    return service.get_matrix(matrix_id)


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
