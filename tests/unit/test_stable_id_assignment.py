from unittest.mock import MagicMock

import pytest

from models import Identity
from revision_service import ResolvedObject, assign_stable_ids

pytestmark = pytest.mark.unit


def _column(*, is_new: bool, stable_id: str | None = None) -> ResolvedObject:
    return ResolvedObject(
        is_new=is_new,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        stable_id=stable_id,
    )


def test_new_object_gets_a_fresh_stable_id_and_active_identity() -> None:
    session = MagicMock()

    assignments = assign_stable_ids(session, [_column(is_new=True)])

    assert len(assignments) == 1
    assert assignments[0].is_new is True
    assert assignments[0].is_restored is False
    assert assignments[0].stable_id

    session.add.assert_called_once()
    added_identity = session.add.call_args.args[0]
    assert isinstance(added_identity, Identity)
    assert added_identity.stable_id == assignments[0].stable_id
    assert added_identity.is_active is True


def test_existing_active_object_is_looked_up_without_restoring() -> None:
    session = MagicMock()
    identity = Identity(stable_id="abc-123", is_active=True)
    session.get.return_value = identity

    assignments = assign_stable_ids(
        session, [_column(is_new=False, stable_id="abc-123")]
    )

    assert assignments[0].stable_id == "abc-123"
    assert assignments[0].is_new is False
    assert assignments[0].is_restored is False
    assert identity.is_active is True
    session.add.assert_not_called()


def test_existing_inactive_object_is_restored() -> None:
    session = MagicMock()
    identity = Identity(stable_id="abc-123", is_active=False)
    session.get.return_value = identity

    assignments = assign_stable_ids(
        session, [_column(is_new=False, stable_id="abc-123")]
    )

    assert assignments[0].stable_id == "abc-123"
    assert assignments[0].is_new is False
    assert assignments[0].is_restored is True
    assert identity.is_active is True
