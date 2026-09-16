from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    project_name: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Building(Base):
    __tablename__ = "buildings"

    building_id: Mapped[str] = mapped_column(String, primary_key=True)
    building_name: Mapped[str | None] = mapped_column(String)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.project_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Section(Base):
    __tablename__ = "sections"

    sect_id: Mapped[str] = mapped_column(String, primary_key=True)
    obj_type: Mapped[str] = mapped_column(String)
    dim: Mapped[dict[str, str | int]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "obj_type IN "
            "('column', 'beam', 'wall', 'slab', 'footing', 'stair')",
            name="ck_sections_obj_type",
        ),
        UniqueConstraint(
            "sect_id",
            "obj_type",
            name="uq_sections_id_type",
        ),
    )


class Material(Base):
    __tablename__ = "materials"

    mat_id: Mapped[str] = mapped_column(String, primary_key=True)
    mat_name: Mapped[str] = mapped_column(String)
    mat_type: Mapped[str] = mapped_column(String)
    mat_strength: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class BarSpec(Base):
    __tablename__ = "barspec"

    barspec_id: Mapped[str] = mapped_column(String, primary_key=True)
    barspec_dia: Mapped[int] = mapped_column(Integer, nullable=False)
    barspec_type: Mapped[str] = mapped_column(String, nullable=False)
    barspec_grade: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Zone(Base):
    __tablename__ = "zones"

    zone_id: Mapped[str] = mapped_column(String, primary_key=True)
    pour_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    building_id: Mapped[str] = mapped_column(
        String, ForeignKey("buildings.building_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Floor(Base):
    __tablename__ = "floors"

    floor_id: Mapped[str] = mapped_column(String, primary_key=True)
    floor_name: Mapped[str] = mapped_column(String, nullable=False)
    elevation: Mapped[int] = mapped_column(Integer, nullable=False)
    building_id: Mapped[str] = mapped_column(
        String, ForeignKey("buildings.building_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Grid(Base):
    __tablename__ = "grid"

    grid_id: Mapped[str] = mapped_column(String, primary_key=True)
    building_id: Mapped[str] = mapped_column(
        String, ForeignKey("buildings.building_id"), nullable=False
    )
    grid_label: Mapped[str] = mapped_column(String, nullable=False)
    grid_axis: Mapped[str] = mapped_column(String, nullable=False)
    grid_coord: Mapped[dict[str, str | int]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "grid_label",
            "grid_axis",
            name="uq_grid_building_label_axis",
        ),
    )


class Revision(Base):
    __tablename__ = "revisions"

    rev_id: Mapped[str] = mapped_column(String, primary_key=True)
    building_id: Mapped[str] = mapped_column(
        String, ForeignKey("buildings.building_id"), nullable=False
    )
    rev_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "rev_number",
            name="uq_revisions_building_rev_number",
        ),
    )


class Identity(Base):
    __tablename__ = "identities"

    stable_id: Mapped[str] = mapped_column(String, primary_key=True)
    ifc_global_id: Mapped[str | None] = mapped_column(String, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class Object(Base):
    __tablename__ = "objects"

    obj_id: Mapped[str] = mapped_column(String, primary_key=True)
    obj_mark: Mapped[str] = mapped_column(String, nullable=False)
    stable_id: Mapped[str] = mapped_column(
        String, ForeignKey("identities.stable_id"), nullable=False
    )
    rev_id: Mapped[str] = mapped_column(
        String, ForeignKey("revisions.rev_id"), nullable=False
    )
    change_status: Mapped[str] = mapped_column(String, nullable=False)
    obj_type: Mapped[str] = mapped_column(String, nullable=False)
    floor_id: Mapped[str] = mapped_column(
        String, ForeignKey("floors.floor_id"), nullable=False
    )
    zone_id: Mapped[str] = mapped_column(
        String, ForeignKey("zones.zone_id"), nullable=False
    )
    sect_id: Mapped[str] = mapped_column(String, nullable=False)
    mat_id: Mapped[str] = mapped_column(
        String, ForeignKey("materials.mat_id"), nullable=False
    )
    geometry_points: Mapped[list[list[int]]] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["sect_id", "obj_type"],
            ["sections.sect_id", "sections.obj_type"],
            name="fk_objects_sect_id_obj_type",
        ),
        CheckConstraint(
            "change_status IN "
            "('added', 'modified', 'unchanged', 'deleted', 'restored')",
            name="ck_objects_change_status",
        ),
    )


class Reinforcement(Base):
    __tablename__ = "reinforcements"

    bar_id: Mapped[str] = mapped_column(String, primary_key=True)
    obj_id: Mapped[str] = mapped_column(
        String, ForeignKey("objects.obj_id"), nullable=False
    )
    barspec_id: Mapped[str] = mapped_column(
        String, ForeignKey("barspec.barspec_id"), nullable=False
    )
    bar_role: Mapped[str] = mapped_column(String, nullable=False)
    bar_count: Mapped[int] = mapped_column(Integer, nullable=False)
    bar_len: Mapped[int] = mapped_column(Integer, nullable=False)
    bar_space: Mapped[int | None] = mapped_column(Integer)
    bar_hook_type: Mapped[str | None] = mapped_column(String)


class Quantity(Base):
    __tablename__ = "quantity"

    qty_id: Mapped[str] = mapped_column(String, primary_key=True)
    obj_id: Mapped[str] = mapped_column(
        String, ForeignKey("objects.obj_id"), nullable=False
    )
    qty_sect: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_bar: Mapped[int] = mapped_column(Integer, nullable=False)