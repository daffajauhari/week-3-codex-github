from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class ReinforcementCreate(BaseModel):
    barspec_id: str
    bar_role: str
    bar_count: int
    bar_len: int
    bar_space: int | None = None
    bar_hook_type: str | None = None


class ObjectCreate(BaseModel):
    is_new: bool
    obj_mark: str
    obj_type: Literal["col", "beam", "wall", "slab"]
    floor_id: str
    zone_id: str
    sect_id: str
    mat_id: str
    geometry_points: list[list[int]]
    reinforcements: list[ReinforcementCreate] = Field(default_factory=list)
    # Deliberately not part of the Human Input field list D8/Commit 13
    # otherwise call for (obj_id/rev_id/change_status are always
    # system-only) - but is_new=false has nothing else in the schema that
    # could tell Workflow 1 (D18) which existing Identity row to continue,
    # so a continuation submission must echo back the stable_id the system
    # previously assigned it. Forbidden on new objects: D6/D7 keep stable_id
    # assignment for new objects entirely system-generated (uuid4).
    stable_id: str | None = None

    @model_validator(mode="after")
    def _validate_stable_id(self) -> Self:
        if self.is_new and self.stable_id is not None:
            raise ValueError("stable_id must not be set when is_new is true")
        if not self.is_new and self.stable_id is None:
            raise ValueError("stable_id is required when is_new is false")
        return self


class BulkUploadRequest(BaseModel):
    objects: list[ObjectCreate]


class RevisionObjectResult(BaseModel):
    obj_id: str
    obj_mark: str
    stable_id: str
    change_status: str


class RevisionResponse(BaseModel):
    rev_id: str
    rev_number: int
    objects: list[RevisionObjectResult]
