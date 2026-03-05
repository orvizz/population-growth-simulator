"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "population_matrices",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("species_accepted", sa.String(255), nullable=True),
        sa.Column("common_name", sa.String(255), nullable=True),
        sa.Column("kingdom", sa.String(128), nullable=True),
        sa.Column("country_code", sa.String(8), nullable=True),
        sa.Column("matrix_a", JSONB(), nullable=True),
        sa.Column("matrix_u", JSONB(), nullable=True),
        sa.Column("matrix_f", JSONB(), nullable=True),
        sa.Column("stage_names", JSONB(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_population_matrices_species_accepted",
        "population_matrices",
        ["species_accepted"],
    )

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("matrix_id", sa.Integer(), sa.ForeignKey("population_matrices.id"), nullable=True),
        sa.Column("initial_vector", JSONB(), nullable=True),
        sa.Column("n_steps", sa.Integer(), nullable=True),
        sa.Column("result_history", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("simulation_runs")
    op.drop_index("ix_population_matrices_species_accepted", table_name="population_matrices")
    op.drop_table("population_matrices")
    op.drop_table("users")
