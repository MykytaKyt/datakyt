"""Link tables recording what is issued to whom."""

from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datakyt.models.base import Base, TimestampMixin
from datakyt.models.inventory import Equipment, Furniture
from datakyt.models.org import Employee
from datakyt.models.software import SoftwareLicense


class EmployeeEquipment(TimestampMixin, Base):
    __tablename__ = "employee_equipment"
    __table_args__ = (
        CheckConstraint(
            "returned_on IS NULL OR returned_on >= issued_on", name="return_after_issue"
        ),
        # An item can have at most one open (not yet returned) assignment.
        Index(
            "uq_employee_equipment_open",
            "equipment_id",
            unique=True,
            postgresql_where=text("returned_on IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"), index=True
    )
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE"), index=True
    )
    issued_on: Mapped[date]
    returned_on: Mapped[date | None]

    employee: Mapped[Employee] = relationship(back_populates="equipment_assignments")
    equipment: Mapped[Equipment] = relationship()


class EmployeeFurniture(TimestampMixin, Base):
    __tablename__ = "employee_furniture"
    __table_args__ = (
        CheckConstraint(
            "returned_on IS NULL OR returned_on >= issued_on", name="return_after_issue"
        ),
        Index(
            "uq_employee_furniture_open",
            "furniture_id",
            unique=True,
            postgresql_where=text("returned_on IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"), index=True
    )
    furniture_id: Mapped[int] = mapped_column(
        ForeignKey("furniture.id", ondelete="CASCADE"), index=True
    )
    issued_on: Mapped[date]
    returned_on: Mapped[date | None]

    employee: Mapped[Employee] = relationship()
    furniture: Mapped[Furniture] = relationship()


class EmployeeSoftwareLicense(TimestampMixin, Base):
    __tablename__ = "employee_sw_license"
    __table_args__ = (UniqueConstraint("employee_id", "software_license_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="CASCADE"), index=True
    )
    software_license_id: Mapped[int] = mapped_column(
        ForeignKey("software_license.id", ondelete="CASCADE"), index=True
    )
    issued_on: Mapped[date]

    employee: Mapped[Employee] = relationship()
    software_license: Mapped[SoftwareLicense] = relationship()
