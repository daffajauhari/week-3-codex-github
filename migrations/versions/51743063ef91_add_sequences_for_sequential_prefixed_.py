"""add sequences for sequential prefixed ids

Revision ID: 51743063ef91
Revises: 65461096482c
Create Date: 2026-09-16 15:03:02.712493

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from ids import ALL_ID_SPECS

# revision identifiers, used by Alembic.
revision: str = '51743063ef91'
down_revision: str | Sequence[str] | None = '65461096482c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    for _, sequence_name, _ in ALL_ID_SPECS:
        op.execute(sa.text(f"CREATE SEQUENCE {sequence_name} START WITH 1"))


def downgrade() -> None:
    """Downgrade schema."""
    for _, sequence_name, _ in reversed(ALL_ID_SPECS):
        op.execute(sa.text(f"DROP SEQUENCE {sequence_name}"))
