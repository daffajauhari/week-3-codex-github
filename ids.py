from sqlalchemy import text
from sqlalchemy.orm import Session

# (prefix, sequence name, zero-pad width). stable_id is NOT here - it
# stays a uuid4() value (D6); this scheme covers every other
# system-generated primary key.
PROJECT_ID = ("PRJ-", "seq_projects", 3)
BUILDING_ID = ("BLD-", "seq_buildings", 3)
FLOOR_ID = ("FL-", "seq_floors", 3)
GRID_ID = ("G-", "seq_grid", 3)
ZONE_ID = ("ZN-", "seq_zones", 3)
MATERIAL_ID = ("MAT-", "seq_materials", 3)
SECTION_ID = ("SECT-", "seq_sections", 3)
BARSPEC_ID = ("BAR-", "seq_barspec", 3)
OBJECT_ID = ("OBJ-", "seq_objects", 3)
REVISION_ID = ("REV-", "seq_revisions", 3)
REINFORCEMENT_ID = ("RBAR-", "seq_reinforcements", 4)
QUANTITY_ID = ("QTY-", "seq_quantity", 3)

# Single source of truth for "every sequence this scheme needs" - used by
# the migration that creates them and by the test fixture that stands up
# a schema via Base.metadata.create_all() instead of running migrations.
ALL_ID_SPECS = (
    PROJECT_ID,
    BUILDING_ID,
    FLOOR_ID,
    GRID_ID,
    ZONE_ID,
    MATERIAL_ID,
    SECTION_ID,
    BARSPEC_ID,
    OBJECT_ID,
    REVISION_ID,
    REINFORCEMENT_ID,
    QUANTITY_ID,
)


def next_id(session: Session, prefix: str, sequence_name: str, width: int) -> str:
    """Draw the next value from a Postgres SEQUENCE and format it as a
    prefixed, zero-padded ID (e.g. "OBJ-007"). Backed by a real sequence
    (not SELECT MAX+1) so it stays race-safe under concurrent writes."""
    value = session.execute(
        text("SELECT nextval(:seq)"), {"seq": sequence_name}
    ).scalar_one()
    return f"{prefix}{value:0{width}d}"
