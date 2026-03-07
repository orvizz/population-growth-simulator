"""
MatrixRepository — pure data access for the population_matrices table.

No business logic, no HTTP concerns. Returns ORM objects only.
"""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.models import MatrixShare, PopulationMatrix


class MatrixRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, matrix_id: int) -> PopulationMatrix | None:
        return self._db.get(PopulationMatrix, matrix_id)

    def list(
        self,
        *,
        caller_id: int | None = None,
        species: str | None = None,
        kingdom: str | None = None,
        country_code: str | None = None,
        source_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PopulationMatrix]:
        q = self._db.query(PopulationMatrix)

        # Visibility filter
        if caller_id is None:
            q = q.filter(PopulationMatrix.visibility == "public")
        else:
            q = q.filter(
                or_(
                    PopulationMatrix.visibility == "public",
                    PopulationMatrix.owner_id == caller_id,
                    PopulationMatrix.shares.any(
                        MatrixShare.shared_with_user_id == caller_id
                    ),
                )
            )

        if species:
            q = q.filter(PopulationMatrix.species_accepted.ilike(f"%{species}%"))
        if kingdom:
            q = q.filter(PopulationMatrix.kingdom == kingdom)
        if country_code:
            q = q.filter(PopulationMatrix.country_code == country_code)
        if source_type:
            q = q.filter(PopulationMatrix.source_type == source_type)

        return q.offset(skip).limit(limit).all()

    def create(
        self,
        *,
        owner_id: int,
        species_accepted: str | None,
        common_name: str | None,
        kingdom: str | None,
        country_code: str | None,
        matrix_a: list,
        matrix_u: list | None,
        matrix_f: list | None,
        stage_names: list | None,
        visibility: str = "private",
    ) -> PopulationMatrix:
        matrix = PopulationMatrix(
            source_type="custom",
            owner_id=owner_id,
            species_accepted=species_accepted,
            common_name=common_name,
            kingdom=kingdom,
            country_code=country_code,
            matrix_a=matrix_a,
            matrix_u=matrix_u,
            matrix_f=matrix_f,
            stage_names=stage_names,
            visibility=visibility,
            metadata_=None,
        )
        self._db.add(matrix)
        self._db.commit()
        self._db.refresh(matrix)
        return matrix

    def update(self, matrix: PopulationMatrix, updates: dict) -> PopulationMatrix:
        for field, value in updates.items():
            setattr(matrix, field, value)
        self._db.commit()
        self._db.refresh(matrix)
        return matrix

    # ------------------------------------------------------------------
    # Share management
    # ------------------------------------------------------------------

    def get_share(self, matrix_id: int, shared_with_user_id: int) -> MatrixShare | None:
        return (
            self._db.query(MatrixShare)
            .filter_by(matrix_id=matrix_id, shared_with_user_id=shared_with_user_id)
            .first()
        )

    def add_share(self, matrix_id: int, shared_with_user_id: int) -> MatrixShare:
        share = MatrixShare(matrix_id=matrix_id, shared_with_user_id=shared_with_user_id)
        self._db.add(share)
        self._db.commit()
        self._db.refresh(share)
        return share

    def remove_share(self, matrix_id: int, shared_with_user_id: int) -> None:
        share = self.get_share(matrix_id, shared_with_user_id)
        if share:
            self._db.delete(share)
            self._db.commit()
