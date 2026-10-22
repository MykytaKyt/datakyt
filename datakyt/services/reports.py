"""Read-only reports. Each returns a list of flat rows plus its column order."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy import Date, cast, func, literal, literal_column, select, union_all
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ColumnClause, CompoundSelect

from datakyt.models import (
    Employee,
    EmployeeEquipment,
    EmployeeFurniture,
    EmployeeSoftwareLicense,
    Equipment,
    EquipmentType,
    Furniture,
    Office,
    Software,
    SoftwareLicense,
)
from datakyt.services.errors import NotFoundError


@dataclass(frozen=True)
class Report:
    columns: tuple[str, ...]
    rows: list[dict[str, Any]]


def _rows(columns: tuple[str, ...], result: Any) -> Report:
    return Report(columns, [dict(zip(columns, row, strict=True)) for row in result])


def inventory(session: Session) -> Report:
    """Count equipment by office, type and status."""
    stmt = (
        select(Office.city, EquipmentType.name, Equipment.status, func.count(Equipment.id))
        .join(Office, Equipment.office_id == Office.id)
        .join(EquipmentType, Equipment.equipment_type_id == EquipmentType.id)
        .where(Equipment.deleted_at.is_(None))
        .group_by(Office.city, EquipmentType.name, Equipment.status)
        .order_by(Office.city, EquipmentType.name, Equipment.status)
    )
    return _rows(("office", "type", "status", "count"), session.execute(stmt))


def employee_items(session: Session, employee_id: int) -> Report:
    """List everything currently issued to one employee."""
    employee = session.get(Employee, employee_id)
    if employee is None or employee.deleted_at is not None:
        raise NotFoundError(f"employee {employee_id} not found")
    equipment = (
        select(
            literal("equipment").label("category"),
            Equipment.id,
            Equipment.inventory_number,
            Equipment.name,
            EmployeeEquipment.issued_on,
        )
        .join(Equipment, EmployeeEquipment.equipment_id == Equipment.id)
        .where(EmployeeEquipment.employee_id == employee_id)
        .where(EmployeeEquipment.returned_on.is_(None))
    )
    furniture = (
        select(
            literal("furniture"),
            Furniture.id,
            Furniture.inventory_number,
            Furniture.name,
            EmployeeFurniture.issued_on,
        )
        .join(Furniture, EmployeeFurniture.furniture_id == Furniture.id)
        .where(EmployeeFurniture.employee_id == employee_id)
        .where(EmployeeFurniture.returned_on.is_(None))
    )
    licenses = (
        select(
            literal("license"),
            SoftwareLicense.id,
            SoftwareLicense.product_key,
            Software.name,
            EmployeeSoftwareLicense.issued_on,
        )
        .join(SoftwareLicense, EmployeeSoftwareLicense.software_license_id == SoftwareLicense.id)
        .join(Software, SoftwareLicense.software_id == Software.id)
        .where(EmployeeSoftwareLicense.employee_id == employee_id)
    )
    stmt: CompoundSelect[*tuple[Any, ...]] = union_all(equipment, furniture, licenses).order_by(
        literal_column("category"), literal_column("issued_on")
    )
    return _rows(
        ("category", "item_id", "inventory_number", "name", "issued_on"), session.execute(stmt)
    )


def expiring_licenses(session: Session, days: int, today: date | None = None) -> Report:
    """Licenses that expire between today and ``days`` from now."""
    today = today or date.today()
    used = (
        select(func.count())
        .where(EmployeeSoftwareLicense.software_license_id == SoftwareLicense.id)
        .scalar_subquery()
    )
    stmt = (
        select(
            SoftwareLicense.id,
            Software.name,
            SoftwareLicense.product_key,
            SoftwareLicense.seats,
            used,
            SoftwareLicense.expires_on,
        )
        .join(Software, SoftwareLicense.software_id == Software.id)
        .where(SoftwareLicense.expires_on.between(today, today + timedelta(days=days)))
        .order_by(SoftwareLicense.expires_on, SoftwareLicense.id)
    )
    report = _rows(
        ("license_id", "software", "product_key", "seats", "seats_used", "expires_on"),
        session.execute(stmt),
    )
    for row in report.rows:
        row["days_left"] = (row["expires_on"] - today).days
    return Report((*report.columns, "days_left"), report.rows)


def expiring_warranties(session: Session, days: int, today: date | None = None) -> Report:
    """Equipment and furniture whose warranty ends between today and ``days`` from now."""
    today = today or date.today()
    month: ColumnClause[Any] = literal_column("interval '1 month'")

    def until(model: type[Equipment] | type[Furniture]) -> Any:
        return cast(model.purchase_date + model.warranty_months * month, Date)

    equipment = select(
        literal("equipment").label("kind"),
        Equipment.id.label("id"),
        Equipment.inventory_number.label("inventory_number"),
        Equipment.name.label("name"),
        Equipment.purchase_date.label("purchase_date"),
        until(Equipment).label("warranty_until"),
    ).where(Equipment.deleted_at.is_(None))
    furniture = select(
        literal("furniture"),
        Furniture.id,
        Furniture.inventory_number,
        Furniture.name,
        Furniture.purchase_date,
        until(Furniture),
    ).where(Furniture.deleted_at.is_(None))
    items = union_all(equipment, furniture).subquery()
    stmt = (
        select(items)
        .where(items.c.warranty_until.between(today, today + timedelta(days=days)))
        .order_by(items.c.warranty_until, items.c.kind, items.c.id)
    )
    report = _rows(
        ("kind", "item_id", "inventory_number", "name", "purchase_date", "warranty_until"),
        session.execute(stmt),
    )
    for row in report.rows:
        row["days_left"] = (row["warranty_until"] - today).days
    return Report((*report.columns, "days_left"), report.rows)
