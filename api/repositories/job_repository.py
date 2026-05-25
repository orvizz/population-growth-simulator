"""
JobRepository — pure data access for the simulation_jobs table.

No business logic, no HTTP concerns. Returns ORM objects only.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from db.models import SimulationJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        user_id: int,
        job_type: str,
        params: dict,
        matrices_snapshot: list | None = None,
    ) -> SimulationJob:
        job = SimulationJob(
            user_id=user_id,
            job_type=job_type,
            status="pending",
            params=params,
            matrices_snapshot=matrices_snapshot,
        )
        self._db.add(job)
        self._db.commit()
        self._db.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> SimulationJob | None:
        return self._db.get(SimulationJob, job_id)

    def list_by_user(self, user_id: int) -> list[SimulationJob]:
        return (
            self._db.query(SimulationJob)
            .filter(SimulationJob.user_id == user_id)
            .order_by(SimulationJob.created_at.desc())
            .all()
        )

    def update_status(
        self,
        job: SimulationJob,
        status: str,
        *,
        result: dict | None = None,
        error: str | None = None,
    ) -> SimulationJob:
        """Update job status and optionally set result or error. Also bumps updated_at."""
        job.status = status
        job.updated_at = datetime.utcnow()
        if result is not None:
            job.result = result
        if error is not None:
            job.error = error
        self._db.commit()
        self._db.refresh(job)
        return job

    def delete(self, job: SimulationJob) -> None:
        self._db.delete(job)
        self._db.commit()
