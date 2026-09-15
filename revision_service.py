from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import BarSpec, Floor, Identity, Material, Section, Zone

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
