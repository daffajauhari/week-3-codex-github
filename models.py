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
            "obj_type IN ('col', 'beam', 'wall', 'slab')",
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


class Member(Base):
    __tablename__ = "members"

    member_id: Mapped[str] = mapped_column(String, primary_key=True)
    member_type: Mapped[str] = mapped_column(String)
    storey_id: Mapped[str] = mapped_column(
        String, ForeignKey("floors.floor_id")
    )
    dimension_id: Mapped[str] = mapped_column(String)
    material_id: Mapped[str] = mapped_column(
        String, ForeignKey("materials.mat_id")
    )
    zone_id: Mapped[str] = mapped_column(
        String, ForeignKey("zones.zone_id")
    )
    geometry_points: Mapped[list[list[int]]] = mapped_column(JSONB)

    __table_args__ = (
        ForeignKeyConstraint(
            ["dimension_id", "member_type"],
            ["sections.sect_id", "sections.obj_type"],
            name="fk_members_dimension_type",
        ),
    )