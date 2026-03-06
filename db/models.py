from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User | None"] = relationship(back_populates="matrices")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="matrix")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="simulation_runs")
    matrix: Mapped["PopulationMatrix | None"] = relationship(back_populates="simulation_runs")
