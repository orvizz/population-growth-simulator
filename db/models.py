from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    matrices: Mapped[list["PopulationMatrix"]] = relationship(back_populates="owner")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="user")
    simulation_jobs: Mapped[list["SimulationJob"]] = relationship(back_populates="user")


class PopulationMatrix(Base):
    __tablename__ = "population_matrices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    species_accepted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    common_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kingdom: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    matrix_a: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    matrix_u: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    matrix_f: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    stage_names: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    # "private" | "shared" | "public". COMPADRE matrices are seeded as "public".
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, server_default="private")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User | None"] = relationship(back_populates="matrices")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="matrix")
    shares: Mapped[list["MatrixShare"]] = relationship(
        back_populates="matrix", cascade="all, delete-orphan"
    )


class MatrixShare(Base):
    """Records that a custom matrix has been shared with a specific user."""
    __tablename__ = "matrix_shares"
    __table_args__ = (UniqueConstraint("matrix_id", "shared_with_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matrix_id: Mapped[int] = mapped_column(
        ForeignKey("population_matrices.id", ondelete="CASCADE"), nullable=False
    )
    shared_with_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    matrix: Mapped["PopulationMatrix"] = relationship(back_populates="shares")
    shared_with_user: Mapped["User"] = relationship()


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # deterministic: single FK; stochastic: null (ids stored in matrix_ids)
    matrix_id: Mapped[int | None] = mapped_column(ForeignKey("population_matrices.id"), nullable=True)
    matrix_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    stochastic: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    initial_vector: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    n_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_history: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    stage_names: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Snapshot of matrix_a arrays (list of 2D arrays; always a list, even for deterministic)
    matrices_snapshot: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Stochastic only: index of the matrix chosen at each step; null for deterministic
    matrix_sequence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Computed analytics dict; filled at run time by AnalyticsService
    analytics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="simulation_runs")
    matrix: Mapped["PopulationMatrix | None"] = relationship(back_populates="simulation_runs")


class SimulationJob(Base):
    """Background / async job record for long-running simulation tasks (e.g. quasi-extinction)."""
    __tablename__ = "simulation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # e.g. "quasi_extinction"
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    # Full input snapshot captured at job creation
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Matrix snapshots captured at job creation
    matrices_snapshot: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Filled on successful completion
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Filled on failure
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user: Mapped["User | None"] = relationship(back_populates="simulation_jobs")
