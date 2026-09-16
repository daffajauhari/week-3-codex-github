from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from models import (
    BarSpec,
    Building,
    Floor,
    Material,
    Object,
    Project,
    Reinforcement,
    Revision,
    Section,
    Zone,
)

pytestmark = pytest.mark.unit


def _scalars_all(*values: list) -> list[MagicMock]:
    return [MagicMock(all=MagicMock(return_value=v)) for v in values]


def test_list_projects_happy_path(client: TestClient, mock_session: MagicMock) -> None:
    mock_session.scalars.return_value.all.return_value = [
        Project(project_id="P01", project_name="pilot")
    ]

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == [{"project_id": "P01", "project_name": "pilot"}]


def test_list_buildings_returns_404_for_unknown_project(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = None

    response = client.get("/projects/does-not-exist/buildings")

    assert response.status_code == 404


def test_list_buildings_happy_path(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Project(project_id="P01", project_name="pilot")
    mock_session.scalars.return_value.all.return_value = [
        Building(building_id="B01", building_name="Tower A", project_id="P01")
    ]

    response = client.get("/projects/P01/buildings")

    assert response.status_code == 200
    assert response.json()[0]["building_id"] == "B01"


def test_list_revisions_returns_400_for_building_in_other_project(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P99"
    )

    response = client.get("/projects/P01/buildings/B01/revisions")

    assert response.status_code == 400


def test_list_revisions_happy_path_ordered_by_rev_number(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )
    mock_session.scalars.return_value.all.return_value = [
        Revision(rev_id="REV-001", building_id="B01", rev_number=0),
        Revision(rev_id="REV-002", building_id="B01", rev_number=1),
    ]

    response = client.get("/projects/P01/buildings/B01/revisions")

    assert response.status_code == 200
    body = response.json()
    assert [r["rev_number"] for r in body] == [0, 1]


def test_list_objects_resolves_names_instead_of_raw_ids(
    client: TestClient, mock_session: MagicMock
) -> None:
    building = Building(building_id="B01", building_name="Tower A", project_id="P01")
    revision = Revision(rev_id="REV-001", building_id="B01", rev_number=0)
    mock_session.get.side_effect = [building, revision]

    obj = Object(
        obj_id="OBJ-001",
        obj_mark="C1.F01.001",
        stable_id="abc-123",
        rev_id="REV-001",
        change_status="added",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )
    floor = Floor(floor_id="F01", floor_name="ground floor", elevation=0, building_id="B01")
    zone = Zone(zone_id="Z01", zone_label="Zone 1", pour_seq=1, building_id="B01")
    section = Section(
        sect_id="C1",
        sect_label="C1 - 400x400 column",
        obj_type="column",
        dim={"shape": "rectangular", "width": 400, "depth": 400},
    )
    material = Material(
        mat_id="K250",
        mat_name="concrete K250",
        mat_type="concrete",
        mat_strength=250,
        mat_weight=2400,
    )

    mock_session.scalars.side_effect = _scalars_all(
        [obj], [floor], [zone], [section], [material]
    )

    response = client.get("/projects/P01/buildings/B01/revisions/REV-001/objects")

    assert response.status_code == 200
    body = response.json()[0]
    assert body["floor_name"] == "ground floor"
    assert body["zone_label"] == "Zone 1"
    assert body["sect_label"] == "C1 - 400x400 column"
    assert body["mat_name"] == "concrete K250"


def test_get_object_detail_returns_404_for_object_in_another_revision(
    client: TestClient, mock_session: MagicMock
) -> None:
    building = Building(building_id="B01", building_name="Tower A", project_id="P01")
    revision = Revision(rev_id="REV-001", building_id="B01", rev_number=0)
    other_rev_obj = Object(
        obj_id="OBJ-001",
        obj_mark="C1.F01.001",
        stable_id="abc-123",
        rev_id="REV-999",
        change_status="added",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )
    mock_session.get.side_effect = [building, revision, other_rev_obj]

    response = client.get(
        "/projects/P01/buildings/B01/revisions/REV-001/objects/OBJ-001"
    )

    assert response.status_code == 400


def test_get_object_detail_happy_path_with_reinforcements(
    client: TestClient, mock_session: MagicMock
) -> None:
    building = Building(building_id="B01", building_name="Tower A", project_id="P01")
    revision = Revision(rev_id="REV-001", building_id="B01", rev_number=0)
    obj = Object(
        obj_id="OBJ-001",
        obj_mark="C1.F01.001",
        stable_id="abc-123",
        rev_id="REV-001",
        change_status="added",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )
    floor = Floor(floor_id="F01", floor_name="ground floor", elevation=0, building_id="B01")
    zone = Zone(zone_id="Z01", zone_label="Zone 1", pour_seq=1, building_id="B01")
    material = Material(
        mat_id="K250",
        mat_name="concrete K250",
        mat_type="concrete",
        mat_strength=250,
        mat_weight=2400,
    )
    section = Section(
        sect_id="C1",
        sect_label="C1 - 400x400 column",
        obj_type="column",
        dim={"shape": "rectangular", "width": 400, "depth": 400},
    )
    bar = Reinforcement(
        bar_id="RBAR-0001",
        obj_id="OBJ-001",
        barspec_id="D16",
        bar_role="longitudinal",
        bar_count=8,
        bar_len=3000,
    )
    barspec = BarSpec(
        barspec_id="D16",
        barspec_label="D16 deformed BjTS 420",
        barspec_dia=16,
        barspec_type="deformed",
        barspec_grade="BjTS 420",
        barspec_weight=7850,
    )

    mock_session.get.side_effect = [building, revision, obj, floor, zone, material]
    mock_session.scalars.side_effect = [
        MagicMock(first=MagicMock(return_value=section)),
        MagicMock(all=MagicMock(return_value=[bar])),
        MagicMock(all=MagicMock(return_value=[barspec])),
        MagicMock(first=MagicMock(return_value=None)),
    ]

    response = client.get(
        "/projects/P01/buildings/B01/revisions/REV-001/objects/OBJ-001"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["sect_label"] == "C1 - 400x400 column"
    assert body["dimension"] == {"shape": "rectangular", "width": 400, "depth": 400}
    assert len(body["reinforcements"]) == 1
    assert body["reinforcements"][0]["barspec_label"] == "D16 deformed BjTS 420"
    assert body["quantity"] is None
