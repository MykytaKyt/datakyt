"""Generic create/read/update/delete service used by every simple entity."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ColumnElement, Select, String, cast, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from datakyt.models import AppUser, Base
from datakyt.services import audit
from datakyt.services.errors import InvalidInputError, NotFoundError, translate_integrity_errors


@dataclass(frozen=True)
class ListParams:
    """Pagination, filtering and sorting options for :meth:`CrudService.list_page`."""

    offset: int = 0
    limit: int = 50
    q: str | None = None
    sort: str | None = None
    filters: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    offset: int
    limit: int


class CrudService[M: Base]:
    """CRUD operations for one model, with audit logging and optional soft delete.

    Args:
        model: ORM class the service manages.
        entity: Name written to the audit log.
        search_fields: Text columns matched by the ``q`` parameter (case-insensitive).
        filter_fields: Columns that can be filtered by exact value.
        sort_fields: Columns accepted by ``sort`` (prefix with ``-`` for descending).
        soft_delete: Hide rows by setting ``deleted_at`` instead of deleting them.
    """

    def __init__(
        self,
        model: type[M],
        *,
        entity: str,
        search_fields: Sequence[str] = (),
        filter_fields: Sequence[str] = (),
        sort_fields: Sequence[str] = ("id",),
        soft_delete: bool = False,
    ) -> None:
        self.model = model
        self.entity = entity
        self.search_fields = tuple(search_fields)
        self.filter_fields = tuple(filter_fields)
        self.sort_fields = tuple(sort_fields)
        self.soft_delete = soft_delete

    def _column(self, name: str) -> InstrumentedAttribute[Any]:
        column: InstrumentedAttribute[Any] = getattr(self.model, name)
        return column

    def base_query(self) -> Select[M]:
        """Return a select of all visible (not soft-deleted) rows."""
        stmt = select(self.model)
        if self.soft_delete:
            stmt = stmt.where(self._column("deleted_at").is_(None))
        return stmt

    def list_page(self, session: Session, params: ListParams | None = None) -> Page[M]:
        """Return one page of rows matching ``params``."""
        params = params or ListParams()
        stmt = self.base_query()
        for name, value in (params.filters or {}).items():
            if name not in self.filter_fields:
                raise InvalidInputError(f"cannot filter by {name!r}")
            if value is not None:
                stmt = stmt.where(self._column(name) == value)
        if params.q and self.search_fields:
            pattern = f"%{params.q}%"
            conditions: list[ColumnElement[bool]] = [
                cast(self._column(name), String).ilike(pattern) for name in self.search_fields
            ]
            stmt = stmt.where(or_(*conditions))

        total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        sort = params.sort or "id"
        descending = sort.startswith("-")
        sort_name = sort.removeprefix("-")
        if sort_name not in self.sort_fields and sort_name != "id":
            raise InvalidInputError(f"cannot sort by {sort_name!r}")
        order = self._column(sort_name)
        stmt = stmt.order_by(order.desc() if descending else order.asc(), self._column("id"))
        stmt = stmt.offset(params.offset).limit(params.limit)
        items = list(session.scalars(stmt))
        return Page(items=items, total=total, offset=params.offset, limit=params.limit)

    def get(self, session: Session, obj_id: int) -> M:
        """Return the row with ``obj_id`` or raise :class:`NotFoundError`."""
        obj = session.scalar(self.base_query().where(self._column("id") == obj_id))
        if obj is None:
            raise NotFoundError(f"{self.entity} {obj_id} not found")
        return obj

    def validate(self, session: Session, data: Mapping[str, Any], obj: M | None) -> None:
        """Hook for entity-specific checks; ``obj`` is ``None`` on create."""

    def create(self, session: Session, data: Mapping[str, Any], actor: AppUser | None) -> M:
        """Insert a row and commit."""
        obj = self.add(session, data, actor)
        session.commit()
        return obj

    def add(self, session: Session, data: Mapping[str, Any], actor: AppUser | None) -> M:
        """Insert a row and flush without committing (used by bulk import)."""
        self.validate(session, data, None)
        obj = self.model(**data)
        session.add(obj)
        with translate_integrity_errors():
            session.flush()
        audit.record(session, actor, "create", self.entity, self._id(obj), audit.snapshot(obj))
        return obj

    def update(
        self, session: Session, obj_id: int, data: Mapping[str, Any], actor: AppUser | None
    ) -> M:
        """Apply a partial update and commit."""
        obj = self.get(session, obj_id)
        self.validate(session, data, obj)
        changes: dict[str, list[Any]] = {}
        for key, value in data.items():
            old = getattr(obj, key)
            if old != value:
                changes[key] = [old, value]
                setattr(obj, key, value)
        if changes:
            with translate_integrity_errors():
                session.flush()
            audit.record(session, actor, "update", self.entity, obj_id, changes)
            session.commit()
            session.refresh(obj)
        return obj

    def before_delete(self, session: Session, obj: M) -> None:
        """Hook to refuse deletion of rows that are still in use."""

    def delete(self, session: Session, obj_id: int, actor: AppUser | None) -> None:
        """Delete (or soft-delete) a row and commit."""
        obj = self.get(session, obj_id)
        self.before_delete(session, obj)
        if self.soft_delete:
            obj.deleted_at = datetime.now(UTC)  # type: ignore[attr-defined]
        else:
            session.delete(obj)
        with translate_integrity_errors():
            session.flush()
        audit.record(session, actor, "delete", self.entity, obj_id)
        session.commit()

    @staticmethod
    def _id(obj: Base) -> int:
        value: int = obj.id  # type: ignore[attr-defined]
        return value
