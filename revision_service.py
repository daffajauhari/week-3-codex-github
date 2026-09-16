from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ids import OBJECT_ID, REINFORCEMENT_ID, next_id
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

_AXIS_POINT_TYPES = {"column", "beam", "footing"}
_BOUNDARY_POINT_TYPES = {"wall", "slab", "stair"}
_TRANSVERSE_ROLE = "transverse"


@dataclass
class ReinforcementInput:
    barspec_label: str
    bar_role: str
    bar_count: int
    bar_len: int
    bar_space: int | None = None
    bar_hook_type: str | None = None


@dataclass
class ObjectInput:
    """Client-facing shape (D44): every Project Configuration reference is
    a natural name, not a raw ID. validate_batch resolves these to real
    IDs, producing a ResolvedObject for Workflows 1-3 to consume."""

    is_new: bool
    obj_mark: str
    obj_type: str
    floor_name: str
    zone_label: str
    sect_label: str
    mat_name: str
    geometry_points: list[list[int]]
    reinforcements: list[ReinforcementInput] = field(default_factory=list)
    # Not part of the client-facing input schema for new objects (D6/D7: a
    # new stable_id is always system-generated). Required when is_new is
    # False so Workflow 1 knows which existing Identity row to look up.
    stable_id: str | None = None


@dataclass
class ResolvedReinforcement:
    barspec_id: str
    bar_role: str
    bar_count: int
    bar_len: int
    bar_space: int | None = None
    bar_hook_type: str | None = None


@dataclass
class ResolvedObject:
    """Same data as ObjectInput, but every Project Configuration reference
    is the real ID it resolved to (D44) - what Workflows 1-3 actually
    store on Object/Reinforcement rows."""

    is_new: bool
    obj_mark: str
    obj_type: str
    floor_id: str
    zone_id: str
    sect_id: str
    mat_id: str
    geometry_points: list[list[int]]
    reinforcements: list[ResolvedReinforcement] = field(default_factory=list)
    stable_id: str | None = None


@dataclass
class _SectionLookup:
    sect_id: str
    obj_type: str
    dim: dict[str, str | int]


@dataclass
class _Resolution:
    floor_by_name: dict[str, str]
    zone_by_label: dict[str, str]
    section_by_label: dict[str, _SectionLookup]
    mat_by_name: dict[str, str]
    barspec_by_label: dict[str, str]


def validate_batch(
    session: Session, objects: Sequence[ObjectInput], building_id: str
) -> tuple[list[str], list[ResolvedObject]]:
    """Pre-Validation Gate (D32).

    Resolves every natural-name reference (floor_name/zone_label scoped to
    building_id, sect_label+obj_type/mat_name/barspec_label globally -
    D44), then runs Contextual Completeness. Returns every problem found -
    never just the first - plus the resolved objects. The resolved list is
    only meaningful when there are no problems; the caller should reject
    the whole batch rather than act on a partial resolution.
    """
    ref_problems, resolution = _resolve_referential_existence(
        session, objects, building_id
    )
    problems = ref_problems + _check_contextual_completeness(objects, resolution)

    if problems:
        return problems, []
    return problems, _build_resolved_objects(objects, resolution)


def _resolve_referential_existence(
    session: Session, objects: Sequence[ObjectInput], building_id: str
) -> tuple[list[str], _Resolution]:
    problems: list[str] = []

    floor_names = {obj.floor_name for obj in objects}
    zone_labels = {obj.zone_label for obj in objects}
    sect_pairs = {(obj.sect_label, obj.obj_type) for obj in objects}
    mat_names = {obj.mat_name for obj in objects}
    barspec_labels = {
        bar.barspec_label for obj in objects for bar in obj.reinforcements
    }

    # floor_name/zone_label are scoped to this building (D44) - a name that
    # exists in a different building must not resolve here.
    floor_by_name = {
        floor_name: floor_id
        for floor_id, floor_name in session.execute(
            select(Floor.floor_id, Floor.floor_name).where(
                Floor.building_id == building_id
            )
        ).all()
    }
    zone_by_label = {
        zone_label: zone_id
        for zone_id, zone_label in session.execute(
            select(Zone.zone_id, Zone.zone_label).where(
                Zone.building_id == building_id
            )
        ).all()
    }
    # sect_label/mat_name/barspec_label have no building scope - resolved
    # globally.
    section_by_label = {
        sect_label: _SectionLookup(sect_id=sect_id, obj_type=obj_type, dim=dim)
        for sect_id, sect_label, obj_type, dim in session.execute(
            select(Section.sect_id, Section.sect_label, Section.obj_type, Section.dim)
        ).all()
    }
    mat_by_name = {
        mat_name: mat_id
        for mat_id, mat_name in session.execute(
            select(Material.mat_id, Material.mat_name)
        ).all()
    }
    barspec_by_label = {
        barspec_label: barspec_id
        for barspec_id, barspec_label in session.execute(
            select(BarSpec.barspec_id, BarSpec.barspec_label)
        ).all()
    }

    for floor_name in sorted(floor_names - floor_by_name.keys()):
        problems.append(f"floor_name '{floor_name}' does not exist")
    for zone_label in sorted(zone_labels - zone_by_label.keys()):
        problems.append(f"zone_label '{zone_label}' does not exist")
    for mat_name in sorted(mat_names - mat_by_name.keys()):
        problems.append(f"mat_name '{mat_name}' does not exist")
    for barspec_label in sorted(barspec_labels - barspec_by_label.keys()):
        problems.append(f"barspec_label '{barspec_label}' does not exist")
    for sect_label, obj_type in sorted(sect_pairs):
        section = section_by_label.get(sect_label)
        if section is None or section.obj_type != obj_type:
            problems.append(
                f"section (sect_label='{sect_label}', obj_type='{obj_type}') "
                "does not exist"
            )

    return problems, _Resolution(
        floor_by_name=floor_by_name,
        zone_by_label=zone_by_label,
        section_by_label=section_by_label,
        mat_by_name=mat_by_name,
        barspec_by_label=barspec_by_label,
    )


def _build_resolved_objects(
    objects: Sequence[ObjectInput], resolution: _Resolution
) -> list[ResolvedObject]:
    resolved_objects: list[ResolvedObject] = []
    for obj in objects:
        section = resolution.section_by_label[obj.sect_label]
        resolved_objects.append(
            ResolvedObject(
                is_new=obj.is_new,
                obj_mark=obj.obj_mark,
                obj_type=obj.obj_type,
                floor_id=resolution.floor_by_name[obj.floor_name],
                zone_id=resolution.zone_by_label[obj.zone_label],
                sect_id=section.sect_id,
                mat_id=resolution.mat_by_name[obj.mat_name],
                geometry_points=obj.geometry_points,
                reinforcements=[
                    ResolvedReinforcement(
                        barspec_id=resolution.barspec_by_label[bar.barspec_label],
                        bar_role=bar.bar_role,
                        bar_count=bar.bar_count,
                        bar_len=bar.bar_len,
                        bar_space=bar.bar_space,
                        bar_hook_type=bar.bar_hook_type,
                    )
                    for bar in obj.reinforcements
                ],
                stable_id=obj.stable_id,
            )
        )
    return resolved_objects


@dataclass
class StableIdAssignment:
    stable_id: str
    is_new: bool
    is_restored: bool


def assign_stable_ids(
    session: Session, objects: Sequence[ResolvedObject]
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
    obj_input: ResolvedObject,
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
        obj_id=next_id(session, *OBJECT_ID),
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
                bar_id=next_id(session, *REINFORCEMENT_ID),
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


def _has_changed(
    session: Session, previous: Object, obj_input: ResolvedObject
) -> bool:
    own_columns_changed = (
        previous.obj_type != obj_input.obj_type
        or previous.floor_id != obj_input.floor_id
        or previous.zone_id != obj_input.zone_id
        or previous.sect_id != obj_input.sect_id
        or previous.mat_id != obj_input.mat_id
        or previous.geometry_points != obj_input.geometry_points
    )
    return own_columns_changed or _reinforcements_changed(session, previous, obj_input)


def _reinforcement_signature(
    bar: Reinforcement | ResolvedReinforcement,
) -> tuple[str, str, int, int, int, str]:
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
    session: Session, previous: Object, obj_input: ResolvedObject
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
    own explicit deleted_stable_ids list instead (apply_explicit_deletions).
    Runs once after every object in the batch has been through Workflows
    1-2. Anything present in the previous revision's baseline but absent
    from processed_stable_ids is flagged deleted, unless it was already
    inactive - the guard against re-flagging the same deletion on every
    later revision (D17).
    """
    previous_objects = _get_previous_revision_objects(session, building_id, rev_id)

    deleted_objects: list[Object] = []
    for previous in previous_objects:
        if previous.stable_id in processed_stable_ids:
            continue

        identity = session.get(Identity, previous.stable_id)
        assert identity is not None
        if not identity.is_active:
            continue

        identity.is_active = False
        deleted_objects.append(_duplicate_object(session, previous, rev_id, "deleted"))

    return deleted_objects


def apply_explicit_deletions(
    session: Session, rev_id: str, deleted_stable_ids: Sequence[str]
) -> list[Object]:
    """Interactive Edit's explicit deletion step (D33, D34).

    Same end effect as Workflow 3's absence-based deletion, but triggered
    by an explicit stable_id list rather than inferred from what's missing
    from the payload - Interactive Edit never treats "not mentioned" as
    "deleted" (D33), so it needs this instead of sync_active_status.
    """
    deleted_objects: list[Object] = []
    for stable_id in deleted_stable_ids:
        identity = session.get(Identity, stable_id)
        if identity is None or not identity.is_active:
            continue

        previous = _get_previous_object(session, stable_id, rev_id)
        if previous is None:
            continue

        identity.is_active = False
        deleted_objects.append(_duplicate_object(session, previous, rev_id, "deleted"))

    return deleted_objects


def carry_forward_unchanged(
    session: Session, building_id: str, rev_id: str, touched_stable_ids: set[str]
) -> list[Object]:
    """Interactive Edit's carry-forward step (D33).

    Every stable_id from the previous revision's baseline that appears in
    neither changed_objects nor deleted_stable_ids (touched_stable_ids
    covers both) is duplicated forward as-is with change_status
    'unchanged', so a partial payload never silently drops an object -
    unlike Bulk Upload, Interactive Edit's absence never means deleted.
    """
    previous_objects = _get_previous_revision_objects(session, building_id, rev_id)

    return [
        _duplicate_object(session, previous, rev_id, "unchanged")
        for previous in previous_objects
        if previous.stable_id not in touched_stable_ids
    ]


def _get_previous_revision_objects(
    session: Session, building_id: str, rev_id: str
) -> Sequence[Object]:
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

    return session.scalars(
        select(Object).where(Object.rev_id == previous_revision.rev_id)
    ).all()


def _duplicate_object(
    session: Session, previous: Object, rev_id: str, change_status: str
) -> Object:
    new_object = Object(
        obj_id=next_id(session, *OBJECT_ID),
        obj_mark=previous.obj_mark,
        stable_id=previous.stable_id,
        rev_id=rev_id,
        change_status=change_status,
        obj_type=previous.obj_type,
        floor_id=previous.floor_id,
        zone_id=previous.zone_id,
        sect_id=previous.sect_id,
        mat_id=previous.mat_id,
        geometry_points=previous.geometry_points,
    )
    session.add(new_object)

    previous_bars = session.scalars(
        select(Reinforcement).where(Reinforcement.obj_id == previous.obj_id)
    ).all()
    for bar in previous_bars:
        session.add(
            Reinforcement(
                bar_id=next_id(session, *REINFORCEMENT_ID),
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


def _check_contextual_completeness(
    objects: Sequence[ObjectInput], resolution: _Resolution
) -> list[str]:
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

        # Referential Existence already reports a missing/mismatched
        # section - only check shape when it actually resolved.
        section = resolution.section_by_label.get(obj.sect_label)
        if section is not None and section.obj_type == obj.obj_type:
            problems.extend(_check_dimension_shape(index, obj, section.dim))

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


def _check_dimension_shape(
    index: int, obj: ObjectInput, dim: dict[str, str | int]
) -> list[str]:
    """VR-10: Section.dimension shape, by obj_type.

    Rectangular (width+depth) or circular (diameter) for axis-point types
    (column/beam/footing); thickness for boundary-point types
    (wall/slab/stair). VR-10's own wording only names column/beam for the
    rectangular/circular case, but footing is axis-point per D47 and
    needs a shape to compute qty_sect the same way column/beam do - this
    treats that omission as a wording gap rather than excluding footing.
    """
    label = f"object[{index}] ({obj.obj_mark})"
    problems: list[str] = []

    if obj.obj_type in _AXIS_POINT_TYPES:
        shape = dim.get("shape")
        if shape == "rectangular":
            if not _is_positive_number(dim.get("width")):
                problems.append(f"{label}: section dimension requires width > 0")
            if not _is_positive_number(dim.get("depth")):
                problems.append(f"{label}: section dimension requires depth > 0")
        elif shape == "circular":
            if not _is_positive_number(dim.get("diameter")):
                problems.append(f"{label}: section dimension requires diameter > 0")
        else:
            problems.append(
                f"{label}: section dimension shape must be 'rectangular' or "
                f"'circular' for obj_type '{obj.obj_type}', got {shape!r}"
            )
    else:
        if not _is_positive_number(dim.get("thickness")):
            problems.append(f"{label}: section dimension requires thickness > 0")

    return problems


def _is_positive_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value > 0
