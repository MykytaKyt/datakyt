"""History of what was issued to whom, and software license seats."""

from typing import Annotated, Any

from fastapi import APIRouter, Query, Response
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from datakyt import schemas
from datakyt.api.crud import PageOut
from datakyt.api.deps import AdminUser, CurrentUser, SessionDep
from datakyt.models import EmployeeEquipment, EmployeeFurniture, EmployeeSoftwareLicense
from datakyt.services import assignments

router = APIRouter(prefix="/assignments", tags=["assignments"])

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=500)]


def _page(session: Session, stmt: Select[Any], offset: int, limit: int) -> dict[str, Any]:
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(session.scalars(stmt.offset(offset).limit(limit)))
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.get("/equipment", response_model=PageOut[schemas.EquipmentAssignmentRead])
def list_equipment_assignments(
    session: SessionDep,
    user: CurrentUser,
    employee_id: int | None = None,
    equipment_id: int | None = None,
    active: Annotated[bool | None, Query(description="Only open (true) or closed (false).")] = None,
    offset: Offset = 0,
    limit: Limit = 50,
) -> dict[str, Any]:
    """List equipment assignments, newest first."""
    stmt = select(EmployeeEquipment).order_by(EmployeeEquipment.id.desc())
    if employee_id is not None:
        stmt = stmt.where(EmployeeEquipment.employee_id == employee_id)
    if equipment_id is not None:
        stmt = stmt.where(EmployeeEquipment.equipment_id == equipment_id)
    if active is not None:
        column = EmployeeEquipment.returned_on
        stmt = stmt.where(column.is_(None) if active else column.is_not(None))
    return _page(session, stmt, offset, limit)


@router.get("/furniture", response_model=PageOut[schemas.FurnitureAssignmentRead])
def list_furniture_assignments(
    session: SessionDep,
    user: CurrentUser,
    employee_id: int | None = None,
    furniture_id: int | None = None,
    active: Annotated[bool | None, Query(description="Only open (true) or closed (false).")] = None,
    offset: Offset = 0,
    limit: Limit = 50,
) -> dict[str, Any]:
    """List furniture assignments, newest first."""
    stmt = select(EmployeeFurniture).order_by(EmployeeFurniture.id.desc())
    if employee_id is not None:
        stmt = stmt.where(EmployeeFurniture.employee_id == employee_id)
    if furniture_id is not None:
        stmt = stmt.where(EmployeeFurniture.furniture_id == furniture_id)
    if active is not None:
        column = EmployeeFurniture.returned_on
        stmt = stmt.where(column.is_(None) if active else column.is_not(None))
    return _page(session, stmt, offset, limit)


@router.get("/licenses", response_model=PageOut[schemas.LicenseAssignmentRead])
def list_license_assignments(
    session: SessionDep,
    user: CurrentUser,
    employee_id: int | None = None,
    software_license_id: int | None = None,
    offset: Offset = 0,
    limit: Limit = 50,
) -> dict[str, Any]:
    """List license seats in use."""
    stmt = select(EmployeeSoftwareLicense).order_by(EmployeeSoftwareLicense.id.desc())
    if employee_id is not None:
        stmt = stmt.where(EmployeeSoftwareLicense.employee_id == employee_id)
    if software_license_id is not None:
        stmt = stmt.where(EmployeeSoftwareLicense.software_license_id == software_license_id)
    return _page(session, stmt, offset, limit)


@router.post("/licenses", response_model=schemas.LicenseAssignmentRead, status_code=201)
def assign_license(
    session: SessionDep, user: AdminUser, body: schemas.LicenseAssignRequest
) -> EmployeeSoftwareLicense:
    """Give an employee one seat of a license."""
    return assignments.assign_license(
        session, body.software_license_id, body.employee_id, user, body.issued_on
    )


@router.delete("/licenses/{assignment_id}", status_code=204, response_class=Response)
def revoke_license(session: SessionDep, user: AdminUser, assignment_id: int) -> Response:
    """Free a license seat."""
    assignments.revoke_license(session, assignment_id, user)
    return Response(status_code=204)
