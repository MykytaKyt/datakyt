"""Audit trail helpers."""

from typing import Any

from pydantic_core import to_jsonable_python
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from datakyt.models import AppUser, AuditLog, Base


def snapshot(obj: Base) -> dict[str, Any]:
    """Return the column values of ``obj`` as JSON-compatible data."""
    mapper = inspect(obj).mapper
    values = {attr.key: getattr(obj, attr.key) for attr in mapper.column_attrs}
    result: dict[str, Any] = to_jsonable_python(values)
    return result


def record(
    session: Session,
    actor: AppUser | None,
    action: str,
    entity: str,
    entity_id: int | None,
    changes: dict[str, Any] | None = None,
) -> AuditLog:
    """Add an audit entry to the current transaction."""
    entry = AuditLog(
        user_id=actor.id if actor is not None else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        changes=to_jsonable_python(changes or {}),
    )
    session.add(entry)
    return entry
