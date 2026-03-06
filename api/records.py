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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


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
    """Full simulation record including the complete vector history."""
    initial_vector: list
    result_history: list


class MatrixSummaryRecord(BaseModel):
    """Lightweight projection — no matrix data — used in list responses."""
    id: int
    source_type: str
    owner_id: int | None
    species_accepted: str | None
    common_name: str | None
    kingdom: str | None
    country_code: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
