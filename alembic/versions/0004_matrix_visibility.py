"""add matrix visibility and shares table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add visibility column (default "private" for new rows)
    op.add_column(
        "population_matrices",
        sa.Column("visibility", sa.String(16), nullable=False, server_default="private"),
    )

    # 2. Data migration: compadre matrices are always public
    op.execute(
        "UPDATE population_matrices SET visibility = 'public' WHERE source_type = 'compadre'"
    )

    # 3. Create matrix_shares join table
    op.create_table(
        "matrix_shares",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "matrix_id",
            sa.Integer,
            sa.ForeignKey("population_matrices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "shared_with_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("matrix_id", "shared_with_user_id"),
    )


def downgrade() -> None:
    op.drop_table("matrix_shares")
    op.drop_column("population_matrices", "visibility")
