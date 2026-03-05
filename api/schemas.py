from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Matrices
# ---------------------------------------------------------------------------

Matrix2D = list[list[float | None]]


class MatrixCreate(BaseModel):
    species_accepted: str | None = None
    common_name: str | None = None
    kingdom: str | None = None
    country_code: str | None = Field(None, max_length=8)
    matrix_a: Matrix2D
    matrix_u: Matrix2D | None = None
    matrix_f: Matrix2D | None = None
    stage_names: list[str] | None = None


class MatrixUpdate(BaseModel):
    """All fields optional — PATCH semantics."""
    species_accepted: str | None = None
    common_name: str | None = None
    kingdom: str | None = None
    country_code: str | None = Field(None, max_length=8)
    matrix_a: Matrix2D | None = None
    matrix_u: Matrix2D | None = None
    matrix_f: Matrix2D | None = None
    stage_names: list[str] | None = None


class MatrixResponse(BaseModel):
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
    # ORM attribute is metadata_ (avoids conflict with SQLAlchemy's own metadata)
    # We expose it as "metadata" in the JSON response
    metadata: dict | None = Field(None, validation_alias="metadata_")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MatrixSummary(BaseModel):
    """Lightweight projection used in list responses (no matrix data)."""
    id: int
    source_type: str
    owner_id: int | None
    species_accepted: str | None
    common_name: str | None
    kingdom: str | None
    country_code: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
