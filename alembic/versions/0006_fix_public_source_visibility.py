"""Ensure all compadre/comadre matrices have visibility='public'

Migration 0004 added the visibility column with server_default='private', which
silently set existing compadre/comadre rows to 'private'. The data fix in 0004
only covered source_type='compadre', leaving comadre rows and any rows seeded
from an older code version with visibility='private'.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-04
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE population_matrices "
        "SET visibility = 'public' "
        "WHERE source_type IN ('compadre', 'comadre') "
        "AND visibility != 'public'"
    )


def downgrade() -> None:
    pass
