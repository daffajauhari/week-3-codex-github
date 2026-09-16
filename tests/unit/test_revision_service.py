from unittest.mock import MagicMock

import pytest

from revision_service import ObjectInput, ReinforcementInput, validate_batch

pytestmark = pytest.mark.unit

_RECTANGULAR_COLUMN_DIM = {"shape": "rectangular", "width": 400, "depth": 400}


def _mock_session(
    *,
    floor_ids: list[str],
    zone_ids: list[str],
    mat_ids: list[str],
    sect_pairs: list[tuple[str, str]],
    barspec_ids: list[str],
    sect_dims: list[tuple[str, str, dict]] | None = None,
) -> MagicMock:
    if sect_dims is None:
        sect_dims = [
            (sect_id, obj_type, _RECTANGULAR_COLUMN_DIM)
            for sect_id, obj_type in sect_pairs
        ]

    session = MagicMock()
    session.scalars.side_effect = [
        MagicMock(all=MagicMock(return_value=floor_ids)),
        MagicMock(all=MagicMock(return_value=zone_ids)),
        MagicMock(all=MagicMock(return_value=mat_ids)),
        MagicMock(all=MagicMock(return_value=barspec_ids)),
    ]
    session.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=sect_pairs)),
        MagicMock(all=MagicMock(return_value=sect_dims)),
    ]
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


def test_rejects_circular_section_missing_diameter() -> None:
    session = _mock_session(
        floor_ids=["F01"],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C2", "column")],
        barspec_ids=[],
        sect_dims=[("C2", "column", {"shape": "circular"})],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C2.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C2",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )

    problems = validate_batch(session, [obj])

    assert any("requires diameter > 0" in problem for problem in problems)


def test_accepts_circular_section_with_valid_diameter() -> None:
    session = _mock_session(
        floor_ids=["F01"],
        zone_ids=["Z01"],
        mat_ids=["K250"],
        sect_pairs=[("C2", "column")],
        barspec_ids=[],
        sect_dims=[("C2", "column", {"shape": "circular", "diameter": 350})],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C2.F01.001",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C2",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )

    problems = validate_batch(session, [obj])

    assert problems == []
