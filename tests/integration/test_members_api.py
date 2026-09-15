import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import Building, Dimension, Floor, Material, Member, Project, Zone

pytestmark = pytest.mark.integration


def _seed_beam(session: Session) -> None:
    session.add(Project(project_id="P01", project_name="AISIMS pilot project"))
    session.flush()
    session.add(Building(building_id="B01", building_name="Tower A", project_id="P01"))
    session.flush()

    session.add_all(
        [
            Floor(
                floor_id="ST02",
                floor_name="roof level",
                elevation=3000,
                building_id="B01",
            ),
            Material(
                material_id="K250",
                material_name="concrete K250",
                material_type="concrete",
                compressive_strength_kg_cm2=250,
            ),
            Dimension(
                dimension_id="B1",
                member_type="beam",
                dim={"shape": "rectangular", "width": 150, "depth": 300},
            ),
            Zone(zone_id="Z02", pour_seq=2, building_id="B01"),
        ]
    )
    session.flush()
    session.add(
        Member(
            member_id="B1.02.A1A2",
            member_type="beam",
            storey_id="ST02",
            dimension_id="B1",
            material_id="K250",
            zone_id="Z02",
            geometry_points=[[0, 0, 3000], [4000, 0, 3000]],
        )
    )
    session.flush()


def test_get_members_lists_seeded_member(client: TestClient, db_session: Session) -> None:
    _seed_beam(db_session)

    response = client.get("/members")

    assert response.status_code == 200
    member_ids = [member["member_id"] for member in response.json()]
    assert member_ids == ["B1.02.A1A2"]


def test_get_member_detail_joins_related_records(
    client: TestClient, db_session: Session
) -> None:
    _seed_beam(db_session)

    response = client.get("/members/B1.02.A1A2")

    assert response.status_code == 200
    body = response.json()
    assert body["storey_name"] == "roof level"
    assert body["material_strength_kg_cm2"] == 250
    assert body["pour_sequence"] == 2
    assert body["dimension_section"] == {
        "shape": "rectangular",
        "width": 150,
        "depth": 300,
    }


def test_get_member_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/members/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Member not found"}
