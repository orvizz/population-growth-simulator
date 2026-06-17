"""
SimulationRepository — pure data access for the simulation_runs table.

No business logic, no HTTP concerns. Returns ORM objects only.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import SimulationRun


class SimulationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, sim_id: int) -> SimulationRun | None:
        return self._db.get(SimulationRun, sim_id)

    def list_by_user(self, user_id: int) -> list[SimulationRun]:
        return (
            self._db.query(SimulationRun)
            .filter(SimulationRun.user_id == user_id)
            .order_by(SimulationRun.created_at.desc())
            .all()
        )

    def create(
        self,
        *,
        user_id: int,
        name: str | None,
        matrix_id: int | None,
        matrix_ids: list[int] | None,
        stochastic: bool,
        random_seed: int | None,
        initial_vector: list[float],
        n_steps: int,
        result_history: list[list[float]],
        stage_names: list[str] | None,
        matrices_snapshot: list | None = None,
        matrix_sequence: list | None = None,
        analytics: dict | None = None,
        n_runs: int | None = None,
        result_variance: list | None = None,
        result_min_history: list | None = None,
        result_max_history: list | None = None,
    ) -> SimulationRun:
        run = SimulationRun(
            user_id=user_id,
            name=name,
            matrix_id=matrix_id,
            matrix_ids=matrix_ids,
            stochastic=stochastic,
            random_seed=random_seed,
            initial_vector=initial_vector,
            n_steps=n_steps,
            result_history=result_history,
            stage_names=stage_names,
            matrices_snapshot=matrices_snapshot,
            matrix_sequence=matrix_sequence,
            analytics=analytics,
            n_runs=n_runs,
            result_variance=result_variance,
            result_min_history=result_min_history,
            result_max_history=result_max_history,
        )
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)
        return run

    def delete(self, run: SimulationRun) -> None:
        self._db.delete(run)
        self._db.commit()
