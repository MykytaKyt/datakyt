"""Application users and the audit trail."""

from datetime import datetime
from typing import Any

from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datakyt.models.base import Base, Role, TimestampMixin, enum_values


class AppUser(TimestampMixin, Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", values_callable=enum_values), default=Role.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(default=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(32))
    entity: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[int | None]
    changes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    user: Mapped[AppUser | None] = relationship()
