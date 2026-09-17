from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from database import get_session
from main import app


@pytest.fixture()
def mock_session() -> MagicMock:
    session = MagicMock()
    # Every POST endpoint's next_id() call reads a sequence via
    # session.execute(...).scalar_one() - stub it so ID generation works
    # without each test having to configure it individually.
    session.execute.return_value.scalar_one.return_value = 1
    return session


@pytest.fixture()
def client(mock_session: MagicMock) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[MagicMock]:
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
