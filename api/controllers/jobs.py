"""
Jobs controller — HTTP concerns only.

Parses requests, delegates to QuasiExtinctionService, returns records.
No business logic, no DB access.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, status

from api.deps import get_current_user, get_quasi_extinction_service
from api.records import JobRecord, JobSummaryRecord, UserRecord
from api.schemas import QuasiExtinctionCreate
from api.services.quasi_extinction_service import QuasiExtinctionService

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.post(
    "/quasi-extinction",
    response_model=JobRecord,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_quasi_extinction_job(
    body: QuasiExtinctionCreate,
    background_tasks: BackgroundTasks,
    current_user: UserRecord = Depends(get_current_user),
    service: QuasiExtinctionService = Depends(get_quasi_extinction_service),
):
    """Start an async quasi-extinction probability analysis.

    Returns immediately with status='pending'. Poll GET /v1/jobs/{id} for results.
    The background task runs N stochastic simulations and estimates the probability
    that total population falls below extinction_threshold within n_steps.
    """
    job = service.create_job(body, user_id=current_user.id)
    background_tasks.add_task(
        QuasiExtinctionService.run_quasi_extinction_background,
        job.id,
        None,  # db_factory — background function opens its own SessionLocal
    )
    return job


@router.get("", response_model=list[JobSummaryRecord])
def list_jobs(
    current_user: UserRecord = Depends(get_current_user),
    service: QuasiExtinctionService = Depends(get_quasi_extinction_service),
):
    """List all jobs for the current user, newest first."""
    return service.list_jobs(current_user.id)


@router.get("/{job_id}", response_model=JobRecord)
def get_job(
    job_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: QuasiExtinctionService = Depends(get_quasi_extinction_service),
):
    """Get a job by ID. Includes result when status='completed', error when status='failed'."""
    return service.get_job(job_id, user_id=current_user.id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: UserRecord = Depends(get_current_user),
    service: QuasiExtinctionService = Depends(get_quasi_extinction_service),
):
    """Delete a completed or failed job. Returns 409 if job is pending or running."""
    service.delete_job(job_id, user_id=current_user.id)
