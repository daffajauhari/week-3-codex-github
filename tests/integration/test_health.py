import pytest
from fastapi.testclient import TestClient

from main import app

pytestmark = pytest.mark.integration


def test_db_check_connects_to_real_database() -> None:
    with TestClient(app) as client:
        response = client.get("/db-check")

    assert response.status_code == 200
    assert response.json()["status"] == "connected"
