from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from models import Building, Project

pytestmark = pytest.mark.unit


def _raise_integrity_error() -> None:
    raise IntegrityError("stmt", {}, Exception("duplicate key"))


# --- POST /projects -----------------------------------------------------


def test_create_project_happy_path(client: TestClient, mock_session: MagicMock) -> None:
    response = client.post("/projects", json={"project_name": "AISIMS pilot"})

    assert response.status_code == 201
    body = response.json()
    assert body["project_name"] == "AISIMS pilot"
    assert body["project_id"]
    mock_session.commit.assert_called_once()


def test_create_project_conflict_on_duplicate_name(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.commit.side_effect = _raise_integrity_error

    response = client.post("/projects", json={"project_name": "AISIMS pilot"})

    assert response.status_code == 409
    mock_session.rollback.assert_called_once()


# --- POST /projects/{project_id}/buildings -------------------------------


def test_create_building_happy_path(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Project(project_id="P01", project_name="pilot")

    response = client.post(
        "/projects/P01/buildings", json={"building_name": "Tower A"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["building_name"] == "Tower A"
    assert body["project_id"] == "P01"


def test_create_building_returns_404_for_unknown_project(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = None

    response = client.post(
        "/projects/does-not-exist/buildings", json={"building_name": "Tower A"}
    )

    assert response.status_code == 404


# --- POST /projects/{project_id}/buildings/{building_id}/floors ---------


def test_create_floor_happy_path(client: TestClient, mock_session: MagicMock) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )

    response = client.post(
        "/projects/P01/buildings/B01/floors",
        json={"floor_name": "4th floor", "elevation": 14000},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["floor_name"] == "4th floor"
    assert body["building_id"] == "B01"


def test_create_floor_returns_400_when_building_belongs_to_other_project(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P99"
    )

    response = client.post(
        "/projects/P01/buildings/B01/floors",
        json={"floor_name": "4th floor", "elevation": 14000},
    )

    assert response.status_code == 400


def test_create_floor_returns_404_for_unknown_building(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = None

    response = client.post(
        "/projects/P01/buildings/does-not-exist/floors",
        json={"floor_name": "4th floor", "elevation": 14000},
    )

    assert response.status_code == 404


# --- POST /projects/{project_id}/buildings/{building_id}/zones ----------


def test_create_zone_happy_path(client: TestClient, mock_session: MagicMock) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )

    response = client.post(
        "/projects/P01/buildings/B01/zones",
        json={"zone_label": "Zone 4", "pour_seq": 4},
    )

    assert response.status_code == 201
    assert response.json()["zone_label"] == "Zone 4"


# --- POST /projects/{project_id}/buildings/{building_id}/grid -----------


def test_create_grid_happy_path(client: TestClient, mock_session: MagicMock) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )

    response = client.post(
        "/projects/P01/buildings/B01/grid",
        json={
            "grid_label": "4",
            "grid_axis": "x",
            "grid_coord": {"x": 12000, "y": 0},
        },
    )

    assert response.status_code == 201
    assert response.json()["grid_coord"] == {"x": 12000, "y": 0}


def test_create_grid_rejects_old_value_shape(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )

    response = client.post(
        "/projects/P01/buildings/B01/grid",
        json={"grid_label": "4", "grid_axis": "x", "grid_coord": {"value": 12000}},
    )

    assert response.status_code == 422


def test_create_grid_conflict_on_duplicate_label_axis(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = Building(
        building_id="B01", building_name="Tower A", project_id="P01"
    )
    mock_session.commit.side_effect = _raise_integrity_error

    response = client.post(
        "/projects/P01/buildings/B01/grid",
        json={"grid_label": "1", "grid_axis": "x", "grid_coord": {"x": 0, "y": 0}},
    )

    assert response.status_code == 409


# --- POST /materials ------------------------------------------------------


def test_create_material_happy_path(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/materials",
        json={
            "mat_name": "concrete K400",
            "mat_type": "concrete",
            "mat_strength": 400,
            "mat_weight": 2400,
        },
    )

    assert response.status_code == 201
    assert response.json()["mat_name"] == "concrete K400"


# --- POST /sections - VR-10 shape validation, all variants ---------------


def test_create_section_accepts_rectangular_dimension(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/sections",
        json={
            "obj_type": "column",
            "sect_label": "C4 - 350x350 column",
            "dimension": {"shape": "rectangular", "width": 350, "depth": 350},
        },
    )

    assert response.status_code == 201


def test_create_section_accepts_circular_dimension(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/sections",
        json={
            "obj_type": "column",
            "sect_label": "C5 - circular column",
            "dimension": {"shape": "circular", "diameter": 400},
        },
    )

    assert response.status_code == 201


def test_create_section_accepts_thickness_dimension_for_boundary_type(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/sections",
        json={
            "obj_type": "slab",
            "sect_label": "S3 - 180mm slab",
            "dimension": {"thickness": 180},
        },
    )

    assert response.status_code == 201


def test_create_section_rejects_missing_shape_for_axis_type(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/sections",
        json={
            "obj_type": "column",
            "sect_label": "C6 - bad column",
            "dimension": {"thickness": 200},
        },
    )

    assert response.status_code == 422
    assert any("rectangular" in detail for detail in response.json()["detail"])


def test_create_section_conflict_on_duplicate_label(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.commit.side_effect = _raise_integrity_error

    response = client.post(
        "/sections",
        json={
            "obj_type": "column",
            "sect_label": "C1 - 400x400 column",
            "dimension": {"shape": "rectangular", "width": 400, "depth": 400},
        },
    )

    assert response.status_code == 409


# --- POST /barspec ---------------------------------------------------------


def test_create_barspec_happy_path(
    client: TestClient, mock_session: MagicMock
) -> None:
    response = client.post(
        "/barspec",
        json={
            "barspec_label": "D25 deformed BjTS 420",
            "barspec_dia": 25,
            "barspec_type": "deformed",
            "barspec_grade": "BjTS 420",
            "barspec_weight": 7850,
        },
    )

    assert response.status_code == 201
    assert response.json()["barspec_dia"] == 25
