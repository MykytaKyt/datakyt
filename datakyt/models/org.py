"""Offices, projects and employees."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datakyt.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from datakyt.models.assignments import EmployeeEquipment


class Office(TimestampMixin, Base):
    __tablename__ = "office"

    id: Mapped[int] = mapped_column(primary_key=True)
    city: Mapped[str] = mapped_column(String(100), unique=True)


class Project(TimestampMixin, Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)


class Employee(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "employee"
    __table_args__ = (
        Index(
            "uq_employee_email_active",
            "email",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_employee_phone_active",
            "phone",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[str | None] = mapped_column(String(100))
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="RESTRICT"))
    office_id: Mapped[int] = mapped_column(ForeignKey("office.id", ondelete="RESTRICT"))

    project: Mapped[Project] = relationship()
    office: Mapped[Office] = relationship()
    equipment_assignments: Mapped[list["EmployeeEquipment"]] = relationship(
        back_populates="employee", viewonly=True
    )
