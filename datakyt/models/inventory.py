"""Equipment, equipment parts and furniture."""

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datakyt.models.base import Base, ItemStatus, SoftDeleteMixin, TimestampMixin, enum_values
from datakyt.models.org import Office


class EquipmentType(TimestampMixin, Base):
    __tablename__ = "equipment_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Equipment(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint("cost > 0", name="cost_positive"),
        CheckConstraint("warranty_months >= 0", name="warranty_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_number: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    serial_number: Mapped[str] = mapped_column(String(100))
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name="item_status", values_callable=enum_values),
        default=ItemStatus.RESERVED,
    )
    warranty_months: Mapped[int]
    cost: Mapped[Decimal]
    purchase_date: Mapped[date]
    description: Mapped[str | None] = mapped_column(Text)
    equipment_type_id: Mapped[int] = mapped_column(
        ForeignKey("equipment_type.id", ondelete="RESTRICT")
    )
    office_id: Mapped[int] = mapped_column(ForeignKey("office.id", ondelete="RESTRICT"))

    equipment_type: Mapped[EquipmentType] = relationship()
    office: Mapped[Office] = relationship()
    parts: Mapped[list["EquipmentPart"]] = relationship(back_populates="equipment", viewonly=True)


class EquipmentPart(TimestampMixin, Base):
    __tablename__ = "equipment_part"
    __table_args__ = (UniqueConstraint("equipment_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"))

    equipment: Mapped[Equipment] = relationship(back_populates="parts")


class FurnitureType(TimestampMixin, Base):
    __tablename__ = "furniture_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Furniture(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "furniture"
    __table_args__ = (
        CheckConstraint("cost > 0", name="cost_positive"),
        CheckConstraint("warranty_months >= 0", name="warranty_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_number: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    warranty_months: Mapped[int]
    cost: Mapped[Decimal]
    purchase_date: Mapped[date]
    furniture_type_id: Mapped[int] = mapped_column(
        ForeignKey("furniture_type.id", ondelete="RESTRICT")
    )
    office_id: Mapped[int] = mapped_column(ForeignKey("office.id", ondelete="RESTRICT"))

    furniture_type: Mapped[FurnitureType] = relationship()
    office: Mapped[Office] = relationship()
