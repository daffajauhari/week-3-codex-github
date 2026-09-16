import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import BarSpec, Building, Floor, Material, Project, Section, Zone

pytestmark = pytest.mark.integration


def _seed_project_config(session: Session) -> None:
    session.add(Project(project_id="P01", project_name="pilot"))
    session.flush()
    session.add(Building(building_id="B01", building_name="Tower A", project_id="P01"))
    session.flush()
    session.add_all(
        [
            Floor(floor_id="F01", floor_name="ground", elevation=0, building_id="B01"),
            Zone(zone_id="Z01", zone_label="Zone 1", pour_seq=1, building_id="B01"),
            Section(
                sect_id="C1",
                sect_label="C1 - 400x400 column",
                obj_type="column",
                dim={"shape": "rectangular", "width": 400, "depth": 400},
            ),
            Material(
                mat_id="K250",
                mat_name="concrete K250",
                mat_type="concrete",
                mat_strength=250,
                mat_weight=2400,
            ),
            BarSpec(
                barspec_id="D16",
                barspec_label="D16 deformed BjTS 420",
                barspec_dia=16,
                barspec_type="deformed",
                barspec_grade="BjTS 420",
                barspec_weight=7850,
            ),
        ]
    )
    session.flush()


def _column_payload(*, obj_mark: str, x: int) -> dict:
    return {
        "is_new": True,
        "obj_mark": obj_mark,
        "obj_type": "column",
        "floor_name": "ground",
        "zone_label": "Zone 1",
        "sect_label": "C1 - 400x400 column",
        "mat_name": "concrete K250",
        "geometry_points": [[x, 0, 0], [x, 0, 3000]],
        # VR-11: concrete objects need at least one reinforcement row.
        "reinforcements": [
            {
                "barspec_label": "D16 deformed BjTS 420",
                "bar_role": "longitudinal",
                "bar_count": 8,
                "bar_len": 3000,
            }
        ],
    }


def test_first_bulk_upload_creates_revision_zero_with_all_added(
    client: TestClient, db_session: Session
) -> None:
    _seed_project_config(db_session)

    response = client.post(
        "/projects/P01/buildings/B01/revisions/bulk",
        json={
            "objects": [
                _column_payload(obj_mark="C1.F01.001", x=0),
                _column_payload(obj_mark="C1.F01.002", x=4000),
            ]
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["rev_number"] == 0
    assert len(body["objects"]) == 2
    assert {obj["change_status"] for obj in body["objects"]} == {"added"}


def test_second_bulk_upload_reports_modified_unchanged_and_deleted(
    client: TestClient, db_session: Session
) -> None:
    _seed_project_config(db_session)

    first = client.post(
        "/projects/P01/buildings/B01/revisions/bulk",
        json={
            "objects": [
                _column_payload(obj_mark="C1.F01.001", x=0),
                _column_payload(obj_mark="C1.F01.002", x=4000),
                _column_payload(obj_mark="C1.F01.003", x=8000),
            ]
        },
    )
    assert first.status_code == 201
    first_objects = {obj["obj_mark"]: obj for obj in first.json()["objects"]}

    second_payload = {
        "objects": [
            {
                **_column_payload(obj_mark="C1.F01.001", x=0),
                "is_new": False,
                "stable_id": first_objects["C1.F01.001"]["stable_id"],
                "geometry_points": [[0, 0, 0], [0, 0, 3500]],
            },
            {
                **_column_payload(obj_mark="C1.F01.002", x=4000),
                "is_new": False,
                "stable_id": first_objects["C1.F01.002"]["stable_id"],
            },
            # C1.F01.003 omitted entirely -> deleted
        ]
    }

    response = client.post(
        "/projects/P01/buildings/B01/revisions/bulk", json=second_payload
    )

    assert response.status_code == 201
    body = response.json()
    assert body["rev_number"] == 1
    statuses = {obj["obj_mark"]: obj["change_status"] for obj in body["objects"]}
    assert statuses["C1.F01.001"] == "modified"
    assert statuses["C1.F01.002"] == "unchanged"
    assert statuses["C1.F01.003"] == "deleted"


def test_bulk_upload_rejects_building_from_a_different_project(
    client: TestClient, db_session: Session
) -> None:
    _seed_project_config(db_session)
    db_session.add(Project(project_id="P02", project_name="other project"))
    db_session.flush()

    response = client.post(
        "/projects/P02/buildings/B01/revisions/bulk",
        json={"objects": [_column_payload(obj_mark="C1.F01.001", x=0)]},
    )

    assert response.status_code == 400


def test_bulk_upload_returns_404_for_unknown_building(
    client: TestClient, db_session: Session
) -> None:
    db_session.add(Project(project_id="P01", project_name="pilot"))
    db_session.flush()

    response = client.post(
        "/projects/P01/buildings/does-not-exist/revisions/bulk",
        json={"objects": []},
    )

    assert response.status_code == 404
