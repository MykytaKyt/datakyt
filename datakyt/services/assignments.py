"""Issuing and returning items, and assigning software licenses."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datakyt.models import (
    AppUser,
    Employee,
    EmployeeEquipment,
    EmployeeFurniture,
    EmployeeSoftwareLicense,
    Equipment,
    Furniture,
    ItemStatus,
    SoftwareLicense,
)
from datakyt.services import audit
from datakyt.services.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    translate_integrity_errors,
)

RETURN_STATUSES = frozenset({ItemStatus.RESERVED, ItemStatus.IN_REPAIR, ItemStatus.BROKEN})


def _active_employee(session: Session, employee_id: int) -> Employee:
    employee = session.get(Employee, employee_id)
    if employee is None or employee.deleted_at is not None:
        raise InvalidInputError(f"employee {employee_id} does not exist")
    return employee


def _locked_equipment(session: Session, equipment_id: int) -> Equipment:
    item = session.scalar(
        select(Equipment)
        .where(Equipment.id == equipment_id, Equipment.deleted_at.is_(None))
        .with_for_update()
    )
    if item is None:
        raise NotFoundError(f"equipment {equipment_id} not found")
    return item


def _locked_furniture(session: Session, furniture_id: int) -> Furniture:
    item = session.scalar(
        select(Furniture)
        .where(Furniture.id == furniture_id, Furniture.deleted_at.is_(None))
        .with_for_update()
    )
    if item is None:
        raise NotFoundError(f"furniture {furniture_id} not found")
    return item


def issue_equipment(
    session: Session,
    equipment_id: int,
    employee_id: int,
    actor: AppUser | None,
    issued_on: date | None = None,
) -> EmployeeEquipment:
    """Issue an available (``reserved``) item to an employee."""
    item = _locked_equipment(session, equipment_id)
    _active_employee(session, employee_id)
    if item.status != ItemStatus.RESERVED:
        raise ConflictError(f"equipment {equipment_id} is {item.status.value}, not available")
    assignment = EmployeeEquipment(
        employee_id=employee_id, equipment_id=equipment_id, issued_on=issued_on or date.today()
    )
    session.add(assignment)
    item.status = ItemStatus.ISSUED
    with translate_integrity_errors():
        session.flush()
    audit.record(
        session,
        actor,
        "issue",
        "equipment",
        equipment_id,
        {"employee_id": employee_id, "issued_on": assignment.issued_on},
    )
    session.commit()
    return assignment


def return_equipment(
    session: Session,
    equipment_id: int,
    actor: AppUser | None,
    returned_on: date | None = None,
    status: ItemStatus = ItemStatus.RESERVED,
) -> EmployeeEquipment:
    """Close the open assignment of an item and set its new status."""
    if status not in RETURN_STATUSES:
        raise InvalidInputError("status after return must be reserved, in_repair or broken")
    item = _locked_equipment(session, equipment_id)
    assignment = session.scalar(
        select(EmployeeEquipment).where(
            EmployeeEquipment.equipment_id == equipment_id,
            EmployeeEquipment.returned_on.is_(None),
        )
    )
    if assignment is None:
        raise ConflictError(f"equipment {equipment_id} is not issued")
    returned_on = returned_on or date.today()
    if returned_on < assignment.issued_on:
        raise InvalidInputError("returned_on must not be earlier than issued_on")
    assignment.returned_on = returned_on
    item.status = status
    session.flush()
    audit.record(
        session,
        actor,
        "return",
        "equipment",
        equipment_id,
        {"employee_id": assignment.employee_id, "returned_on": returned_on, "status": status},
    )
    session.commit()
    return assignment


def issue_furniture(
    session: Session,
    furniture_id: int,
    employee_id: int,
    actor: AppUser | None,
    issued_on: date | None = None,
) -> EmployeeFurniture:
    """Issue a furniture item that is not currently issued."""
    _locked_furniture(session, furniture_id)
    _active_employee(session, employee_id)
    open_assignment = session.scalar(
        select(EmployeeFurniture.id).where(
            EmployeeFurniture.furniture_id == furniture_id,
            EmployeeFurniture.returned_on.is_(None),
        )
    )
    if open_assignment is not None:
        raise ConflictError(f"furniture {furniture_id} is already issued")
    assignment = EmployeeFurniture(
        employee_id=employee_id, furniture_id=furniture_id, issued_on=issued_on or date.today()
    )
    session.add(assignment)
    with translate_integrity_errors():
        session.flush()
    audit.record(
        session,
        actor,
        "issue",
        "furniture",
        furniture_id,
        {"employee_id": employee_id, "issued_on": assignment.issued_on},
    )
    session.commit()
    return assignment


def return_furniture(
    session: Session,
    furniture_id: int,
    actor: AppUser | None,
    returned_on: date | None = None,
) -> EmployeeFurniture:
    """Close the open assignment of a furniture item."""
    _locked_furniture(session, furniture_id)
    assignment = session.scalar(
        select(EmployeeFurniture).where(
            EmployeeFurniture.furniture_id == furniture_id,
            EmployeeFurniture.returned_on.is_(None),
        )
    )
    if assignment is None:
        raise ConflictError(f"furniture {furniture_id} is not issued")
    returned_on = returned_on or date.today()
    if returned_on < assignment.issued_on:
        raise InvalidInputError("returned_on must not be earlier than issued_on")
    assignment.returned_on = returned_on
    session.flush()
    audit.record(
        session,
        actor,
        "return",
        "furniture",
        furniture_id,
        {"employee_id": assignment.employee_id, "returned_on": returned_on},
    )
    session.commit()
    return assignment


def assign_license(
    session: Session,
    license_id: int,
    employee_id: int,
    actor: AppUser | None,
    issued_on: date | None = None,
) -> EmployeeSoftwareLicense:
    """Give an employee a seat of a license, respecting the seat count and expiry."""
    lic = session.scalar(
        select(SoftwareLicense).where(SoftwareLicense.id == license_id).with_for_update()
    )
    if lic is None:
        raise InvalidInputError(f"software license {license_id} does not exist")
    _active_employee(session, employee_id)
    issued_on = issued_on or date.today()
    if lic.expires_on is not None and lic.expires_on < issued_on:
        raise ConflictError(f"software license {license_id} expired on {lic.expires_on}")
    used = (
        session.scalar(
            select(func.count()).where(EmployeeSoftwareLicense.software_license_id == license_id)
        )
        or 0
    )
    if used >= lic.seats:
        raise ConflictError(f"all {lic.seats} seats of license {license_id} are in use")
    assignment = EmployeeSoftwareLicense(
        employee_id=employee_id, software_license_id=license_id, issued_on=issued_on
    )
    session.add(assignment)
    with translate_integrity_errors():
        session.flush()
    audit.record(
        session,
        actor,
        "assign",
        "software_license",
        license_id,
        {"employee_id": employee_id, "issued_on": issued_on},
    )
    session.commit()
    return assignment


def revoke_license(session: Session, assignment_id: int, actor: AppUser | None) -> None:
    """Free a license seat."""
    assignment = session.get(EmployeeSoftwareLicense, assignment_id)
    if assignment is None:
        raise NotFoundError(f"license assignment {assignment_id} not found")
    session.delete(assignment)
    session.flush()
    audit.record(
        session,
        actor,
        "revoke",
        "software_license",
        assignment.software_license_id,
        {"employee_id": assignment.employee_id},
    )
    session.commit()
