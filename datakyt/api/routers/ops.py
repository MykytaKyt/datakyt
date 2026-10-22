"""Health check and audit log."""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select

from datakyt import __version__, db
from datakyt.api.crud import PageOut
from datakyt.api.deps import AdminUser, SessionDep
from datakyt.models import AuditLog

router = APIRouter(tags=["ops"])


@router.get("/health")
def health(session: SessionDep) -> JSONResponse:
    """Report service and database health; 503 if the database is unreachable."""
    try:
        db.ping(session)
    except Exception:
        return JSONResponse(
            {"status": "error", "database": "unreachable", "version": __version__},
            status_code=503,
        )
    return JSONResponse({"status": "ok", "database": "ok", "version": __version__})


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int | None
    action: str
    entity: str
    entity_id: int | None
    changes: dict[str, Any]


@router.get("/audit-log", response_model=PageOut[AuditRead])
def audit_log(
    session: SessionDep,
    user: AdminUser,
    entity: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> dict[str, Any]:
    """List audit entries, newest first (admins only)."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if entity is not None:
        stmt = stmt.where(AuditLog.entity == entity)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(session.scalars(stmt.offset(offset).limit(limit)))
    return {"items": items, "total": total, "offset": offset, "limit": limit}
