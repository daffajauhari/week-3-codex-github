from unittest.mock import MagicMock

import pytest

from models import Object, Reinforcement, Revision
from revision_service import (
    ResolvedObject,
    ResolvedReinforcement,
    StableIdAssignment,
    determine_change_status,
)

pytestmark = pytest.mark.unit

_ASSIGNMENT = StableIdAssignment(stable_id="abc-123", is_new=False, is_restored=False)


def _previous_object(**overrides: object) -> Object:
    defaults: dict[str, object] = {
        "obj_id": "O-prev",
        "obj_mark": "C1.F01.001",
        "stable_id": "abc-123",
        "rev_id": "R1",
        "change_status": "added",
        "obj_type": "column",
        "floor_id": "F01",
        "zone_id": "Z01",
        "sect_id": "C1",
        "mat_id": "K250",
        "geometry_points": [[0, 0, 0], [0, 0, 3000]],
    }
    defaults.update(overrides)
    return Object(**defaults)  # type: ignore[arg-type]


def _obj_input(**overrides: object) -> ResolvedObject:
    defaults: dict[str, object] = {
        "is_new": False,
        "obj_mark": "C1.F01.001",
        "obj_type": "column",
        "floor_id": "F01",
        "zone_id": "Z01",
        "sect_id": "C1",
        "mat_id": "K250",
        "geometry_points": [[0, 0, 0], [0, 0, 3000]],
        "reinforcements": [],
        "stable_id": "abc-123",
    }
    defaults.update(overrides)
    return ResolvedObject(**defaults)  # type: ignore[arg-type]


def _mock_session_for_comparison(
    *, previous_object: Object | None, previous_bars: list[Reinforcement] | None = None
) -> MagicMock:
    session = MagicMock()
    session.get.return_value = Revision(
        rev_id="R2", building_id="B01", rev_number=2
    )
    session.execute.return_value.scalar_one.return_value = 1

    scalars_results = [
        MagicMock(first=MagicMock(return_value=Revision(rev_id="R1", building_id="B01", rev_number=1))),
        MagicMock(first=MagicMock(return_value=previous_object)),
    ]
    if previous_bars is not None:
        scalars_results.append(MagicMock(all=MagicMock(return_value=previous_bars)))
    session.scalars.side_effect = scalars_results

    return session


def test_object_with_changed_own_columns_is_modified() -> None:
    previous = _previous_object(floor_id="F01")
    session = _mock_session_for_comparison(previous_object=previous)
    incoming = _obj_input(floor_id="F02")

    result = determine_change_status(session, incoming, _ASSIGNMENT, rev_id="R2")

    assert result.change_status == "modified"


def test_object_with_unchanged_columns_but_different_reinforcement_is_modified() -> None:
    previous = _previous_object()
    previous_bars = [
        Reinforcement(
            bar_id="bar-1",
            obj_id="O-prev",
            barspec_id="D16",
            bar_role="longitudinal",
            bar_count=8,
            bar_len=3000,
        )
    ]
    session = _mock_session_for_comparison(
        previous_object=previous, previous_bars=previous_bars
    )
    incoming = _obj_input(
        reinforcements=[
            ResolvedReinforcement(
                barspec_id="D16",
                bar_role="longitudinal",
                bar_count=10,  # different bar_count
                bar_len=3000,
            )
        ]
    )

    result = determine_change_status(session, incoming, _ASSIGNMENT, rev_id="R2")

    assert result.change_status == "modified"


def test_fully_identical_object_is_unchanged() -> None:
    previous = _previous_object()
    previous_bars = [
        Reinforcement(
            bar_id="bar-1",
            obj_id="O-prev",
            barspec_id="D16",
            bar_role="longitudinal",
            bar_count=8,
            bar_len=3000,
        )
    ]
    session = _mock_session_for_comparison(
        previous_object=previous, previous_bars=previous_bars
    )
    incoming = _obj_input(
        reinforcements=[
            ResolvedReinforcement(
                barspec_id="D16",
                bar_role="longitudinal",
                bar_count=8,
                bar_len=3000,
            )
        ]
    )

    result = determine_change_status(session, incoming, _ASSIGNMENT, rev_id="R2")

    assert result.change_status == "unchanged"


def test_new_stable_id_is_added_without_comparison() -> None:
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 1
    assignment = StableIdAssignment(stable_id="new-1", is_new=True, is_restored=False)

    result = determine_change_status(session, _obj_input(), assignment, rev_id="R2")

    assert result.change_status == "added"
    session.get.assert_not_called()


def test_restored_stable_id_is_restored_without_comparison() -> None:
    session = MagicMock()
    session.execute.return_value.scalar_one.return_value = 1
    assignment = StableIdAssignment(stable_id="abc-123", is_new=False, is_restored=True)

    result = determine_change_status(session, _obj_input(), assignment, rev_id="R2")

    assert result.change_status == "restored"
    session.get.assert_not_called()
