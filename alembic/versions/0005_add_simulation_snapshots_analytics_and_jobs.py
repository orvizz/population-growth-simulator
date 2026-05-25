"""add simulation snapshot/analytics columns and simulation_jobs table

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-25
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to simulation_runs
    op.add_column(
        "simulation_runs",
        sa.Column("matrices_snapshot", JSONB, nullable=True),
    )
    op.add_column(
        "simulation_runs",
        sa.Column("matrix_sequence", JSONB, nullable=True),
    )
    op.add_column(
        "simulation_runs",
        sa.Column("analytics", JSONB, nullable=True),
    )

    # Create simulation_jobs table
    op.create_table(
        "simulation_jobs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("params", JSONB, nullable=False),
        sa.Column("matrices_snapshot", JSONB, nullable=True),
        sa.Column("result", JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("simulation_jobs")
    op.drop_column("simulation_runs", "analytics")
    op.drop_column("simulation_runs", "matrix_sequence")
    op.drop_column("simulation_runs", "matrices_snapshot")
