"""
MatrixService — business logic for population matrices.

Responsibilities:
- Enforce access rules: COMPADRE matrices are immutable; only the owner
  may modify a custom matrix.
- Convert ORM objects into domain records before returning them.
- Delegate all DB access to MatrixRepository.

The service is the ONLY place where these business rules live.
Neither the controller nor the repository checks them.
"""
from fastapi import HTTPException, status

from api.records import MatrixRecord, MatrixSummaryRecord
from api.repositories.matrix_repository import MatrixRepository
from api.schemas import MatrixCreate, MatrixUpdate

_COMPADRE = "compadre"


class MatrixService:
    def __init__(self, repo: MatrixRepository) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_matrices(
        self,
        *,
        species: str | None = None,
        kingdom: str | None = None,
        country_code: str | None = None,
        source_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MatrixSummaryRecord]:
        rows = self._repo.list(
            species=species,
            kingdom=kingdom,
            country_code=country_code,
            source_type=source_type,
            skip=skip,
            limit=limit,
        )
        return [MatrixSummaryRecord.model_validate(r) for r in rows]

    def get_matrix(self, matrix_id: int) -> MatrixRecord:
        """Raises 404 if the matrix does not exist."""
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        return MatrixRecord.model_validate(matrix)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def create_matrix(self, data: MatrixCreate, *, owner_id: int) -> MatrixRecord:
        matrix = self._repo.create(
            owner_id=owner_id,
            species_accepted=data.species_accepted,
            common_name=data.common_name,
            kingdom=data.kingdom,
            country_code=data.country_code,
            matrix_a=data.matrix_a,
            matrix_u=data.matrix_u,
            matrix_f=data.matrix_f,
            stage_names=data.stage_names,
        )
        return MatrixRecord.model_validate(matrix)

    def update_matrix(
        self, matrix_id: int, data: MatrixUpdate, *, user_id: int
    ) -> MatrixRecord:
        """
        Raises:
            404 — matrix not found
            403 — matrix is from COMPADRE (immutable)
            403 — authenticated user is not the owner
        """
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")

        if matrix.source_type == _COMPADRE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="COMPADRE matrices are read-only",
            )
        if matrix.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this matrix",
            )

        updated = self._repo.update(matrix, data.model_dump(exclude_unset=True))
        return MatrixRecord.model_validate(updated)
