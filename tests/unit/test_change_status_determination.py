from unittest.mock import MagicMock

import pytest

from models import BarSpec, Material, Object, Reinforcement, Revision, Section
from revision_service import (
    ResolvedObject,
    ResolvedReinforcement,
    StableIdAssignment,
    determine_change_status,
)

pytestmark = pytest.mark.unit

_ASSIGNMENT = StableIdAssignment(stable_id="abc-123", is_new=False, is_restored=False)

_SECTION = Section(
    sect_id="C1",
    sect_label="C1 - 400x400 column",
    obj_type="column",
    dim={"shape": "rectangular", "width": 400, "depth": 400},
)
_MATERIAL = Material(
    mat_id="K250",
    mat_name="concrete K250",
    mat_type="concrete",
    mat_strength=250,
    mat_weight=2400,
)


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
    *,
    previous_object: Object | None,
    previous_bars: list[Reinforcement] | None = None,
    barspecs: list[BarSpec] | None = None,
) -> MagicMock:
    session = MagicMock()
    current_revision = Revision(rev_id="R2", building_id="B01", rev_number=2)
    # _create_quantity's Material lookup shares session.get with Workflow
    # 2's Revision lookup - key off the model class so each gets the
    # right kind of object back.
    session.get.side_effect = lambda model, _id: (
        current_revision if model is Revision else _MATERIAL
    )
    session.execute.return_value.scalar_one.return_value = 1

    scalars_results = [
        MagicMock(
            first=MagicMock(
                return_value=Revision(rev_id="R1", building_id="B01", rev_number=1)
            )
        ),
        MagicMock(first=MagicMock(return_value=previous_object)),
    ]
    if previous_bars is not None:
        scalars_results.append(MagicMock(all=MagicMock(return_value=previous_bars)))
    # _create_quantity's own lookups, appended after the comparison ones.
    scalars_results.append(MagicMock(first=MagicMock(return_value=_SECTION)))
    scalars_results.append(
        MagicMock(all=MagicMock(return_value=barspecs if barspecs is not None else []))
    )
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

    barspec = BarSpec(
        barspec_id="D16",
        barspec_label="D16 deformed BjTS 420",
        barspec_dia=16,
        barspec_type="deformed",
        barspec_grade="BjTS 420",
        barspec_weight=7850,
    )
    session = _mock_session_for_comparison(
        previous_object=previous, previous_bars=previous_bars, barspecs=[barspec]
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

    barspec = BarSpec(
        barspec_id="D16",
        barspec_label="D16 deformed BjTS 420",
        barspec_dia=16,
        barspec_type="deformed",
        barspec_grade="BjTS 420",
        barspec_weight=7850,
    )
    session = _mock_session_for_comparison(
        previous_object=previous, previous_bars=previous_bars, barspecs=[barspec]
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
    session.get.return_value = _MATERIAL
    session.execute.return_value.scalar_one.return_value = 1
    session.scalars.side_effect = [
        MagicMock(first=MagicMock(return_value=_SECTION)),
        MagicMock(all=MagicMock(return_value=[])),
    ]
    assignment = StableIdAssignment(stable_id="new-1", is_new=True, is_restored=False)

    result = determine_change_status(session, _obj_input(), assignment, rev_id="R2")

    assert result.change_status == "added"
    # No revision-history lookup happens for a brand new object - the
    # only session.get() call is _create_quantity's Material lookup.
    session.get.assert_called_once_with(Material, "K250")


def test_restored_stable_id_is_restored_without_comparison() -> None:
    session = MagicMock()
    session.get.return_value = _MATERIAL
    session.execute.return_value.scalar_one.return_value = 1
    session.scalars.side_effect = [
        MagicMock(first=MagicMock(return_value=_SECTION)),
        MagicMock(all=MagicMock(return_value=[])),
    ]
    assignment = StableIdAssignment(stable_id="abc-123", is_new=False, is_restored=True)

    result = determine_change_status(session, _obj_input(), assignment, rev_id="R2")

    assert result.change_status == "restored"
    session.get.assert_called_once_with(Material, "K250")
