"""add stochastic multi-run stats columns to simulation_runs

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("simulation_runs", sa.Column("n_runs", sa.Integer, nullable=True))
    op.add_column("simulation_runs", sa.Column("result_variance", JSONB, nullable=True))
    op.add_column("simulation_runs", sa.Column("result_min_history", JSONB, nullable=True))
    op.add_column("simulation_runs", sa.Column("result_max_history", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("simulation_runs", "result_max_history")
    op.drop_column("simulation_runs", "result_min_history")
    op.drop_column("simulation_runs", "result_variance")
    op.drop_column("simulation_runs", "n_runs")
