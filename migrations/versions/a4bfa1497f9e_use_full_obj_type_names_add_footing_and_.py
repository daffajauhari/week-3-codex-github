"""use full obj_type names, add footing and stair

Revision ID: a4bfa1497f9e
Revises: 51743063ef91
Create Date: 2026-09-16 15:20:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a4bfa1497f9e'
down_revision: str | Sequence[str] | None = '51743063ef91'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the FK before renaming section's own obj_type values, so the
    # composite (sect_id, obj_type) target doesn't momentarily disagree
    # with any existing objects row referencing it.
    op.drop_constraint('fk_objects_sect_id_obj_type', 'objects', type_='foreignkey')
    op.drop_constraint('ck_sections_obj_type', 'sections', type_='check')

    op.execute(sa.text("UPDATE sections SET obj_type = 'column' WHERE obj_type = 'col'"))
    op.execute(sa.text("UPDATE objects SET obj_type = 'column' WHERE obj_type = 'col'"))

    op.create_check_constraint(
        'ck_sections_obj_type',
        'sections',
        "obj_type IN ('column', 'beam', 'wall', 'slab', 'footing', 'stair')",
    )
    op.create_foreign_key(
        'fk_objects_sect_id_obj_type',
        'objects',
        'sections',
        ['sect_id', 'obj_type'],
        ['sect_id', 'obj_type'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_objects_sect_id_obj_type', 'objects', type_='foreignkey')
    op.drop_constraint('ck_sections_obj_type', 'sections', type_='check')

    op.execute(sa.text("UPDATE sections SET obj_type = 'col' WHERE obj_type = 'column'"))
    op.execute(sa.text("UPDATE objects SET obj_type = 'col' WHERE obj_type = 'column'"))

    op.create_check_constraint(
        'ck_sections_obj_type',
        'sections',
        "obj_type IN ('col', 'beam', 'wall', 'slab')",
    )
    op.create_foreign_key(
        'fk_objects_sect_id_obj_type',
        'objects',
        'sections',
        ['sect_id', 'obj_type'],
        ['sect_id', 'obj_type'],
    )
