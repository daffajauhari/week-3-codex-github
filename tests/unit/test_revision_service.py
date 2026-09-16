from unittest.mock import MagicMock

import pytest

from revision_service import ObjectInput, ReinforcementInput, validate_batch

pytestmark = pytest.mark.unit

_BUILDING_ID = "B01"
_RECTANGULAR_COLUMN_DIM = {"shape": "rectangular", "width": 400, "depth": 400}


def _mock_session(
    *,
    floor_names: list[tuple[str, str]],
    zone_labels: list[tuple[str, str]],
    mat_names: list[tuple[str, str, str]],
    sect_labels: list[tuple[str, str, str, dict]],
    barspec_labels: list[tuple[str, str]],
) -> MagicMock:
    """floor_names/zone_labels: [(id, name)]. sect_labels: [(sect_id,
    sect_label, obj_type, dim)]. mat_names: [(id, name, mat_type)].
    barspec_labels: [(id, name)]."""
    session = MagicMock()
    session.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=floor_names)),
        MagicMock(all=MagicMock(return_value=zone_labels)),
        MagicMock(all=MagicMock(return_value=sect_labels)),
        MagicMock(all=MagicMock(return_value=mat_names)),
        MagicMock(all=MagicMock(return_value=barspec_labels)),
    ]
    return session


def _valid_column() -> ObjectInput:
    return ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C1 - 400x400 column",
        mat_name="concrete K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        reinforcements=[
            ReinforcementInput(
                barspec_label="D16 deformed",
                bar_role="longitudinal",
                bar_count=8,
                bar_len=3000,
            ),
            ReinforcementInput(
                barspec_label="D10 deformed",
                bar_role="transverse",
                bar_count=20,
                bar_len=1200,
                bar_space=150,
                bar_hook_type="135deg",
            ),
        ],
    )


def _valid_session() -> MagicMock:
    return _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[("D16", "D16 deformed"), ("D10", "D10 deformed")],
    )


def test_rejects_nonexistent_floor_name() -> None:
    session = _mock_session(
        floor_names=[],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[("D16", "D16 deformed"), ("D10", "D10 deformed")],
    )

    problems, resolved = validate_batch(session, [_valid_column()], _BUILDING_ID)

    assert any(
        "floor_name 'ground floor' does not exist" in problem for problem in problems
    )
    assert resolved == []


def test_rejects_transverse_bar_missing_bar_space() -> None:
    session = _valid_session()
    obj = ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C1 - 400x400 column",
        mat_name="concrete K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        reinforcements=[
            ReinforcementInput(
                barspec_label="D10 deformed",
                bar_role="transverse",
                bar_count=20,
                bar_len=1200,
                bar_hook_type="135deg",
            ),
        ],
    )

    problems, _resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert any("bar_space is required" in problem for problem in problems)


def test_rejects_column_with_three_geometry_points() -> None:
    session = _valid_session()
    obj = ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C1 - 400x400 column",
        mat_name="concrete K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000], [0, 1000, 3000]],
    )

    problems, _resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert any("requires exactly 2 geometry_points" in problem for problem in problems)


def test_accepts_fully_valid_batch() -> None:
    session = _valid_session()

    problems, resolved = validate_batch(session, [_valid_column()], _BUILDING_ID)

    assert problems == []
    assert len(resolved) == 1
    assert resolved[0].floor_id == "F01"
    assert resolved[0].zone_id == "Z01"
    assert resolved[0].sect_id == "C1"
    assert resolved[0].mat_id == "K250"
    assert [bar.barspec_id for bar in resolved[0].reinforcements] == ["D16", "D10"]


def test_rejects_circular_section_missing_diameter() -> None:
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C2", "C2 - circular column", "column", {"shape": "circular"})],
        barspec_labels=[],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C2.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C2 - circular column",
        mat_name="concrete K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )

    problems, resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert any("requires diameter > 0" in problem for problem in problems)
    assert resolved == []


def test_accepts_circular_section_with_valid_diameter() -> None:
    # Steel, not concrete: isolates this test to the diameter check alone
    # rather than also having to satisfy VR-11's reinforcement cardinality.
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("S1", "structural steel", "steel")],
        sect_labels=[
            (
                "C2",
                "C2 - circular column",
                "column",
                {"shape": "circular", "diameter": 350},
            )
        ],
        barspec_labels=[],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C2.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C2 - circular column",
        mat_name="structural steel",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )

    problems, resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert problems == []
    assert resolved[0].sect_id == "C2"


def test_rejects_sect_label_with_mismatched_obj_type() -> None:
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[],
    )
    obj = ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="beam",  # C1's actual obj_type is "column"
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C1 - 400x400 column",
        mat_name="concrete K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )

    problems, resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert any(
        "sect_label='C1 - 400x400 column'" in problem and "does not exist" in problem
        for problem in problems
    )
    assert resolved == []


# --- VR-11: reinforcement cardinality by material type ------------------


def _column(*, mat_name: str, reinforcements: list[ReinforcementInput]) -> ObjectInput:
    return ObjectInput(
        is_new=True,
        obj_mark="C1.F01.001",
        obj_type="column",
        floor_name="ground floor",
        zone_label="Zone 1",
        sect_label="C1 - 400x400 column",
        mat_name=mat_name,
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
        reinforcements=reinforcements,
    )


def _one_bar() -> list[ReinforcementInput]:
    return [
        ReinforcementInput(
            barspec_label="D16 deformed",
            bar_role="longitudinal",
            bar_count=8,
            bar_len=3000,
        )
    ]


def test_vr11_rejects_concrete_object_with_zero_reinforcement_rows() -> None:
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[],
    )
    obj = _column(mat_name="concrete K250", reinforcements=[])

    problems, resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert any(
        "concrete objects require at least one reinforcement row" in problem
        for problem in problems
    )
    assert resolved == []


def test_vr11_accepts_concrete_object_with_one_reinforcement_row() -> None:
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("K250", "concrete K250", "concrete")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[("D16", "D16 deformed")],
    )
    obj = _column(mat_name="concrete K250", reinforcements=_one_bar())

    problems, _resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert problems == []


def test_vr11_accepts_steel_object_with_zero_reinforcement_rows() -> None:
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("S1", "structural steel", "steel")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[],
    )
    obj = _column(mat_name="structural steel", reinforcements=[])

    problems, _resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert problems == []


def test_vr11_accepts_steel_object_with_reinforcement_rows_too() -> None:
    # Not forbidden, just not required - a steel object may still carry
    # embedded rebar.
    session = _mock_session(
        floor_names=[("F01", "ground floor")],
        zone_labels=[("Z01", "Zone 1")],
        mat_names=[("S1", "structural steel", "steel")],
        sect_labels=[("C1", "C1 - 400x400 column", "column", _RECTANGULAR_COLUMN_DIM)],
        barspec_labels=[("D16", "D16 deformed")],
    )
    obj = _column(mat_name="structural steel", reinforcements=_one_bar())

    problems, _resolved = validate_batch(session, [obj], _BUILDING_ID)

    assert problems == []
