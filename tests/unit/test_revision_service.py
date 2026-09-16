from unittest.mock import MagicMock

import pytest

from revision_service import ObjectInput, ReinforcementInput, validate_batch

pytestmark = pytest.mark.unit


def _mock_session(
    *,
    floor_ids: list[str],
    zone_ids: list[str],
    mat_ids: list[str],
    sect_pairs: list[tuple[str, str]],
    barspec_ids: list[str],
) -> MagicMock:
    session = MagicMock()
    session.scalars.side_effect = [
        MagicMock(all=MagicMock(return_value=floor_ids)),
        MagicMock(all=MagicMock(return_value=zone_ids)),
        MagicMock(all=MagicMock(return_value=mat_ids)),
        MagicMock(all=MagicMock(return_value=barspec_ids)),
    ]
    session.execute.return_value.all.return_value = sect_pairs
    return session


def _valid_column() -> ObjectInput:
    return ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        reinforcements=[
            ReinforcementInput(
                barspec_id="D16",
                bar_role="longitudinal",
                bar_count=8,
                bar_len=3000,
            ),
            ReinforcementInput(
                barspec_id="D10",
                bar_role="transverse",
                bar_count=20,
                bar_len=1200,
                bar_space=150,
                bar_hook_type="135deg",
            ),
        ],
    )


def test_rejects_nonexistent_floor_id() -> None:
    session = _mock_session(
        floor_ids=[],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C1", "column")],
        barspec_ids=["D16", "D10"],
    )

    problems = validate_batch(session, [_valid_column()])

    assert any("floor_id 'F01' does not exist" in problem for problem in problems)


def test_rejects_transverse_bar_missing_bar_space() -> None:
    session = _mock_session(
        floor_ids=["F01"],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C1", "column")],
        barspec_ids=["D10"],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        reinforcements=[
            ReinforcementInput(
                barspec_id="D10",
                bar_role="transverse",
                bar_count=20,
                bar_len=1200,
                bar_hook_type="135deg",
            ),
        ],
    )

    problems = validate_batch(session, [obj])

    assert any("bar_space is required" in problem for problem in problems)


def test_rejects_column_with_three_geometry_points() -> None:
    session = _mock_session(
        floor_ids=["F01"],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C1", "column")],
        barspec_ids=[],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000], [0, 1000, 3000]],
    )

    problems = validate_batch(session, [obj])

    assert any("requires exactly 2 geometry_points" in problem for problem in problems)


def test_accepts_fully_valid_batch() -> None:
    session = _mock_session(
        floor_ids=["F01"],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C1", "column")],
        barspec_ids=["D16", "D10"],
    )

    problems = validate_batch(session, [_valid_column()])

    assert problems == []
