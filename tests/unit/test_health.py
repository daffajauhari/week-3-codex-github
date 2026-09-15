import pytest
from fastapi.testclient import TestClient

from main import app

pytestmark = pytest.mark.unit


def test_hello_reports_backend_running() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Backend is running"}
