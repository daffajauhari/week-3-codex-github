"""rename dimension to section, add barspec table

Revision ID: 9b52c9ab1906
Revises: 4ffedcd98c89
Create Date: 2026-09-15 19:56:24.280247

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b52c9ab1906'
down_revision: str | Sequence[str] | None = '4ffedcd98c89'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Section: renamed from Dimension. Postgres transparently repoints the
    # members FK and updates the check constraint's expression on column
    # rename, so no data loss and no TRUNCATE is required here (unlike
    # Floor/Zone in the previous migration, no new NOT NULL column without
    # a default is being introduced).
    op.rename_table('dimensions', 'sections')
    op.alter_column('sections', 'dimension_id', new_column_name='sect_id')
    op.alter_column('sections', 'member_type', new_column_name='obj_type')
    op.execute(
        sa.text(
            "ALTER TABLE sections "
            "RENAME CONSTRAINT ck_dimensions_member_type TO ck_sections_obj_type"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE sections "
            "RENAME CONSTRAINT uq_dimensions_id_type TO uq_sections_id_type"
        )
    )
    op.add_column(
        'sections',
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
    )

    # Material: rename to the short field names used across the rest of the
    # schema; renamed columns transparently carry the members FK along.
    op.alter_column('materials', 'material_id', new_column_name='mat_id')
    op.alter_column('materials', 'material_name', new_column_name='mat_name')
    op.alter_column('materials', 'material_type', new_column_name='mat_type')
    op.alter_column(
        'materials', 'compressive_strength_kg_cm2', new_column_name='mat_strength'
    )
    op.add_column(
        'materials',
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
    )

    op.create_table(
        'barspec',
        sa.Column('barspec_id', sa.String(), nullable=False),
        sa.Column('barspec_dia', sa.Integer(), nullable=False),
        sa.Column('barspec_type', sa.String(), nullable=False),
        sa.Column('barspec_grade', sa.String(), nullable=False),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.PrimaryKeyConstraint('barspec_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('barspec')

    op.drop_column('materials', 'created_at')
    op.alter_column(
        'materials', 'mat_strength', new_column_name='compressive_strength_kg_cm2'
    )
    op.alter_column('materials', 'mat_type', new_column_name='material_type')
    op.alter_column('materials', 'mat_name', new_column_name='material_name')
    op.alter_column('materials', 'mat_id', new_column_name='material_id')

    op.drop_column('sections', 'created_at')
    op.execute(
        sa.text(
            "ALTER TABLE sections "
            "RENAME CONSTRAINT uq_sections_id_type TO uq_dimensions_id_type"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE sections "
            "RENAME CONSTRAINT ck_sections_obj_type TO ck_dimensions_member_type"
        )
    )
    op.alter_column('sections', 'obj_type', new_column_name='member_type')
    op.alter_column('sections', 'sect_id', new_column_name='dimension_id')
    op.rename_table('sections', 'dimensions')
