import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from database import engine, get_session
from ids import REVISION_ID, next_id
from models import Building, Object, Revision
from revision_service import (
    ObjectInput,
    ReinforcementInput,
    apply_explicit_deletions,
    assign_stable_ids,
    carry_forward_unchanged,
    determine_change_status,
    sync_active_status,
    validate_batch,
)
from schemas import (
    BulkUploadRequest,
    EditRevisionRequest,
    ObjectCreate,
    RevisionObjectResult,
    RevisionResponse,
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
        floor_id=payload.floor_id,
        zone_id=payload.zone_id,
        sect_id=payload.sect_id,
        mat_id=payload.mat_id,
        geometry_points=payload.geometry_points,
        reinforcements=[
            ReinforcementInput(
                barspec_id=bar.barspec_id,
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


@app.post(
    "/buildings/{building_id}/revisions/bulk",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def bulk_upload_revision(
    building_id: str,
    payload: BulkUploadRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RevisionResponse:
    # A single transaction covers the whole handler: nothing here calls
    # session.commit() until the very end, so any exception - a 404, a
    # rejected batch, or anything else - leaves the transaction uncommitted
    # and it rolls back automatically when the session closes.
    if session.get(Building, building_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )

    object_inputs = [_to_object_input(obj) for obj in payload.objects]

    problems = validate_batch(session, object_inputs)
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

    assignments = assign_stable_ids(session, object_inputs)

    results: list[RevisionObjectResult] = []
    processed_stable_ids: set[str] = set()
    for obj_input, assignment in zip(object_inputs, assignments, strict=True):
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
    "/buildings/{building_id}/revisions/edit",
    response_model=RevisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def edit_revision(
    building_id: str,
    payload: EditRevisionRequest,
    session: Annotated[Session, Depends(get_session)],
) -> RevisionResponse:
    if session.get(Building, building_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Building not found"
        )

    # Pre-Validation Gate is scoped only to changed_objects (D33/D34) -
    # deleted_stable_ids and the carry-forward step don't introduce any
    # new Human Input to validate.
    changed_inputs = [_to_object_input(obj) for obj in payload.changed_objects]

    problems = validate_batch(session, changed_inputs)
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

    assignments = assign_stable_ids(session, changed_inputs)

    results: list[RevisionObjectResult] = []
    touched_stable_ids: set[str] = set(payload.deleted_stable_ids)
    for obj_input, assignment in zip(changed_inputs, assignments, strict=True):
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
