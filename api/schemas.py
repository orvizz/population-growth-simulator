"""
Input DTOs — Pydantic models that validate data arriving over HTTP.

These cross the API boundary (request bodies, query params).
They are the ONLY place where input validation lives.
Business rules (ownership, COMPADRE immutability) live in the service layer.
"""
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username must not contain spaces")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Matrices
# ---------------------------------------------------------------------------

Matrix2D = list[list[float | None]]


class MatrixCreate(BaseModel):
    species_accepted: str | None = Field(None, max_length=255)
    common_name: str | None = Field(None, max_length=255)
    kingdom: str | None = Field(None, max_length=128)
    country_code: str | None = Field(None, max_length=8)
    matrix_a: Matrix2D
    matrix_u: Matrix2D | None = None
    matrix_f: Matrix2D | None = None
    stage_names: list[str] | None = None
    visibility: Literal["private", "shared", "public"] = "private"

    @field_validator("matrix_a")
    @classmethod
    def matrix_a_must_be_square(cls, v: Matrix2D) -> Matrix2D:
        n = len(v)
        if n == 0:
            raise ValueError("matrix_a cannot be empty")
        for i, row in enumerate(v):
            if len(row) != n:
                raise ValueError(
                    f"matrix_a must be square: row {i} has {len(row)} elements, expected {n}"
                )
        return v

    @model_validator(mode="after")
    def sub_matrices_match_a(self) -> "MatrixCreate":
        """matrix_u and matrix_f, if provided, must have the same dimension as matrix_a."""
        n = len(self.matrix_a)
        for name, mat in [("matrix_u", self.matrix_u), ("matrix_f", self.matrix_f)]:
            if mat is None:
                continue
            if len(mat) != n or any(len(row) != n for row in mat):
                raise ValueError(
                    f"{name} must be {n}×{n} to match matrix_a"
                )
        return self

    @model_validator(mode="after")
    def stage_names_match_dimension(self) -> "MatrixCreate":
        if self.stage_names is not None:
            n = len(self.matrix_a)
            if len(self.stage_names) != n:
                raise ValueError(
                    f"stage_names has {len(self.stage_names)} entries but matrix_a is {n}×{n}"
                )
        return self


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------

class SimulationCreate(BaseModel):
    matrix_id: int | None = None          # deterministic: single matrix
    matrix_ids: list[int] | None = None   # stochastic: 2+ matrices
    initial_vector: list[float] = Field(min_length=1)
    n_steps: int = Field(ge=1, le=1000)
    random_seed: int | None = None
    name: str | None = Field(None, max_length=255)

    @model_validator(mode="after")
    def check_matrix_source(self) -> "SimulationCreate":
        has_single = self.matrix_id is not None
        has_multi = bool(self.matrix_ids)
        if not has_single and not has_multi:
            raise ValueError("Provide either matrix_id (deterministic) or matrix_ids (stochastic)")
        if has_single and has_multi:
            raise ValueError("Provide either matrix_id or matrix_ids, not both")
        if has_multi and len(self.matrix_ids) < 2:
            raise ValueError("Stochastic simulation requires at least 2 matrices in matrix_ids")
        return self

    @property
    def is_stochastic(self) -> bool:
        return self.matrix_ids is not None


class SimulationImport(BaseModel):
    """Schema for restoring a simulation from an exported JSON file."""
    format_version: str = "1"
    name: str | None = Field(None, max_length=255)
    stochastic: bool
    matrix_id: int | None = None
    matrix_ids: list[int] | None = None
    initial_vector: list[float] = Field(min_length=1)
    n_steps: int = Field(ge=1, le=10000)
    random_seed: int | None = None
    stage_names: list[str] | None = None
    result_history: list[list[float]] = Field(min_length=1)
    species_accepted: str | None = None


class MatrixUpdate(BaseModel):
    """All fields optional — PATCH semantics. Omitted fields are not changed."""
    species_accepted: str | None = Field(None, max_length=255)
    common_name: str | None = Field(None, max_length=255)
    kingdom: str | None = Field(None, max_length=128)
    country_code: str | None = Field(None, max_length=8)
    matrix_a: Matrix2D | None = None
    matrix_u: Matrix2D | None = None
    matrix_f: Matrix2D | None = None
    stage_names: list[str] | None = None
    visibility: Literal["private", "shared", "public"] | None = None

    @model_validator(mode="after")
    def square_matrices(self) -> "MatrixUpdate":
        """Any provided matrix must be square; sub-matrices must match matrix_a if both given."""
        def check_square(name: str, mat: Matrix2D) -> None:
            n = len(mat)
            if n == 0:
                raise ValueError(f"{name} cannot be empty")
            for i, row in enumerate(mat):
                if len(row) != n:
                    raise ValueError(f"{name} must be square: row {i} has {len(row)} elements")

        for name, mat in [
            ("matrix_a", self.matrix_a),
            ("matrix_u", self.matrix_u),
            ("matrix_f", self.matrix_f),
        ]:
            if mat is not None:
                check_square(name, mat)

        if self.matrix_a is not None:
            n = len(self.matrix_a)
            for name, mat in [("matrix_u", self.matrix_u), ("matrix_f", self.matrix_f)]:
                if mat is not None and (len(mat) != n or any(len(r) != n for r in mat)):
                    raise ValueError(f"{name} must be {n}×{n} to match matrix_a")

        return self


class MatrixShareCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
