from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import (
    BarSpec,
    Floor,
    Identity,
    Material,
    Object,
    Reinforcement,
    Revision,
    Section,
    Zone,
)

_AXIS_POINT_TYPES = {"col", "beam"}
_BOUNDARY_POINT_TYPES = {"wall", "slab"}
_TRANSVERSE_ROLE = "transverse"


@dataclass
class ReinforcementInput:
    barspec_id: str
    bar_role: str
    bar_count: int
    bar_len: int
    bar_space: int | None = None
    bar_hook_type: str | None = None


@dataclass
class ObjectInput:
    is_new: bool
    obj_mark: str
    obj_type: str
    floor_id: str
    zone_id: str
    sect_id: str
    mat_id: str
    geometry_points: list[list[int]]
    reinforcements: list[ReinforcementInput] = field(default_factory=list)
    # Not part of the client-facing input schema for new objects (D6/D7: a
    # new stable_id is always system-generated). Required when is_new is
    # False so Workflow 1 knows which existing Identity row to look up.
    stable_id: str | None = None


def validate_batch(session: Session, objects: Sequence[ObjectInput]) -> list[str]:
    """Pre-Validation Gate (D29).

    Runs Referential Existence then Contextual Completeness against the
    whole batch and returns every problem found - never just the first -
    so the caller can reject the batch with a complete list.
    """
    problems = _check_referential_existence(session, objects)
    problems.extend(_check_contextual_completeness(objects))
    return problems


def _check_referential_existence(
    session: Session, objects: Sequence[ObjectInput]
) -> list[str]:
    problems: list[str] = []

    floor_ids = {obj.floor_id for obj in objects}
    zone_ids = {obj.zone_id for obj in objects}
    mat_ids = {obj.mat_id for obj in objects}
    sect_pairs = {(obj.sect_id, obj.obj_type) for obj in objects}
    barspec_ids = {bar.barspec_id for obj in objects for bar in obj.reinforcements}

    existing_floor_ids = set(session.scalars(select(Floor.floor_id)).all())
    existing_zone_ids = set(session.scalars(select(Zone.zone_id)).all())
    existing_mat_ids = set(session.scalars(select(Material.mat_id)).all())
    existing_sect_pairs = {
        (sect_id, obj_type)
        for sect_id, obj_type in session.execute(
            select(Section.sect_id, Section.obj_type)
        ).all()
    }
    existing_barspec_ids = set(session.scalars(select(BarSpec.barspec_id)).all())

    for floor_id in sorted(floor_ids - existing_floor_ids):
        problems.append(f"floor_id '{floor_id}' does not exist")
    for zone_id in sorted(zone_ids - existing_zone_ids):
        problems.append(f"zone_id '{zone_id}' does not exist")
    for mat_id in sorted(mat_ids - existing_mat_ids):
        problems.append(f"mat_id '{mat_id}' does not exist")
    for sect_id, obj_type in sorted(sect_pairs - existing_sect_pairs):
        problems.append(
            f"section (sect_id='{sect_id}', obj_type='{obj_type}') does not exist"
        )
    for barspec_id in sorted(barspec_ids - existing_barspec_ids):
        problems.append(f"barspec_id '{barspec_id}' does not exist")

    return problems


@dataclass
class StableIdAssignment:
    stable_id: str
    is_new: bool
    is_restored: bool


def assign_stable_ids(
    session: Session, objects: Sequence[ObjectInput]
) -> list[StableIdAssignment]:
    """Workflow 1: Stable ID Assignment (D18).

    Only touches Identity - it never creates Object rows. Returns one
    assignment per input object, in order.
    """
    assignments: list[StableIdAssignment] = []

    for obj in objects:
        if obj.is_new:
            stable_id = str(uuid4())
            session.add(Identity(stable_id=stable_id, is_active=True))
            assignments.append(
                StableIdAssignment(stable_id=stable_id, is_new=True, is_restored=False)
            )
            continue

        if obj.stable_id is None:
            raise ValueError(
                f"object '{obj.obj_mark}' has is_new=False but no stable_id"
            )

        identity = session.get(Identity, obj.stable_id)
        if identity is None:
            raise ValueError(
                f"object '{obj.obj_mark}' references unknown stable_id "
                f"'{obj.stable_id}'"
            )

        was_inactive = not identity.is_active
        if was_inactive:
            identity.is_active = True

        assignments.append(
            StableIdAssignment(
                stable_id=identity.stable_id,
                is_new=False,
                is_restored=was_inactive,
            )
        )

    return assignments


def determine_change_status(
    session: Session,
    obj_input: ObjectInput,
    assignment: StableIdAssignment,
    rev_id: str,
) -> Object:
    """Workflow 2: Change Status Determination (D18, D19).

    Inserts a fresh Object row (and its Reinforcement rows) for this input
    with the resolved change_status, and returns the inserted Object. Runs
    unconditionally, even for objects that come out 'unchanged' - every
    object gets a full snapshot row every revision (D9).
    """
    if assignment.is_new:
        change_status = "added"
    elif assignment.is_restored:
        change_status = "restored"
    else:
        previous = _get_previous_object(session, assignment.stable_id, rev_id)
        if previous is None or _has_changed(session, previous, obj_input):
            change_status = "modified"
        else:
            change_status = "unchanged"

    new_object = Object(
        obj_id=str(uuid4()),
        obj_mark=obj_input.obj_mark,
        stable_id=assignment.stable_id,
        rev_id=rev_id,
        change_status=change_status,
        obj_type=obj_input.obj_type,
        floor_id=obj_input.floor_id,
        zone_id=obj_input.zone_id,
        sect_id=obj_input.sect_id,
        mat_id=obj_input.mat_id,
        geometry_points=obj_input.geometry_points,
    )
    session.add(new_object)

    for bar in obj_input.reinforcements:
        session.add(
            Reinforcement(
                bar_id=str(uuid4()),
                obj_id=new_object.obj_id,
                barspec_id=bar.barspec_id,
                bar_role=bar.bar_role,
                bar_count=bar.bar_count,
                bar_len=bar.bar_len,
                bar_space=bar.bar_space,
                bar_hook_type=bar.bar_hook_type,
            )
        )

    return new_object


def _get_previous_object(
    session: Session, stable_id: str, rev_id: str
) -> Object | None:
    current_revision = session.get(Revision, rev_id)
    assert current_revision is not None

    previous_revision = session.scalars(
        select(Revision).where(
            Revision.building_id == current_revision.building_id,
            Revision.rev_number == current_revision.rev_number - 1,
        )
    ).first()
    if previous_revision is None:
        return None

    return session.scalars(
        select(Object).where(
            Object.stable_id == stable_id,
            Object.rev_id == previous_revision.rev_id,
        )
    ).first()


def _has_changed(session: Session, previous: Object, obj_input: ObjectInput) -> bool:
    own_columns_changed = (
        previous.obj_type != obj_input.obj_type
        or previous.floor_id != obj_input.floor_id
        or previous.zone_id != obj_input.zone_id
        or previous.sect_id != obj_input.sect_id
        or previous.mat_id != obj_input.mat_id
        or previous.geometry_points != obj_input.geometry_points
    )
    return own_columns_changed or _reinforcements_changed(session, previous, obj_input)


class _HasBarFields(Protocol):
    bar_role: str
    barspec_id: str
    bar_count: int
    bar_len: int
    bar_space: int | None
    bar_hook_type: str | None


def _reinforcement_signature(bar: _HasBarFields) -> tuple[str, str, int, int, int, str]:
    # bar_space/bar_hook_type are optional (VR-06); normalize None to a
    # sentinel outside the real value range so tuples stay sortable without
    # comparing None to int/str.
    return (
        bar.bar_role,
        bar.barspec_id,
        bar.bar_count,
        bar.bar_len,
        bar.bar_space if bar.bar_space is not None else -1,
        bar.bar_hook_type or "",
    )


def _reinforcements_changed(
    session: Session, previous: Object, obj_input: ObjectInput
) -> bool:
    previous_bars = session.scalars(
        select(Reinforcement).where(Reinforcement.obj_id == previous.obj_id)
    ).all()

    previous_signature = sorted(
        _reinforcement_signature(bar) for bar in previous_bars
    )
    incoming_signature = sorted(
        _reinforcement_signature(bar) for bar in obj_input.reinforcements
    )
    return previous_signature != incoming_signature


def sync_active_status(
    session: Session, building_id: str, rev_id: str, processed_stable_ids: set[str]
) -> list[Object]:
    """Workflow 3: Active Status Sync (D17, D18).

    Bulk Upload only (D33) - Interactive Edit handles deletion through its
    own explicit deleted_stable_ids list instead. Runs once after every
    object in the batch has been through Workflows 1-2. Anything present
    in the previous revision's baseline but absent from
    processed_stable_ids is flagged deleted, unless it was already
    inactive - the guard against re-flagging the same deletion on every
    later revision (D17).
    """
    current_revision = session.get(Revision, rev_id)
    assert current_revision is not None

    previous_revision = session.scalars(
        select(Revision).where(
            Revision.building_id == building_id,
            Revision.rev_number == current_revision.rev_number - 1,
        )
    ).first()
    if previous_revision is None:
        return []

    previous_objects = session.scalars(
        select(Object).where(Object.rev_id == previous_revision.rev_id)
    ).all()

    deleted_objects: list[Object] = []
    for previous in previous_objects:
        if previous.stable_id in processed_stable_ids:
            continue

        identity = session.get(Identity, previous.stable_id)
        assert identity is not None
        if not identity.is_active:
            continue

        identity.is_active = False

        deleted_object = Object(
            obj_id=str(uuid4()),
            obj_mark=previous.obj_mark,
            stable_id=previous.stable_id,
            rev_id=rev_id,
            change_status="deleted",
            obj_type=previous.obj_type,
            floor_id=previous.floor_id,
            zone_id=previous.zone_id,
            sect_id=previous.sect_id,
            mat_id=previous.mat_id,
            geometry_points=previous.geometry_points,
        )
        session.add(deleted_object)

        previous_bars = session.scalars(
            select(Reinforcement).where(Reinforcement.obj_id == previous.obj_id)
        ).all()
        for bar in previous_bars:
            session.add(
                Reinforcement(
                    bar_id=str(uuid4()),
                    obj_id=deleted_object.obj_id,
                    barspec_id=bar.barspec_id,
                    bar_role=bar.bar_role,
                    bar_count=bar.bar_count,
                    bar_len=bar.bar_len,
                    bar_space=bar.bar_space,
                    bar_hook_type=bar.bar_hook_type,
                )
            )

        deleted_objects.append(deleted_object)

    return deleted_objects


def _check_contextual_completeness(objects: Sequence[ObjectInput]) -> list[str]:
    problems: list[str] = []

    for index, obj in enumerate(objects):
        point_count = len(obj.geometry_points)
        if obj.obj_type in _AXIS_POINT_TYPES and point_count != 2:
            problems.append(
                f"object[{index}] ({obj.obj_mark}): obj_type '{obj.obj_type}' "
                f"requires exactly 2 geometry_points, got {point_count}"
            )
        elif obj.obj_type in _BOUNDARY_POINT_TYPES and point_count < 3:
            problems.append(
                f"object[{index}] ({obj.obj_mark}): obj_type '{obj.obj_type}' "
                f"requires at least 3 geometry_points, got {point_count}"
            )

        for bar_index, bar in enumerate(obj.reinforcements):
            if bar.bar_role != _TRANSVERSE_ROLE:
                continue
            if bar.bar_space is None:
                problems.append(
                    f"object[{index}] ({obj.obj_mark}) reinforcement[{bar_index}]: "
                    "bar_space is required when bar_role='transverse'"
                )
            if bar.bar_hook_type is None:
                problems.append(
                    f"object[{index}] ({obj.obj_mark}) reinforcement[{bar_index}]: "
                    "bar_hook_type is required when bar_role='transverse'"
                )

    return problems
