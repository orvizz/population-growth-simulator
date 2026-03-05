"""
MatrixRepository — pure data access for the population_matrices table.

No business logic, no HTTP concerns. Returns ORM objects only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import PopulationMatrix


class MatrixRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, matrix_id: int) -> PopulationMatrix | None:
        return self._db.get(PopulationMatrix, matrix_id)

    def list(
        self,
        *,
        species: str | None = None,
        kingdom: str | None = None,
        country_code: str | None = None,
        source_type: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[PopulationMatrix]:
        q = self._db.query(PopulationMatrix)
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
