import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import engine, get_session
from ids import (
    BARSPEC_ID,
    BUILDING_ID,
    FLOOR_ID,
    GRID_ID,
    MATERIAL_ID,
    PROJECT_ID,
    REVISION_ID,
    SECTION_ID,
    ZONE_ID,
    next_id,
)
from models import (
    BarSpec,
    Building,
    Floor,
    Grid,
    Material,
    Object,
    Project,
    Quantity,
    Reinforcement,
    Revision,
    Section,
    Zone,
)
from revision_service import (
    ObjectInput,
    ReinforcementInput,
    apply_explicit_deletions,
    assign_stable_ids,
    carry_forward_unchanged,
    determine_change_status,
    sync_active_status,
    validate_batch,
    validate_section_dimension_shape,
)
from schemas import (
    BarSpecCreate,
    BarSpecResponse,
    BuildingCreate,
    BuildingResponse,
    BulkUploadRequest,
    EditRevisionRequest,
    FloorCreate,
    FloorResponse,
    GridCreate,
    GridResponse,
    MaterialCreate,
    MaterialResponse,
    ObjectCreate,
    ObjectDetail,
    ObjectListItem,
    ProjectCreate,
    ProjectResponse,
    QuantityDetail,
    ReinforcementDetail,
    RevisionListItem,
    RevisionObjectResult,
    RevisionResponse,
    SectionCreate,
    SectionResponse,
    ZoneCreate,
    ZoneResponse,
)

app = FastAPI()

frontend_origin = os.environ["FRONTEND_ORIGIN"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello() -> dict[str, str]:
    return {"message": "Backend is running"}


@app.get("/db-check")
def check_database() -> dict[str, str]:
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    return {
        "status": "connected",
        "database": database_name,
    }


def _to_object_input(payload: ObjectCreate) -> ObjectInput:
    return ObjectInput(
        is_new=payload.is_new,
        obj_mark=payload.obj_mark,
        obj_type=payload.obj_type,
        floor_name=payload.floor_name,
        zone_label=payload.zone_label,
        sect_label=payload.sect_label,
        mat_name=payload.mat_name,
        geometry_points=payload.geometry_points,
        reinforcements=[
            ReinforcementInput(
                barspec_label=bar.barspec_label,
                bar_role=bar.bar_role,
                bar_count=bar.bar_count,
                bar_len=bar.bar_len,
                bar_space=bar.bar_space,
                bar_hook_type=bar.bar_hook_type,
            )
            for bar in payload.reinforcements
        ],
        stable_id=payload.stable_id,
    )


def _to_result(obj: Object) -> RevisionObjectResult:
    return RevisionObjectResult(
        obj_id=obj.obj_id,
        obj_mark=obj.obj_mark,
        stable_id=obj.stable_id,
        change_status=obj.change_status,
    )


def _next_rev_number(session: Session, building_id: str) -> int:
    max_rev_number = session.scalars(
        select(func.max(Revision.rev_number)).where(
            Revision.building_id == building_id
        )
    ).one()
    return 0 if max_rev_number is None else max_rev_number + 1


def _require_building_in_project(
    session: Session, project_id: str, building_id: str
) -> Building:
    """D37: validate the full /projects/{project_id}/buildings/{building_id}
    path chain - 404 if the building doesn't exist at all, 400 if it exists
    but belongs to a different project."""
    building = session.get(Building, building_id)
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )
    if building.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building does not belong to this project",
        )
    return building


@app.post(
    "/projects/{project_id}/buildings/{building_id}/revisions/bulk",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def bulk_upload_revision(
    project_id: str,
    building_id: str,
    payload: BulkUploadRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RevisionResponse:
    # A single transaction covers the whole handler: nothing here calls
    # session.commit() until the very end, so any exception - a 404, a
    # rejected batch, or anything else - leaves the transaction uncommitted
    # and it rolls back automatically when the session closes.
    _require_building_in_project(session, project_id, building_id)

    object_inputs = [_to_object_input(obj) for obj in payload.objects]

    problems, resolved_objects = validate_batch(session, object_inputs, building_id)
    if problems:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problems
        )

    revision = Revision(
        rev_id=next_id(session, *REVISION_ID),
        building_id=building_id,
        rev_number=_next_rev_number(session, building_id),
    )
    session.add(revision)
    session.flush()

    assignments = assign_stable_ids(session, resolved_objects)

    results: list[RevisionObjectResult] = []
    processed_stable_ids: set[str] = set()
    for obj_input, assignment in zip(resolved_objects, assignments, strict=True):
        new_object = determine_change_status(
            session, obj_input, assignment, revision.rev_id
        )
        processed_stable_ids.add(assignment.stable_id)
        results.append(_to_result(new_object))

    deleted_objects = sync_active_status(
        session, building_id, revision.rev_id, processed_stable_ids
    )
    results.extend(_to_result(obj) for obj in deleted_objects)

    session.commit()

    return RevisionResponse(
        rev_id=revision.rev_id, rev_number=revision.rev_number, objects=results
    )


@app.post(
    "/projects/{project_id}/buildings/{building_id}/revisions/edit",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def edit_revision(
    project_id: str,
    building_id: str,
    payload: EditRevisionRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RevisionResponse:
    _require_building_in_project(session, project_id, building_id)

    # Pre-Validation Gate is scoped only to changed_objects (D33/D34) -
    # deleted_stable_ids and the carry-forward step don't introduce any
    # new Human Input to validate.
    changed_inputs = [_to_object_input(obj) for obj in payload.changed_objects]

    problems, resolved_objects = validate_batch(session, changed_inputs, building_id)
    if problems:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problems
        )

    revision = Revision(
        rev_id=next_id(session, *REVISION_ID),
        building_id=building_id,
        rev_number=_next_rev_number(session, building_id),
    )
    session.add(revision)
    session.flush()

    assignments = assign_stable_ids(session, resolved_objects)

    results: list[RevisionObjectResult] = []
    touched_stable_ids: set[str] = set(payload.deleted_stable_ids)
    for obj_input, assignment in zip(resolved_objects, assignments, strict=True):
        new_object = determine_change_status(
            session, obj_input, assignment, revision.rev_id
        )
        touched_stable_ids.add(assignment.stable_id)
        results.append(_to_result(new_object))

    deleted_objects = apply_explicit_deletions(
        session, revision.rev_id, payload.deleted_stable_ids
    )
    results.extend(_to_result(obj) for obj in deleted_objects)

    carried_objects = carry_forward_unchanged(
        session, building_id, revision.rev_id, touched_stable_ids
    )
    results.extend(_to_result(obj) for obj in carried_objects)

    session.commit()

    return RevisionResponse(
        rev_id=revision.rev_id, rev_number=revision.rev_number, objects=results
    )


# --- Project Configuration (Commit 22, D38) ----------------------------
#
# No new synthetic data is generated here - these endpoints are for user
# input going forward, existing seeded rows stay as-is.


def _commit_or_conflict(session: Session, conflict_detail: str) -> None:
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=conflict_detail
        ) from None


def _require_project(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@app.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
def create_project(
    payload: ProjectCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ProjectResponse:
    project = Project(
        project_id=next_id(session, *PROJECT_ID), project_name=payload.project_name
    )
    session.add(project)
    _commit_or_conflict(session, "project_name already exists")
    return ProjectResponse.model_validate(project)


@app.post(
    "/projects/{project_id}/buildings",
    response_model=BuildingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_building(
    project_id: str,
    payload: BuildingCreate,
    session: Annotated[Session, Depends(get_session)],
) -> BuildingResponse:
    _require_project(session, project_id)

    building = Building(
        building_id=next_id(session, *BUILDING_ID),
        building_name=payload.building_name,
        project_id=project_id,
    )
    session.add(building)
    _commit_or_conflict(session, "building_name already exists")
    return BuildingResponse.model_validate(building)


@app.post(
    "/projects/{project_id}/buildings/{building_id}/floors",
    response_model=FloorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_floor(
    project_id: str,
    building_id: str,
    payload: FloorCreate,
    session: Annotated[Session, Depends(get_session)],
) -> FloorResponse:
    _require_building_in_project(session, project_id, building_id)

    floor = Floor(
        floor_id=next_id(session, *FLOOR_ID),
        floor_name=payload.floor_name,
        elevation=payload.elevation,
        building_id=building_id,
    )
    session.add(floor)
    _commit_or_conflict(session, "floor_name already exists in this building")
    return FloorResponse.model_validate(floor)


@app.post(
    "/projects/{project_id}/buildings/{building_id}/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_zone(
    project_id: str,
    building_id: str,
    payload: ZoneCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ZoneResponse:
    _require_building_in_project(session, project_id, building_id)

    zone = Zone(
        zone_id=next_id(session, *ZONE_ID),
        zone_label=payload.zone_label,
        pour_seq=payload.pour_seq,
        building_id=building_id,
    )
    session.add(zone)
    _commit_or_conflict(session, "zone_label already exists in this building")
    return ZoneResponse.model_validate(zone)


@app.post(
    "/projects/{project_id}/buildings/{building_id}/grid",
    response_model=GridResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_grid(
    project_id: str,
    building_id: str,
    payload: GridCreate,
    session: Annotated[Session, Depends(get_session)],
) -> GridResponse:
    _require_building_in_project(session, project_id, building_id)

    grid = Grid(
        grid_id=next_id(session, *GRID_ID),
        grid_label=payload.grid_label,
        grid_axis=payload.grid_axis,
        grid_coord=payload.grid_coord,
        building_id=building_id,
    )
    session.add(grid)
    _commit_or_conflict(
        session, "grid_label + grid_axis already exists in this building"
    )
    return GridResponse.model_validate(grid)


@app.post(
    "/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED
)
def create_material(
    payload: MaterialCreate,
    session: Annotated[Session, Depends(get_session)],
) -> MaterialResponse:
    material = Material(
        mat_id=next_id(session, *MATERIAL_ID),
        mat_name=payload.mat_name,
        mat_type=payload.mat_type,
        mat_strength=payload.mat_strength,
        mat_weight=payload.mat_weight,
    )
    session.add(material)
    _commit_or_conflict(session, "mat_name already exists")
    return MaterialResponse.model_validate(material)


@app.post(
    "/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED
)
def create_section(
    payload: SectionCreate,
    session: Annotated[Session, Depends(get_session)],
) -> SectionResponse:
    problems = validate_section_dimension_shape(payload.obj_type, payload.dimension)
    if problems:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=problems
        )

    section = Section(
        sect_id=next_id(session, *SECTION_ID),
        sect_label=payload.sect_label,
        obj_type=payload.obj_type,
        dim=payload.dimension,
    )
    session.add(section)
    _commit_or_conflict(session, "sect_label already exists")
    return SectionResponse.model_validate(section)


@app.post(
    "/barspec", response_model=BarSpecResponse, status_code=status.HTTP_201_CREATED
)
def create_barspec(
    payload: BarSpecCreate,
    session: Annotated[Session, Depends(get_session)],
) -> BarSpecResponse:
    barspec = BarSpec(
        barspec_id=next_id(session, *BARSPEC_ID),
        barspec_label=payload.barspec_label,
        barspec_dia=payload.barspec_dia,
        barspec_type=payload.barspec_type,
        barspec_grade=payload.barspec_grade,
        barspec_weight=payload.barspec_weight,
    )
    session.add(barspec)
    _commit_or_conflict(session, "barspec_label already exists")
    return BarSpecResponse.model_validate(barspec)


# --- Browsing (Commit 23, D39) -------------------------------------------
#
# Project -> Building -> Revision -> Object, list/detail responses resolve
# foreign keys to their descriptive values rather than bare IDs.


def _require_revision_in_building(
    session: Session, building_id: str, rev_id: str
) -> Revision:
    revision = session.get(Revision, rev_id)
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )
    if revision.building_id != building_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revision does not belong to this building",
        )
    return revision


def _require_object_in_revision(session: Session, rev_id: str, obj_id: str) -> Object:
    obj = session.get(Object, obj_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Object not found"
        )
    if obj.rev_id != rev_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Object does not belong to this revision",
        )
    return obj


@app.get("/projects", response_model=list[ProjectResponse])
def list_projects(
    session: Annotated[Session, Depends(get_session)],
) -> list[ProjectResponse]:
    projects = session.scalars(select(Project).order_by(Project.project_id)).all()
    return [ProjectResponse.model_validate(project) for project in projects]


@app.get(
    "/projects/{project_id}/buildings", response_model=list[BuildingResponse]
)
def list_buildings(
    project_id: str, session: Annotated[Session, Depends(get_session)]
) -> list[BuildingResponse]:
    _require_project(session, project_id)
    buildings = session.scalars(
        select(Building)
        .where(Building.project_id == project_id)
        .order_by(Building.building_id)
    ).all()
    return [BuildingResponse.model_validate(building) for building in buildings]


@app.get(
    "/projects/{project_id}/buildings/{building_id}/revisions",
    response_model=list[RevisionListItem],
)
def list_revisions(
    project_id: str,
    building_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> list[RevisionListItem]:
    _require_building_in_project(session, project_id, building_id)
    revisions = session.scalars(
        select(Revision)
        .where(Revision.building_id == building_id)
        .order_by(Revision.rev_number)
    ).all()
    return [RevisionListItem.model_validate(revision) for revision in revisions]


@app.get(
    "/projects/{project_id}/buildings/{building_id}/revisions/{rev_id}/objects",
    response_model=list[ObjectListItem],
)
def list_objects(
    project_id: str,
    building_id: str,
    rev_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> list[ObjectListItem]:
    _require_building_in_project(session, project_id, building_id)
    _require_revision_in_building(session, building_id, rev_id)

    objects = session.scalars(
        select(Object).where(Object.rev_id == rev_id).order_by(Object.obj_mark)
    ).all()

    floor_names = {
        floor.floor_id: floor.floor_name for floor in session.scalars(select(Floor)).all()
    }
    zone_labels = {
        zone.zone_id: zone.zone_label for zone in session.scalars(select(Zone)).all()
    }
    sect_labels = {
        (section.sect_id, section.obj_type): section.sect_label
        for section in session.scalars(select(Section)).all()
    }
    mat_names = {
        material.mat_id: material.mat_name
        for material in session.scalars(select(Material)).all()
    }

    return [
        ObjectListItem(
            obj_id=obj.obj_id,
            obj_mark=obj.obj_mark,
            stable_id=obj.stable_id,
            obj_type=obj.obj_type,
            change_status=obj.change_status,
            floor_name=floor_names.get(obj.floor_id, obj.floor_id),
            zone_label=zone_labels.get(obj.zone_id, obj.zone_id),
            sect_label=sect_labels.get((obj.sect_id, obj.obj_type), obj.sect_id),
            mat_name=mat_names.get(obj.mat_id, obj.mat_id),
        )
        for obj in objects
    ]


@app.get(
    "/projects/{project_id}/buildings/{building_id}/revisions/{rev_id}/objects/{obj_id}",
    response_model=ObjectDetail,
)
def get_object_detail(
    project_id: str,
    building_id: str,
    rev_id: str,
    obj_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ObjectDetail:
    _require_building_in_project(session, project_id, building_id)
    _require_revision_in_building(session, building_id, rev_id)
    obj = _require_object_in_revision(session, rev_id, obj_id)

    floor = session.get(Floor, obj.floor_id)
    zone = session.get(Zone, obj.zone_id)
    section = session.scalars(
        select(Section).where(
            Section.sect_id == obj.sect_id, Section.obj_type == obj.obj_type
        )
    ).first()
    material = session.get(Material, obj.mat_id)
    assert floor is not None
    assert zone is not None
    assert section is not None
    assert material is not None

    bars = session.scalars(
        select(Reinforcement).where(Reinforcement.obj_id == obj.obj_id)
    ).all()
    barspec_by_id = {
        barspec.barspec_id: barspec for barspec in session.scalars(select(BarSpec)).all()
    }
    reinforcements = [
        ReinforcementDetail(
            bar_id=bar.bar_id,
            barspec_label=barspec_by_id[bar.barspec_id].barspec_label,
            barspec_dia=barspec_by_id[bar.barspec_id].barspec_dia,
            barspec_grade=barspec_by_id[bar.barspec_id].barspec_grade,
            bar_role=bar.bar_role,
            bar_count=bar.bar_count,
            bar_len=bar.bar_len,
            bar_space=bar.bar_space,
            bar_hook_type=bar.bar_hook_type,
        )
        for bar in bars
    ]

    quantity_row = session.scalars(
        select(Quantity).where(Quantity.obj_id == obj.obj_id)
    ).first()
    quantity = (
        QuantityDetail(qty_sect=quantity_row.qty_sect, qty_bar=quantity_row.qty_bar)
        if quantity_row is not None
        else None
    )

    return ObjectDetail(
        obj_id=obj.obj_id,
        obj_mark=obj.obj_mark,
        stable_id=obj.stable_id,
        obj_type=obj.obj_type,
        change_status=obj.change_status,
        floor_name=floor.floor_name,
        zone_label=zone.zone_label,
        sect_label=section.sect_label,
        dimension=section.dim,
        mat_name=material.mat_name,
        geometry_points=obj.geometry_points,
        reinforcements=reinforcements,
        quantity=quantity,
    )
