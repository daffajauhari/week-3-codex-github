from decimal import Decimal

import pytest

from models import BarSpec
from revision_service import ResolvedReinforcement, _compute_qty_bar, _compute_qty_sect

pytestmark = pytest.mark.unit


def _barspec(**overrides: object) -> BarSpec:
    defaults: dict[str, object] = {
        "barspec_id": "D16",
        "barspec_label": "D16 deformed BjTS 420",
        "barspec_dia": 16,
        "barspec_type": "deformed",
        "barspec_grade": "BjTS 420",
        "barspec_weight": 7850,
    }
    defaults.update(overrides)
    return BarSpec(**defaults)  # type: ignore[arg-type]


def test_rectangular_column_qty_sect_in_m3() -> None:
    qty_sect = _compute_qty_sect(
        "column",
        {"shape": "rectangular", "width": 400, "depth": 400},
        [[0, 0, 0], [0, 0, 3500]],
        "concrete",
        2400,
    )

    assert qty_sect == Decimal("0.56")


def test_circular_column_qty_sect_uses_pi_r_squared() -> None:
    qty_sect = _compute_qty_sect(
        "column",
        {"shape": "circular", "diameter": 350},
        [[0, 0, 0], [0, 0, 3000]],
        "concrete",
        2400,
    )

    assert qty_sect == Decimal("0.29")


def test_concrete_slab_qty_sect_uses_polygon_area() -> None:
    qty_sect = _compute_qty_sect(
        "slab",
        {"thickness": 150},
        [
            [0, 0, 3000],
            [4000, 0, 3000],
            [4000, 3000, 3000],
            [0, 3000, 3000],
        ],
        "concrete",
        2400,
    )

    assert qty_sect == Decimal("1.80")


def test_steel_beam_qty_sect_is_weight_not_volume() -> None:
    qty_sect = _compute_qty_sect(
        "beam",
        {"shape": "rectangular", "width": 200, "depth": 400},
        [[0, 0, 0], [4000, 0, 0]],
        "steel",
        7850,
    )

    assert qty_sect == Decimal("2512.00")


def test_steel_beam_qty_bar_from_its_own_reinforcement() -> None:
    barspec = _barspec()

    qty_bar = _compute_qty_bar(
        [
            ResolvedReinforcement(
                barspec_id="D16", bar_role="longitudinal", bar_count=4, bar_len=4000
            )
        ],
        {"D16": barspec},
    )

    assert qty_bar == Decimal("25.25")


def test_zero_reinforcement_rows_yields_zero_not_an_error() -> None:
    qty_bar = _compute_qty_bar([], {})

    assert qty_bar == Decimal("0.00")
