"""add label and weight fields and uniqueness constraints

Revision ID: 086649eb0ad9
Revises: a4bfa1497f9e
Create Date: 2026-09-16 15:10:06.393751

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '086649eb0ad9'
down_revision: str | Sequence[str] | None = 'a4bfa1497f9e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # sections/materials/barspec/zones are gaining new NOT NULL columns
    # with no sensible default to backfill - existing rows (and anything
    # downstream referencing them) are wiped and reseeded instead, same
    # as the Floor/Zone truncate in the earlier building_id migration.
    op.execute(
        sa.text(
            "TRUNCATE TABLE objects, reinforcements, sections, materials, "
            "barspec, zones RESTART IDENTITY CASCADE"
        )
    )

    op.add_column('sections', sa.Column('sect_label', sa.String(), nullable=False))
    op.create_unique_constraint('uq_sections_label', 'sections', ['sect_label'])

    op.add_column('materials', sa.Column('mat_weight', sa.Integer(), nullable=False))
    op.alter_column('materials', 'mat_name', existing_type=sa.String(), nullable=False)
    op.create_unique_constraint('uq_materials_name', 'materials', ['mat_name'])

    op.add_column('barspec', sa.Column('barspec_label', sa.String(), nullable=False))
    op.add_column('barspec', sa.Column('barspec_weight', sa.Integer(), nullable=False))
    op.create_unique_constraint('uq_barspec_label', 'barspec', ['barspec_label'])

    op.add_column('zones', sa.Column('zone_label', sa.String(), nullable=False))
    op.create_unique_constraint(
        'uq_zones_building_label', 'zones', ['building_id', 'zone_label']
    )

    op.create_unique_constraint(
        'uq_floors_building_name', 'floors', ['building_id', 'floor_name']
    )
    op.create_unique_constraint('uq_projects_name', 'projects', ['project_name'])
    op.create_unique_constraint('uq_buildings_name', 'buildings', ['building_name'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_buildings_name', 'buildings', type_='unique')
    op.drop_constraint('uq_projects_name', 'projects', type_='unique')
    op.drop_constraint('uq_floors_building_name', 'floors', type_='unique')

    op.drop_constraint('uq_zones_building_label', 'zones', type_='unique')
    op.drop_column('zones', 'zone_label')

    op.drop_constraint('uq_barspec_label', 'barspec', type_='unique')
    op.drop_column('barspec', 'barspec_weight')
    op.drop_column('barspec', 'barspec_label')

    op.drop_constraint('uq_materials_name', 'materials', type_='unique')
    op.alter_column('materials', 'mat_name', existing_type=sa.String(), nullable=True)
    op.drop_column('materials', 'mat_weight')

    op.drop_constraint('uq_sections_label', 'sections', type_='unique')
    op.drop_column('sections', 'sect_label')
