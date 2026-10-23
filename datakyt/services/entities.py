"""Service instances for every entity exposed through the API."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from datakyt.models import (
    Employee,
    EmployeeEquipment,
    EmployeeFurniture,
    Equipment,
    EquipmentPart,
    EquipmentType,
    Furniture,
    FurnitureType,
    ItemStatus,
    Office,
    Project,
    Software,
    SoftwareLicense,
)
from datakyt.services.crud import CrudService
from datakyt.services.errors import ConflictError, InvalidInputError


def _require_alive(
    session: Session, model: type[Employee | Equipment | Furniture], obj_id: int, label: str
) -> None:
    alive = session.scalar(select(exists().where(model.id == obj_id, model.deleted_at.is_(None))))
    if not alive:
        raise InvalidInputError(f"{label} {obj_id} does not exist")


class EmployeeService(CrudService[Employee]):
    def before_delete(self, session: Session, obj: Employee) -> None:
        open_items = session.scalar(
            select(
                exists().where(
                    EmployeeEquipment.employee_id == obj.id, EmployeeEquipment.returned_on.is_(None)
                )
            )
        ) or session.scalar(
            select(
                exists().where(
                    EmployeeFurniture.employee_id == obj.id, EmployeeFurniture.returned_on.is_(None)
                )
            )
        )
        if open_items:
            raise ConflictError("employee still holds issued items; return them first")


class EquipmentService(CrudService[Equipment]):
    def validate(self, session: Session, data: Mapping[str, Any], obj: Equipment | None) -> None:
        status = data.get("status")
        if obj is None:
            if status == ItemStatus.ISSUED:
                raise InvalidInputError("use POST /equipment/{id}/issue to issue an item")
            return
        if status is not None and status != obj.status:
            if status == ItemStatus.ISSUED:
                raise InvalidInputError("use POST /equipment/{id}/issue to issue an item")
            if obj.status == ItemStatus.ISSUED:
                raise ConflictError("item is issued; return it before changing its status")

    def before_delete(self, session: Session, obj: Equipment) -> None:
        if obj.status == ItemStatus.ISSUED:
            raise ConflictError("item is issued; return it before deleting")
        obj.status = ItemStatus.WRITTEN_OFF


class EquipmentPartService(CrudService[EquipmentPart]):
    def validate(
        self, session: Session, data: Mapping[str, Any], obj: EquipmentPart | None
    ) -> None:
        if "equipment_id" in data:
            _require_alive(session, Equipment, data["equipment_id"], "equipment")


class FurnitureService(CrudService[Furniture]):
    def before_delete(self, session: Session, obj: Furniture) -> None:
        issued = session.scalar(
            select(
                exists().where(
                    EmployeeFurniture.furniture_id == obj.id,
                    EmployeeFurniture.returned_on.is_(None),
                )
            )
        )
        if issued:
            raise ConflictError("item is issued; return it before deleting")


class LicenseService(CrudService[SoftwareLicense]):
    def validate(
        self, session: Session, data: Mapping[str, Any], obj: SoftwareLicense | None
    ) -> None:
        purchased = data.get("purchased_on", obj.purchased_on if obj else None)
        expires = data.get("expires_on", obj.expires_on if obj else None)
        if purchased is not None and expires is not None and expires < purchased:
            raise InvalidInputError("expires_on must not be earlier than purchased_on")


offices = CrudService(Office, entity="office", search_fields=("city",), sort_fields=("city",))
projects = CrudService(Project, entity="project", search_fields=("name",), sort_fields=("name",))
equipment_types = CrudService(
    EquipmentType, entity="equipment_type", search_fields=("name",), sort_fields=("name",)
)
furniture_types = CrudService(
    FurnitureType, entity="furniture_type", search_fields=("name",), sort_fields=("name",)
)
employees = EmployeeService(
    Employee,
    entity="employee",
    search_fields=("full_name", "email", "phone", "position"),
    filter_fields=("office_id", "project_id"),
    sort_fields=("full_name", "email", "created_at"),
    soft_delete=True,
)
equipment = EquipmentService(
    Equipment,
    entity="equipment",
    search_fields=("inventory_number", "name", "serial_number", "description"),
    filter_fields=("status", "office_id", "equipment_type_id"),
    sort_fields=("inventory_number", "name", "status", "purchase_date", "cost", "created_at"),
    soft_delete=True,
)
equipment_parts = EquipmentPartService(
    EquipmentPart,
    entity="equipment_part",
    search_fields=("name", "serial_number"),
    filter_fields=("equipment_id",),
    sort_fields=("name",),
)
furniture = FurnitureService(
    Furniture,
    entity="furniture",
    search_fields=("inventory_number", "name"),
    filter_fields=("office_id", "furniture_type_id"),
    sort_fields=("inventory_number", "name", "purchase_date", "cost", "created_at"),
    soft_delete=True,
)
software = CrudService(
    Software, entity="software", search_fields=("name", "vendor"), sort_fields=("name",)
)
licenses = LicenseService(
    SoftwareLicense,
    entity="software_license",
    search_fields=("product_key",),
    filter_fields=("software_id",),
    sort_fields=("purchased_on", "expires_on", "seats"),
)
