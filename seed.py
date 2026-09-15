from sqlalchemy.orm import Session

from database import engine
from models import Building, Floor, Grid, Material, Project, Section, Zone


def seed_data() -> None:
    with Session(engine) as session, session.begin():
        session.add(Project(project_id="P01", project_name="AISIMS pilot project"))
        session.flush()
        session.add(Building(building_id="B01", building_name="Tower A", project_id="P01"))
        session.flush()

        session.add_all(
            [
                Section(
                    sect_id="C1",
                    obj_type="col",
                    dim={
                        "shape": "rectangular",
                        "width": 300,
                        "depth": 300,
                    },
                ),
                Section(
                    sect_id="C2",
                    obj_type="col",
                    dim={"shape": "circular", "diameter": 300},
                ),
                Section(
                    sect_id="B1",
                    obj_type="beam",
                    dim={
                        "shape": "rectangular",
                        "width": 150,
                        "depth": 300,
                    },
                ),
                Section(
                    sect_id="W1",
                    obj_type="wall",
                    dim={"thickness": 100},
                ),
                Section(
                    sect_id="S1",
                    obj_type="slab",
                    dim={"thickness": 120},
                ),
            ]
        )

        session.add_all(
            [
                Material(
                    mat_id="K100",
                    mat_name="concrete K100",
                    mat_type="concrete",
                    mat_strength=100,
                ),
                Material(
                    mat_id="K250",
                    mat_name="concrete K250",
                    mat_type="concrete",
                    mat_strength=250,
                ),
            ]
        )

        session.add_all(
            [
                Zone(
                    zone_id="Z01",
                    pour_seq=1,
                    building_id="B01",
                ),
                Zone(
                    zone_id="Z02",
                    pour_seq=2,
                    building_id="B01",
                ),
            ]
        )

        session.add_all(
            [
                Floor(
                    floor_id="01",
                    floor_name="base level",
                    elevation=0,
                    building_id="B01",
                ),
                Floor(
                    floor_id="02",
                    floor_name="roof level",
                    elevation=3000,
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
                    grid_axis="y",
                    grid_label="A",
                    grid_coord={"value": 0},
                ),
                Grid(
                    grid_id="G04",
                    building_id="B01",
                    grid_axis="y",
                    grid_label="B",
                    grid_coord={"value": 3000},
                ),
            ]
        )

        session.flush()

    print("Seed completed: 1 project, 1 building, 5 sections, 2 materials,")
    print("2 zones, 2 floors, and 4 grids inserted.")


if __name__ == "__main__":
    seed_data()