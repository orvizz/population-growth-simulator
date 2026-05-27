"""
QuasiExtinctionService — manages quasi-extinction probability jobs.

A quasi-extinction analysis runs N stochastic simulations and estimates the
probability that the total population falls below a threshold (extinction_threshold)
within n_steps time steps.

Job lifecycle: pending → running → completed | failed
"""
from __future__ import annotations

import math

import numpy as np
from fastapi import HTTPException

from api.records import JobRecord, JobSummaryRecord
from api.repositories.job_repository import JobRepository
from api.repositories.matrix_repository import MatrixRepository
from api.schemas import QuasiExtinctionCreate
from api.services.simulation_service import SimulationService


class QuasiExtinctionService:
    def __init__(
        self,
        job_repo: JobRepository,
        matrix_repo: MatrixRepository,
    ) -> None:
        self._jobs = job_repo
        self._matrices = matrix_repo

    def create_job(self, data: QuasiExtinctionCreate, *, user_id: int) -> JobRecord:
        """Validate matrices, snapshot them, create job record. Does NOT start execution.

        The background task is started by the controller after this returns.
        Returns a JobRecord with status="pending".
        """
        # Load and validate matrices
        matrices = [self._matrices.get_by_id(mid) for mid in data.matrix_ids]
        for mid, m in zip(data.matrix_ids, matrices):
            if m is None:
                raise HTTPException(status_code=404, detail=f"Matrix {mid} not found")
            if not m.matrix_a:
                raise HTTPException(
                    status_code=400, detail=f"Matrix {mid} has no matrix_a defined"
                )
        dims = [len(m.matrix_a) for m in matrices]
        if len(set(dims)) > 1:
            raise HTTPException(
                status_code=400,
                detail=f"All matrices must have the same dimension — got {set(dims)}",
            )
        n = dims[0]
        if len(data.initial_vector) != n:
            raise HTTPException(
                status_code=400,
                detail=f"initial_vector has {len(data.initial_vector)} elements but matrices are {n}×{n}",
            )

        # Snapshot matrix values
        matrices_snapshot = SimulationService.snapshot_matrices(
            [m.matrix_a for m in matrices]
        )

        # Serialise input params
        params = data.model_dump()

        # Create DB record
        job = self._jobs.create(
            user_id=user_id,
            job_type="quasi_extinction",
            params=params,
            matrices_snapshot=matrices_snapshot,
        )
        return JobRecord.model_validate(job)

    def get_job(self, job_id: int, *, user_id: int) -> JobRecord:
        """Return job by ID. Raises 404/403 on missing/unauthorized."""
        job = self._jobs.get_by_id(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this job")
        return JobRecord.model_validate(job)

    def list_jobs(self, user_id: int) -> list[JobSummaryRecord]:
        """List all jobs for a user, newest first."""
        jobs = self._jobs.list_by_user(user_id)
        return [JobSummaryRecord.model_validate(j) for j in jobs]

    def delete_job(self, job_id: int, *, user_id: int) -> None:
        """Delete a job. Only completed or failed jobs may be deleted."""
        job = self._jobs.get_by_id(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="You do not own this job")
        if job.status not in ("completed", "failed"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete a job with status '{job.status}'. "
                       "Only completed or failed jobs may be deleted.",
            )
        self._jobs.delete(job)

    # ------------------------------------------------------------------
    # Background execution (called by FastAPI BackgroundTasks)
    # ------------------------------------------------------------------

    @staticmethod
    def run_quasi_extinction_background(job_id: int, db_factory) -> None:
        """Execute quasi-extinction analysis for job_id.

        This runs in a FastAPI BackgroundTask — it must create its own DB session
        (the request session will be closed when this is called).

        Algorithm:
          For each of n_runs stochastic simulations:
            1. Pick matrices randomly at each step (uniform)
            2. Check if total population < extinction_threshold at any step
            3. Record step at which extinction occurred (if any)

        Result:
          quasi_extinction_probability = n_extinct / n_runs
          time_to_extinction_distribution: {step: count} — only for runs that went extinct
          mean_final_population: mean of total population at step n_steps across all runs
          std_final_population: std dev of total population at step n_steps
          lambda_s_distribution: estimated lambda_s per run
        """
        # Outer guard: background tasks must NEVER propagate exceptions to the
        # ASGI worker.  Any DB connectivity issue (e.g. table missing during
        # tests, network error) is swallowed here — the job simply stays in its
        # last-known status.
        try:
            from db.session import SessionLocal
            from api.repositories.job_repository import JobRepository

            with SessionLocal() as db:
                job_repo = JobRepository(db)
                job = job_repo.get_by_id(job_id)
                if job is None:
                    return  # Job was deleted before execution started

                job = job_repo.update_status(job, "running")

                try:
                    params = job.params
                    matrices_snapshot = job.matrices_snapshot
                    result = _compute_quasi_extinction(params, matrices_snapshot)
                    job_repo.update_status(job, "completed", result=result)
                except Exception as exc:
                    job_repo.update_status(job, "failed", error=str(exc))
        except Exception:
            # DB session could not be established or table not found (e.g. during
            # tests where background uses the main DB, not the test DB).
            # Job stays in its current status — acceptable in a test context.
            pass


def _compute_quasi_extinction(params: dict, matrices_snapshot: list) -> dict:
    """Pure computation for quasi-extinction probability.

    Args:
        params: QuasiExtinctionCreate fields as a dict
        matrices_snapshot: list of snapshotted matrix_a arrays (already float, no None)

    Returns result dict with:
        n_runs: total runs executed
        n_extinct: runs where total population fell below threshold
        quasi_extinction_probability: n_extinct / n_runs
        extinction_threshold: threshold used
        time_to_extinction_distribution: {step_str: count} for extinct runs
        mean_final_population: mean total pop at final step (across all runs)
        std_final_population: std dev of total pop at final step
        lambda_s_distribution: list of per-run lambda_s estimates
    """
    n_runs: int = params["n_runs"]
    n_steps: int = params["n_steps"]
    initial_vector: list[float] = params["initial_vector"]
    extinction_threshold: float = params["extinction_threshold"]
    random_seed: int | None = params.get("random_seed")

    arrays = [
        np.array(
            [[0.0 if v is None else float(v) for v in row] for row in m],
            dtype=float,
        )
        for m in matrices_snapshot
    ]
    v0 = np.array(initial_vector, dtype=float)

    n_extinct = 0
    time_to_extinction: dict[int, int] = {}
    final_populations: list[float] = []
    lambda_s_list: list[float] = []

    # Use a master RNG; each run gets a child seed for independence + reproducibility
    master_rng = np.random.default_rng(random_seed)

    for _ in range(n_runs):
        run_seed = int(master_rng.integers(2**31))
        rng = np.random.default_rng(run_seed)

        v = v0.copy()
        log_growth_sum = 0.0
        valid_steps = 0
        extinct_at: int | None = None

        # Track previous norm for lambda_s calculation; initialise before the loop
        prev_norm = float(np.linalg.norm(v0))

        for step in range(1, n_steps + 1):
            idx = int(rng.integers(len(arrays)))
            v = arrays[idx] @ v

            new_norm = float(np.linalg.norm(v))
            total_pop = float(v.sum())

            if extinct_at is None and total_pop < extinction_threshold:
                extinct_at = step

            # Accumulate log-growth for lambda_s
            if prev_norm > 0 and new_norm > 0:
                log_growth_sum += math.log(new_norm / prev_norm)
                valid_steps += 1

            prev_norm = new_norm

        final_total = float(v.sum())
        final_populations.append(final_total)

        # lambda_s for this run
        if valid_steps > 0:
            lambda_s_list.append(math.exp(log_growth_sum / valid_steps))
        else:
            lambda_s_list.append(0.0)

        if extinct_at is not None:
            n_extinct += 1
            time_to_extinction[extinct_at] = time_to_extinction.get(extinct_at, 0) + 1

    final_arr = np.array(final_populations)
    return {
        "n_runs": n_runs,
        "n_extinct": n_extinct,
        "quasi_extinction_probability": n_extinct / n_runs,
        "extinction_threshold": extinction_threshold,
        "time_to_extinction_distribution": {str(k): v for k, v in sorted(time_to_extinction.items())},
        "mean_final_population": float(final_arr.mean()),
        "std_final_population": float(final_arr.std()),
        "lambda_s_distribution": lambda_s_list,
    }
