"""
Domain records — Pydantic models that represent business entities.

These are the objects that flow between the service and controller layers.
They are constructed from ORM objects (from_attributes=True) and used
directly as FastAPI response_model targets.

Records are NEVER used for input validation — that is the responsibility
of the schemas (DTOs) in api/schemas.py.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRecord(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatrixShareRecord(BaseModel):
    """A user a matrix has been shared with."""
    shared_with_user_id: int
    shared_with_username: str


class MatrixRecord(BaseModel):
    """Full matrix including sub-matrices — used in single-resource responses."""
    id: int
    source_type: str
    owner_id: int | None
    species_accepted: str | None
    common_name: str | None
    kingdom: str | None
    country_code: str | None
    matrix_a: list | None
    matrix_u: list | None
    matrix_f: list | None
    stage_names: list | None
    # ORM stores this as metadata_ to avoid clashing with SQLAlchemy internals;
    # we expose it as "metadata" in all API responses.
    metadata: dict | None = Field(None, validation_alias="metadata_")
    visibility: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DeterministicAnalyticsRecord(BaseModel):
    """Analytics computed from a deterministic (single-matrix) simulation.

    All metrics are derived from eigenvalue analysis of the Leslie/Lefkovitch matrix A.
    """
    lambda_1: float
    """Dominant real eigenvalue of A — the long-run deterministic growth rate.
    λ₁ > 1 → growing, λ₁ < 1 → declining, λ₁ = 1 → stable."""
    stable_stage_distribution: list[float]
    """Right eigenvector of λ₁, normalised so Σwᵢ = 1.
    Proportional stage composition at demographic equilibrium."""
    reproductive_value: list[float]
    """Left eigenvector of λ₁, normalised so v[0] = 1.
    Relative contribution of each stage to future population growth."""
    sensitivities: list[list[float]]
    """sᵢⱼ = (vᵢ · wⱼ) / (vᵀ · w). Absolute change in λ₁ per unit change in aᵢⱼ."""
    elasticities: list[list[float]]
    """eᵢⱼ = (aᵢⱼ / λ₁) · sᵢⱼ. Proportional sensitivity; Σeᵢⱼ = 1."""
    analytics_reliable: bool
    """False when λ₁ ≈ 0 (degenerate/zero matrix); True otherwise."""
    stage_names: list[str] | None = None


class StochasticAnalyticsRecord(BaseModel):
    """Analytics computed from a stochastic (multi-matrix) simulation.

    Metrics are derived from the simulated trajectory and frequency-weighted mean matrix.
    """
    lambda_s: float
    """Stochastic long-run growth rate.
    Estimated as exp((1/T) · Σₜ log(‖v(t+1)‖ / ‖v(t)‖))."""
    mean_matrix: list[list[float]]
    """Frequency-weighted mean matrix: Ā = Σₖ (nₖ/T) · Aₖ, where nₖ = times matrix k was chosen."""
    lambda_1_of_mean: float
    """Dominant eigenvalue of Ā — deterministic approximation of λ_s."""
    elasticities_of_mean: list[list[float]]
    """Elasticities of Ā — proportional importance of each transition in the mean environment."""
    stable_stage_distribution_of_mean: list[float]
    """Right eigenvector of Ā, normalised to sum 1 — equilibrium under mean environment."""
    analytics_reliable: bool
    """False when n_steps < 20 or all population norms are zero; True otherwise."""
    stage_names: list[str] | None = None


# Union type for use in records that can hold either analytics variant
AnalyticsRecord = DeterministicAnalyticsRecord | StochasticAnalyticsRecord


class SimulationRunResult(BaseModel):
    """Returned by POST /v1/simulations/run — ephemeral, never stored in DB."""
    stochastic: bool
    matrix_id: int | None
    matrix_ids: list | None
    random_seed: int | None
    initial_vector: list
    n_steps: int
    result_history: list
    stage_names: list | None
    species_accepted: str | None
    matrices_snapshot: list | None = None
    analytics: AnalyticsRecord | None = None


class SimulationSummaryRecord(BaseModel):
    """Lightweight projection — no result_history — used in list responses."""
    id: int
    user_id: int | None
    name: str | None
    matrix_id: int | None
    matrix_ids: list | None
    stochastic: bool
    n_steps: int
    random_seed: int | None
    stage_names: list | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationRecord(SimulationSummaryRecord):
    """Full simulation record including the complete vector history and analytics."""
    initial_vector: list
    result_history: list
    matrices_snapshot: list | None = None
    matrix_sequence: list | None = None
    analytics: AnalyticsRecord | None = None


class MatrixSummaryRecord(BaseModel):
    """Lightweight projection — no matrix data — used in list responses."""
    id: int
    source_type: str
    owner_id: int | None
    species_accepted: str | None
    common_name: str | None
    kingdom: str | None
    country_code: str | None
    visibility: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobSummaryRecord(BaseModel):
    """Lightweight job projection for list responses."""
    id: int
    user_id: int | None
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRecord(JobSummaryRecord):
    """Full job record including params and result."""
    params: dict
    matrices_snapshot: list | None = None
    result: dict | None = None
    error: str | None = None
