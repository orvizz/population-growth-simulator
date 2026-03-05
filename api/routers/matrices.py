from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import MatrixCreate, MatrixResponse, MatrixSummary, MatrixUpdate
from db.models import PopulationMatrix, User

router = APIRouter(prefix="/v1/matrices", tags=["matrices"])

_COMPADRE = "compadre"


def _get_matrix_or_404(matrix_id: int, db: Session) -> PopulationMatrix:
    matrix = db.get(PopulationMatrix, matrix_id)
    if matrix is None:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return matrix


def _assert_editable(matrix: PopulationMatrix, user: User) -> None:
    """Raises 403 if the matrix is from COMPADRE or owned by a different user."""
    if matrix.source_type == _COMPADRE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="COMPADRE matrices are read-only",
        )
    if matrix.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this matrix",
        )


# ---------------------------------------------------------------------------
# GET /v1/matrices  — list (paginated, filterable)
# ---------------------------------------------------------------------------

@router.get("", response_model=list[MatrixSummary])
def list_matrices(
    species: str | None = Query(None, description="Partial species name filter (case-insensitive)"),
    kingdom: str | None = Query(None),
    country_code: str | None = Query(None),
    source_type: str | None = Query(None, description="'compadre' or 'custom'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(PopulationMatrix)
    if species:
        q = q.filter(PopulationMatrix.species_accepted.ilike(f"%{species}%"))
    if kingdom:
        q = q.filter(PopulationMatrix.kingdom == kingdom)
    if country_code:
        q = q.filter(PopulationMatrix.country_code == country_code)
    if source_type:
        q = q.filter(PopulationMatrix.source_type == source_type)
    return q.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# GET /v1/matrices/{id}  — single matrix with full data
# ---------------------------------------------------------------------------

@router.get("/{matrix_id}", response_model=MatrixResponse)
def get_matrix(matrix_id: int, db: Session = Depends(get_db)):
    return _get_matrix_or_404(matrix_id, db)


# ---------------------------------------------------------------------------
# POST /v1/matrices  — create (auth required, caller becomes owner)
# ---------------------------------------------------------------------------

@router.post("", response_model=MatrixResponse, status_code=status.HTTP_201_CREATED)
def create_matrix(
    body: MatrixCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matrix = PopulationMatrix(
        source_type="custom",
        owner_id=current_user.id,
        species_accepted=body.species_accepted,
        common_name=body.common_name,
        kingdom=body.kingdom,
        country_code=body.country_code,
        matrix_a=body.matrix_a,
        matrix_u=body.matrix_u,
        matrix_f=body.matrix_f,
        stage_names=body.stage_names,
        metadata_=None,
    )
    db.add(matrix)
    db.commit()
    db.refresh(matrix)
    return matrix


# ---------------------------------------------------------------------------
# PATCH /v1/matrices/{id}  — partial update (auth required, owner only, not COMPADRE)
# ---------------------------------------------------------------------------

@router.patch("/{matrix_id}", response_model=MatrixResponse)
def update_matrix(
    matrix_id: int,
    body: MatrixUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matrix = _get_matrix_or_404(matrix_id, db)
    _assert_editable(matrix, current_user)

    # Only apply fields that were explicitly included in the request body
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(matrix, field, value)

    db.commit()
    db.refresh(matrix)
    return matrix
