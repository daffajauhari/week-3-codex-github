import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import Building, Floor, Material, Project, Section, Zone

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
        ]
    )
    session.flush()


def _column_payload(*, obj_mark: str, x: int) -> dict:
    return {
        "is_new": True,
        "obj_mark": obj_mark,
        "obj_type": "column",
        "floor_id": "F01",
        "zone_id": "Z01",
        "sect_id": "C1",
        "mat_id": "K250",
        "geometry_points": [[x, 0, 0], [x, 0, 3000]],
        "reinforcements": [],
    }


def test_edit_carries_forward_untouched_changes_one_and_deletes_another(
    client: TestClient, db_session: Session
) -> None:
    _seed_project_config(db_session)

    baseline = client.post(
        "/buildings/B01/revisions/bulk",
        json={
            "objects": [
                _column_payload(obj_mark="C1.F01.001", x=0),
                _column_payload(obj_mark="C1.F01.002", x=4000),
                _column_payload(obj_mark="C1.F01.003", x=8000),
            ]
        },
    )
    assert baseline.status_code == 201
    baseline_objects = {obj["obj_mark"]: obj for obj in baseline.json()["objects"]}

    edit_response = client.post(
        "/buildings/B01/revisions/edit",
        json={
            "changed_objects": [
                {
                    **_column_payload(obj_mark="C1.F01.001", x=0),
                    "is_new": False,
                    "stable_id": baseline_objects["C1.F01.001"]["stable_id"],
                    "geometry_points": [[0, 0, 0], [0, 0, 3500]],
                },
            ],
            "deleted_stable_ids": [baseline_objects["C1.F01.002"]["stable_id"]],
        },
    )

    assert edit_response.status_code == 201
    body = edit_response.json()
    assert body["rev_number"] == 1
    statuses = {obj["obj_mark"]: obj["change_status"] for obj in body["objects"]}
    assert statuses["C1.F01.001"] == "modified"
    assert statuses["C1.F01.002"] == "deleted"
    # untouched object must be carried forward, never silently dropped
    assert statuses["C1.F01.003"] == "unchanged"
    assert len(body["objects"]) == 3
