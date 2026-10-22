"""Declarative base, shared column mixins and enums."""

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, MetaData, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for every ORM model."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {
        datetime: DateTime(timezone=True),
        Decimal: Numeric(12, 2),
    }


class TimestampMixin:
    """``created_at`` and ``updated_at`` maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class SoftDeleteMixin:
    """Rows are hidden by setting ``deleted_at`` instead of being removed."""

    deleted_at: Mapped[datetime | None] = mapped_column(default=None)


class ItemStatus(enum.StrEnum):
    """Lifecycle state of a piece of equipment."""

    ISSUED = "issued"
    RESERVED = "reserved"
    IN_REPAIR = "in_repair"
    BROKEN = "broken"
    WRITTEN_OFF = "written_off"


class Role(enum.StrEnum):
    """Access level of an application user."""

    ADMIN = "admin"
    VIEWER = "viewer"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Store enum values (not member names) in Postgres enum types."""
    return [str(member.value) for member in enum_cls]
