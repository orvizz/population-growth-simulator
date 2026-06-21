"""
MatrixService — business logic for population matrices.

Responsibilities:
- Enforce access rules: COMPADRE matrices are immutable; only the owner
  may modify a custom matrix.
- Enforce visibility: private matrices are only visible to their owner;
  shared matrices are visible to the owner and explicitly shared users;
  public matrices are visible to everyone.
- Convert ORM objects into domain records before returning them.
- Delegate all DB access to MatrixRepository / UserRepository.

The service is the ONLY place where these business rules live.
"""
from fastapi import HTTPException, status

import json

from pydantic import ValidationError

from api.records import BatchImportResult, MatrixImportError, MatrixRecord, MatrixShareRecord, MatrixSummaryRecord
from api.repositories.matrix_repository import MatrixRepository
from api.repositories.user_repository import UserRepository
from api.schemas import MatrixCreate, MatrixImport, MatrixShareCreate, MatrixUpdate

_COMPADRE = "compadre"


class MatrixService:
    def __init__(self, repo: MatrixRepository, user_repo: UserRepository) -> None:
        self._repo = repo
        self._user_repo = user_repo

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_readable(self, matrix, caller_id: int | None) -> None:
        """Raise 403 if the caller cannot read this matrix."""
        if matrix.visibility == "public":
            return
        if caller_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="This matrix is private")
        if matrix.owner_id == caller_id:
            return
        if matrix.visibility == "shared":
            if any(s.shared_with_user_id == caller_id for s in matrix.shares):
                return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This matrix is private")

    def _assert_owner(self, matrix, user_id: int) -> None:
        if matrix.source_type == _COMPADRE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="COMPADRE matrices are read-only")
        if matrix.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You do not own this matrix")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_matrices(
        self,
        *,
        caller_id: int | None = None,
        mine: bool = False,
        species: str | None = None,
        kingdom: str | None = None,
        country_code: str | None = None,
        source_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MatrixSummaryRecord]:
        if mine and caller_id is None:
            return []
        rows = self._repo.list(
            caller_id=caller_id,
            owner_id=caller_id if mine else None,
            species=species,
            kingdom=kingdom,
            country_code=country_code,
            source_type=source_type,
            skip=skip,
            limit=limit,
        )
        return [MatrixSummaryRecord.model_validate(r) for r in rows]

    def count_matrices(
        self,
        *,
        caller_id: int | None = None,
        mine: bool = False,
        species: str | None = None,
        kingdom: str | None = None,
        source_type: str | None = None,
    ) -> int:
        if mine and caller_id is None:
            return 0
        return self._repo.count(
            caller_id=caller_id,
            owner_id=caller_id if mine else None,
            species=species,
            kingdom=kingdom,
            source_type=source_type,
        )

    def get_matrix(self, matrix_id: int, *, caller_id: int | None = None) -> MatrixRecord:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_readable(matrix, caller_id)
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
            visibility=data.visibility,
        )
        return MatrixRecord.model_validate(matrix)

    def update_matrix(
        self, matrix_id: int, data: MatrixUpdate, *, user_id: int
    ) -> MatrixRecord:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_owner(matrix, user_id)

        updates = data.model_dump(exclude_unset=True)

        # If owner removes all shares by setting visibility to private/public,
        # clean up the shares table so stale records don't accumulate.
        new_vis = updates.get("visibility")
        if new_vis in ("private", "public") and matrix.visibility == "shared":
            for share in list(matrix.shares):
                self._repo.remove_share(matrix.id, share.shared_with_user_id)

        updated = self._repo.update(matrix, updates)
        return MatrixRecord.model_validate(updated)

    def delete_matrix(self, matrix_id: int, *, user_id: int) -> None:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_owner(matrix, user_id)
        self._repo.delete(matrix)

    # ------------------------------------------------------------------
    # Share management
    # ------------------------------------------------------------------

    def list_shares(self, matrix_id: int, *, user_id: int) -> list[MatrixShareRecord]:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_owner(matrix, user_id)
        return [
            MatrixShareRecord(
                shared_with_user_id=s.shared_with_user_id,
                shared_with_username=s.shared_with_user.username,
            )
            for s in matrix.shares
        ]

    def share_matrix(
        self, matrix_id: int, data: MatrixShareCreate, *, user_id: int
    ) -> MatrixShareRecord:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_owner(matrix, user_id)

        target = self._user_repo.get_by_username(data.username)
        if target is None:
            raise HTTPException(status_code=404, detail=f"User '{data.username}' not found")
        if target.id == user_id:
            raise HTTPException(status_code=400, detail="You cannot share a matrix with yourself")

        if self._repo.get_share(matrix_id, target.id):
            raise HTTPException(status_code=409,
                                detail=f"Matrix already shared with '{data.username}'")

        # Auto-promote to "shared" visibility if still private
        if matrix.visibility == "private":
            self._repo.update(matrix, {"visibility": "shared"})

        share = self._repo.add_share(matrix_id, target.id)
        return MatrixShareRecord(
            shared_with_user_id=share.shared_with_user_id,
            shared_with_username=target.username,
        )

    def unshare_matrix(
        self, matrix_id: int, *, shared_user_id: int, user_id: int
    ) -> None:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_owner(matrix, user_id)

        if not self._repo.get_share(matrix_id, shared_user_id):
            raise HTTPException(status_code=404, detail="Share not found")

        self._repo.remove_share(matrix_id, shared_user_id)

        # If no more shares remain, revert visibility to private
        self._repo._db.refresh(matrix)
        if not matrix.shares:
            self._repo.update(matrix, {"visibility": "private"})

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    def export_json(self, matrix_id: int, user_id: int | None) -> dict:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_readable(matrix, user_id)
        return {
            "format_version": "1",
            "source_type": matrix.source_type,
            "species_accepted": matrix.species_accepted,
            "common_name": matrix.common_name,
            "kingdom": matrix.kingdom,
            "country_code": matrix.country_code,
            "matrix_a": matrix.matrix_a,
            "matrix_u": matrix.matrix_u,
            "matrix_f": matrix.matrix_f,
            "stage_names": matrix.stage_names,
        }

    def export_csv(self, matrix_id: int, user_id: int | None) -> tuple[str, str]:
        matrix = self._repo.get_by_id(matrix_id)
        if matrix is None:
            raise HTTPException(status_code=404, detail="Matrix not found")
        self._assert_readable(matrix, user_id)

        n = len(matrix.matrix_a)
        stage_names = matrix.stage_names or [f"stage_{i + 1}" for i in range(n)]
        header = ";".join(stage_names)
        rows = [
            ";".join(str(v if v is not None else 0.0) for v in row)
            for row in matrix.matrix_a
        ]
        csv_content = "\n".join([header] + rows)

        species = matrix.species_accepted or f"matrix_{matrix_id}"
        filename = species.replace(" ", "_").replace("/", "_") + ".csv"
        return csv_content, filename

    def import_matrices(
        self, files: list[tuple[str, bytes]], user_id: int
    ) -> BatchImportResult:
        created: list[MatrixRecord] = []
        errors: list[MatrixImportError] = []

        for filename, raw in files:
            try:
                data = json.loads(raw)
                imp = MatrixImport(**data)
            except (json.JSONDecodeError, ValidationError, TypeError) as exc:
                errors.append(MatrixImportError(filename=filename, reason=str(exc)))
                continue

            n = len(imp.matrix_a)
            zero = [[0.0] * n for _ in range(n)]
            dto = MatrixCreate(
                species_accepted=imp.species_accepted,
                common_name=imp.common_name,
                kingdom=imp.kingdom,
                country_code=imp.country_code,
                matrix_a=imp.matrix_a,
                matrix_u=imp.matrix_u if imp.matrix_u is not None else zero,
                matrix_f=imp.matrix_f if imp.matrix_f is not None else zero,
                stage_names=imp.stage_names,
                visibility="private",
            )
            try:
                record = self.create_matrix(dto, owner_id=user_id)
                created.append(record)
            except HTTPException as exc:
                errors.append(MatrixImportError(filename=filename, reason=exc.detail))

        return BatchImportResult(created=created, errors=errors)
