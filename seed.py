from sqlalchemy.orm import Session

from database import engine
from ids import (
    BARSPEC_ID,
    BUILDING_ID,
    FLOOR_ID,
    GRID_ID,
    MATERIAL_ID,
    PROJECT_ID,
    SECTION_ID,
    ZONE_ID,
    next_id,
)
from models import BarSpec, Building, Floor, Grid, Material, Project, Section, Zone


def seed_data() -> None:
    """Seed the Project Configuration tables only (D23).

    IDs are drawn from the same sequences the API's POST endpoints use
    (ids.next_id), so seeded rows carry the same "PRJ-001"-style IDs a
    user would get from the real endpoints (D28) instead of ad-hoc
    values.

    Project Design data (Object, Reinforcement, Quantity, Identity,
    Revision) is intentionally left empty here - it is populated by
    exercising the Bulk Upload endpoint via /docs instead.
    """
    with Session(engine) as session, session.begin():
        project = Project(
            project_id=next_id(session, *PROJECT_ID),
            project_name="AISIMS pilot project",
        )
        session.add(project)
        session.flush()

        building = Building(
            building_id=next_id(session, *BUILDING_ID),
            building_name="Tower A",
            project_id=project.project_id,
        )
        session.add(building)
        session.flush()

        session.add_all(
            [
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="C1 - 400x400 column",
                    obj_type="column",
                    dim={"shape": "rectangular", "width": 400, "depth": 400},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="C2 - Ø350 column",
                    obj_type="column",
                    dim={"shape": "circular", "diameter": 350},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="C3 - 300x300 column",
                    obj_type="column",
                    dim={"shape": "rectangular", "width": 300, "depth": 300},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="B1 - 250x500 beam",
                    obj_type="beam",
                    dim={"shape": "rectangular", "width": 250, "depth": 500},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="B2 - 200x400 beam",
                    obj_type="beam",
                    dim={"shape": "rectangular", "width": 200, "depth": 400},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="W1 - 200mm wall",
                    obj_type="wall",
                    dim={"thickness": 200},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="S1 - 120mm slab",
                    obj_type="slab",
                    dim={"thickness": 120},
                ),
                Section(
                    sect_id=next_id(session, *SECTION_ID),
                    sect_label="S2 - 150mm slab",
                    obj_type="slab",
                    dim={"thickness": 150},
                ),
            ]
        )

        session.add_all(
            [
                Material(
                    mat_id=next_id(session, *MATERIAL_ID),
                    mat_name="concrete K250",
                    mat_type="concrete",
                    mat_strength=250,
                    mat_weight=2400,
                ),
                Material(
                    mat_id=next_id(session, *MATERIAL_ID),
                    mat_name="concrete K300",
                    mat_type="concrete",
                    mat_strength=300,
                    mat_weight=2400,
                ),
                Material(
                    mat_id=next_id(session, *MATERIAL_ID),
                    mat_name="concrete K350",
                    mat_type="concrete",
                    mat_strength=350,
                    mat_weight=2400,
                ),
            ]
        )

        session.add_all(
            [
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="D10 deformed BjTS 420",
                    barspec_dia=10,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                    barspec_weight=7850,
                ),
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="D13 deformed BjTS 420",
                    barspec_dia=13,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                    barspec_weight=7850,
                ),
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="D16 deformed BjTS 420",
                    barspec_dia=16,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                    barspec_weight=7850,
                ),
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="D19 deformed BjTS 420",
                    barspec_dia=19,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                    barspec_weight=7850,
                ),
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="D22 deformed BjTS 420",
                    barspec_dia=22,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                    barspec_weight=7850,
                ),
                BarSpec(
                    barspec_id=next_id(session, *BARSPEC_ID),
                    barspec_label="P8 plain BjTP 280",
                    barspec_dia=8,
                    barspec_type="plain",
                    barspec_grade="BjTP 280",
                    barspec_weight=7850,
                ),
            ]
        )

        session.add_all(
            [
                Zone(
                    zone_id=next_id(session, *ZONE_ID),
                    zone_label="Zone 1",
                    pour_seq=1,
                    building_id=building.building_id,
                ),
                Zone(
                    zone_id=next_id(session, *ZONE_ID),
                    zone_label="Zone 2",
                    pour_seq=2,
                    building_id=building.building_id,
                ),
                Zone(
                    zone_id=next_id(session, *ZONE_ID),
                    zone_label="Zone 3",
                    pour_seq=3,
                    building_id=building.building_id,
                ),
            ]
        )

        session.add_all(
            [
                Floor(
                    floor_id=next_id(session, *FLOOR_ID),
                    floor_name="ground floor",
                    elevation=0,
                    building_id=building.building_id,
                ),
                Floor(
                    floor_id=next_id(session, *FLOOR_ID),
                    floor_name="2nd floor",
                    elevation=3500,
                    building_id=building.building_id,
                ),
                Floor(
                    floor_id=next_id(session, *FLOOR_ID),
                    floor_name="3rd floor",
                    elevation=7000,
                    building_id=building.building_id,
                ),
                Floor(
                    floor_id=next_id(session, *FLOOR_ID),
                    floor_name="roof floor",
                    elevation=10500,
                    building_id=building.building_id,
                ),
            ]
        )

        session.add_all(
            [
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="x",
                    grid_label="1",
                    grid_coord={"x": 0, "y": 0},
                ),
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="x",
                    grid_label="2",
                    grid_coord={"x": 4000, "y": 0},
                ),
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="x",
                    grid_label="3",
                    grid_coord={"x": 8000, "y": 0},
                ),
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="y",
                    grid_label="A",
                    grid_coord={"x": 0, "y": 0},
                ),
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="y",
                    grid_label="B",
                    grid_coord={"x": 0, "y": 3000},
                ),
                Grid(
                    grid_id=next_id(session, *GRID_ID),
                    building_id=building.building_id,
                    grid_axis="y",
                    grid_label="C",
                    grid_coord={"x": 0, "y": 6000},
                ),
            ]
        )

        session.flush()

    print("Seed completed: 1 project, 1 building, 8 sections, 3 materials,")
    print("6 bar specs, 3 zones, 4 floors, and 6 grids inserted.")


if __name__ == "__main__":
    seed_data()
