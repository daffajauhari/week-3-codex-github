"""rename storey to floor, add building id to floor and zone, add grid table

Revision ID: 4ffedcd98c89
Revises: 52ffe1088b42
Create Date: 2026-09-15 19:52:01.399886

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4ffedcd98c89'
down_revision: str | Sequence[str] | None = '52ffe1088b42'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    # Floor: renamed from Storey. Postgres transparently repoints the
    # members FK to the renamed table/column, no constraint changes needed.
    op.rename_table('storeys', 'floors')
    op.alter_column('floors', 'storey_id', new_column_name='floor_id')
    op.alter_column('floors', 'storey_name', new_column_name='floor_name')
    op.alter_column('floors', 'elevation_mm', new_column_name='elevation')

    # Existing Floor/Zone rows (and dependent Member rows) are wiped, not
    # migrated, so the new NOT NULL building_id columns can be added below
    # without a backfill.
    op.execute(
        sa.text("TRUNCATE TABLE members, floors, zones RESTART IDENTITY CASCADE")
    )

    op.add_column('floors', sa.Column('building_id', sa.String(), nullable=False))
    op.create_foreign_key(
        'fk_floors_building_id',
        'floors',
        'buildings',
        ['building_id'],
        ['building_id'],
    )
    op.add_column(
        'floors',
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
    )

    # Zone: add building_id, rename pour_sequence -> pour_seq, drop zone_name
    op.add_column('zones', sa.Column('building_id', sa.String(), nullable=False))
    op.create_foreign_key(
        'fk_zones_building_id',
        'zones',
        'buildings',
        ['building_id'],
        ['building_id'],
    )
    op.alter_column('zones', 'pour_sequence', new_column_name='pour_seq')
    op.drop_column('zones', 'zone_name')
    op.add_column(
        'zones',
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
    )

    # Grid: structurally new shape (single surrogate key instead of composite
    # axis+label key, building-scoped, JSONB coordinate) - replace outright.
    op.drop_table('grids')
    op.create_table(
        'grid',
        sa.Column('grid_id', sa.String(), nullable=False),
        sa.Column('building_id', sa.String(), nullable=False),
        sa.Column('grid_label', sa.String(), nullable=False),
        sa.Column('grid_axis', sa.String(), nullable=False),
        sa.Column(
            'grid_coord', postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            'created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False
        ),
        sa.ForeignKeyConstraint(['building_id'], ['buildings.building_id']),
        sa.PrimaryKeyConstraint('grid_id'),
        sa.UniqueConstraint(
            'building_id', 'grid_label', 'grid_axis', name='uq_grid_building_label_axis'
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table('grid')
    op.create_table(
        'grids',
        sa.Column('grid_axis', sa.String(), nullable=False),
        sa.Column('grid_label', sa.String(), nullable=False),
        sa.Column('coordinate_mm', sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "grid_axis IN ('x', 'y')", name='ck_grids_axis'
        ),
        sa.PrimaryKeyConstraint('grid_axis', 'grid_label'),
    )

    op.drop_column('zones', 'created_at')
    op.add_column(
        'zones', sa.Column('zone_name', sa.String(), nullable=False, server_default='')
    )
    op.alter_column('zones', 'zone_name', server_default=None)
    op.alter_column('zones', 'pour_seq', new_column_name='pour_sequence')
    op.drop_constraint('fk_zones_building_id', 'zones', type_='foreignkey')
    op.drop_column('zones', 'building_id')

    op.drop_column('floors', 'created_at')
    op.drop_constraint('fk_floors_building_id', 'floors', type_='foreignkey')
    op.drop_column('floors', 'building_id')
    op.alter_column('floors', 'elevation', new_column_name='elevation_mm')
    op.alter_column('floors', 'floor_name', new_column_name='storey_name')
    op.alter_column('floors', 'floor_id', new_column_name='storey_id')
    op.rename_table('floors', 'storeys')
