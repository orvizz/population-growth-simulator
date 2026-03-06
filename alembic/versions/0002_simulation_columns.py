"""add stochastic simulation columns to simulation_runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("simulation_runs", sa.Column("matrix_ids", JSONB(), nullable=True))
    op.add_column("simulation_runs", sa.Column("stochastic", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("simulation_runs", sa.Column("random_seed", sa.Integer(), nullable=True))
    op.add_column("simulation_runs", sa.Column("stage_names", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("simulation_runs", "stage_names")
    op.drop_column("simulation_runs", "random_seed")
    op.drop_column("simulation_runs", "stochastic")
    op.drop_column("simulation_runs", "matrix_ids")
