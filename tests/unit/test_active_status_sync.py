from unittest.mock import MagicMock

import pytest

from models import BarSpec, Identity, Material, Object, Reinforcement, Revision, Section
from revision_service import sync_active_status

pytestmark = pytest.mark.unit

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


def _previous_object() -> Object:
    return Object(
        obj_id="O-prev",
        obj_mark="C1.F01.001",
        stable_id="abc-123",
        rev_id="R1",
        change_status="added",
        obj_type="column",
        floor_id="F01",
        zone_id="Z01",
        sect_id="C1",
        mat_id="K250",
        geometry_points=[[0, 0, 0], [0, 0, 3000]],
    )


def _mock_session(
    *, identity_active: bool, with_bars: bool
) -> tuple[MagicMock, Identity]:
    session = MagicMock()
    revision = Revision(rev_id="R2", building_id="B01", rev_number=2)
    previous_revision = Revision(rev_id="R1", building_id="B01", rev_number=1)
    identity = Identity(stable_id="abc-123", is_active=identity_active)

    lookup_by_model = {Revision: revision, Identity: identity, Material: _MATERIAL}
    session.get.side_effect = lambda model, _id: lookup_by_model[model]
    session.execute.return_value.scalar_one.return_value = 1

    scalars_results = [
        MagicMock(first=MagicMock(return_value=previous_revision)),
        MagicMock(all=MagicMock(return_value=[_previous_object()])),
    ]
    bars: list[Reinforcement] = []
    if with_bars:
        bars = [
            Reinforcement(
                bar_id="bar-1",
                obj_id="O-prev",
                barspec_id="D16",
                bar_role="longitudinal",
                bar_count=8,
                bar_len=3000,
            )
        ]
        scalars_results.append(MagicMock(all=MagicMock(return_value=bars)))
        # _create_quantity's own lookups, only reached when the deletion
        # branch actually runs (identity_active=True).
        barspec = BarSpec(
            barspec_id="D16",
            barspec_label="D16 deformed BjTS 420",
            barspec_dia=16,
            barspec_type="deformed",
            barspec_grade="BjTS 420",
            barspec_weight=7850,
        )
        scalars_results.append(MagicMock(first=MagicMock(return_value=_SECTION)))
        scalars_results.append(MagicMock(all=MagicMock(return_value=[barspec])))
    session.scalars.side_effect = scalars_results

    return session, identity


def test_first_time_deletion_flags_object_and_deactivates_identity() -> None:
    session, identity = _mock_session(identity_active=True, with_bars=True)

    deleted = sync_active_status(
        session, building_id="B01", rev_id="R2", processed_stable_ids=set()
    )

    assert len(deleted) == 1
    assert deleted[0].change_status == "deleted"
    assert deleted[0].stable_id == "abc-123"
    assert identity.is_active is False


def test_already_deleted_object_produces_no_new_row() -> None:
    session, identity = _mock_session(identity_active=False, with_bars=False)

    deleted = sync_active_status(
        session, building_id="B01", rev_id="R2", processed_stable_ids=set()
    )

    assert deleted == []
    assert identity.is_active is False


def test_object_present_in_current_batch_is_not_flagged_deleted() -> None:
    session, _identity = _mock_session(identity_active=True, with_bars=False)

    deleted = sync_active_status(
        session,
        building_id="B01",
        rev_id="R2",
        processed_stable_ids={"abc-123"},
    )

    assert deleted == []
