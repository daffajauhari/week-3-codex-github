from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from database import get_session
from main import app
from models import Dimension, Floor, Material, Member, Zone

pytestmark = pytest.mark.unit


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client(mock_session: MagicMock) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[MagicMock]:
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_members_returns_empty_list_when_no_members(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.scalars.return_value.all.return_value = []

    response = client.get("/members")

    assert response.status_code == 200
    assert response.json() == []


def test_get_member_returns_404_when_missing(
    client: TestClient, mock_session: MagicMock
) -> None:
    mock_session.get.return_value = None

    response = client.get("/members/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Member not found"}


def test_get_member_returns_detail_when_found(
    client: TestClient, mock_session: MagicMock
) -> None:
    member = Member(
        member_id="B1.02.A1A2",
        member_type="beam",
        storey_id="ST02",
        dimension_id="B1",
        material_id="K250",
        zone_id="Z02",
        geometry_points=[[0, 0, 3000], [4000, 0, 3000]],
    )
    floor = Floor(
        floor_id="ST02", floor_name="roof level", elevation=3000, building_id="B01"
    )
    material = Material(
        material_id="K250",
        material_name="concrete K250",
        material_type="concrete",
        compressive_strength_kg_cm2=250,
    )
    dimension = Dimension(
        dimension_id="B1",
        member_type="beam",
        dim={"shape": "rectangular", "width": 150, "depth": 300},
    )
    zone = Zone(zone_id="Z02", pour_seq=2, building_id="B01")

    lookup = {
        Floor: floor,
        Material: material,
        Dimension: dimension,
        Zone: zone,
    }
    mock_session.get.side_effect = lambda model, _id: (
        member if model is Member else lookup[model]
    )

    response = client.get("/members/B1.02.A1A2")

    assert response.status_code == 200
    body = response.json()
    assert body["storey_name"] == "roof level"
    assert body["material_strength_kg_cm2"] == 250
    assert body["pour_sequence"] == 2
    assert body["dimension_section"] == dimension.dim
