from sqlalchemy.orm import Session

from database import engine
from models import BarSpec, Building, Floor, Grid, Material, Project, Section, Zone


def seed_data() -> None:
    """Seed the Project Configuration tables only (D23).

    Project Design data (Object, Reinforcement, Quantity, Identity,
    Revision) is intentionally left empty here - it is populated by
    exercising the Bulk Upload endpoint via /docs instead.
    """
    with Session(engine) as session, session.begin():
        session.add(
            Project(project_id="P01", project_name="AISIMS pilot project")
        )
        session.flush()
        session.add(
            Building(
                building_id="B01", building_name="Tower A", project_id="P01"
            )
        )
        session.flush()

        session.add_all(
            [
                Section(
                    sect_id="C1",
                    obj_type="column",
                    dim={"shape": "rectangular", "width": 400, "depth": 400},
                ),
                Section(
                    sect_id="C2",
                    obj_type="column",
                    dim={"shape": "circular", "diameter": 350},
                ),
                Section(
                    sect_id="C3",
                    obj_type="column",
                    dim={"shape": "rectangular", "width": 300, "depth": 300},
                ),
                Section(
                    sect_id="B1",
                    obj_type="beam",
                    dim={"shape": "rectangular", "width": 250, "depth": 500},
                ),
                Section(
                    sect_id="B2",
                    obj_type="beam",
                    dim={"shape": "rectangular", "width": 200, "depth": 400},
                ),
                Section(
                    sect_id="W1",
                    obj_type="wall",
                    dim={"thickness": 200},
                ),
                Section(
                    sect_id="S1",
                    obj_type="slab",
                    dim={"thickness": 120},
                ),
                Section(
                    sect_id="S2",
                    obj_type="slab",
                    dim={"thickness": 150},
                ),
            ]
        )

        session.add_all(
            [
                Material(
                    mat_id="K250",
                    mat_name="concrete K250",
                    mat_type="concrete",
                    mat_strength=250,
                ),
                Material(
                    mat_id="K300",
                    mat_name="concrete K300",
                    mat_type="concrete",
                    mat_strength=300,
                ),
                Material(
                    mat_id="K350",
                    mat_name="concrete K350",
                    mat_type="concrete",
                    mat_strength=350,
                ),
            ]
        )

        session.add_all(
            [
                BarSpec(
                    barspec_id="D10",
                    barspec_dia=10,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                ),
                BarSpec(
                    barspec_id="D13",
                    barspec_dia=13,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                ),
                BarSpec(
                    barspec_id="D16",
                    barspec_dia=16,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                ),
                BarSpec(
                    barspec_id="D19",
                    barspec_dia=19,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                ),
                BarSpec(
                    barspec_id="D22",
                    barspec_dia=22,
                    barspec_type="deformed",
                    barspec_grade="BjTS 420",
                ),
                BarSpec(
                    barspec_id="P8",
                    barspec_dia=8,
                    barspec_type="plain",
                    barspec_grade="BjTP 280",
                ),
            ]
        )

        session.add_all(
            [
                Zone(zone_id="Z01", pour_seq=1, building_id="B01"),
                Zone(zone_id="Z02", pour_seq=2, building_id="B01"),
                Zone(zone_id="Z03", pour_seq=3, building_id="B01"),
            ]
        )

        session.add_all(
            [
                Floor(
                    floor_id="F01",
                    floor_name="ground floor",
                    elevation=0,
                    building_id="B01",
                ),
                Floor(
                    floor_id="F02",
                    floor_name="2nd floor",
                    elevation=3500,
                    building_id="B01",
                ),
                Floor(
                    floor_id="F03",
                    floor_name="3rd floor",
                    elevation=7000,
                    building_id="B01",
                ),
                Floor(
                    floor_id="F04",
                    floor_name="roof floor",
                    elevation=10500,
                    building_id="B01",
                ),
            ]
        )

        session.add_all(
            [
                Grid(
                    grid_id="G01",
                    building_id="B01",
                    grid_axis="x",
                    grid_label="1",
                    grid_coord={"value": 0},
                ),
                Grid(
                    grid_id="G02",
                    building_id="B01",
                    grid_axis="x",
                    grid_label="2",
                    grid_coord={"value": 4000},
                ),
                Grid(
                    grid_id="G03",
                    building_id="B01",
                    grid_axis="x",
                    grid_label="3",
                    grid_coord={"value": 8000},
                ),
                Grid(
                    grid_id="G04",
                    building_id="B01",
                    grid_axis="y",
                    grid_label="A",
                    grid_coord={"value": 0},
                ),
                Grid(
                    grid_id="G05",
                    building_id="B01",
                    grid_axis="y",
                    grid_label="B",
                    grid_coord={"value": 3000},
                ),
                Grid(
                    grid_id="G06",
                    building_id="B01",
                    grid_axis="y",
                    grid_label="C",
                    grid_coord={"value": 6000},
                ),
            ]
        )

        session.flush()

    print("Seed completed: 1 project, 1 building, 8 sections, 3 materials,")
    print("6 bar specs, 3 zones, 4 floors, and 6 grids inserted.")


if __name__ == "__main__":
    seed_data()
