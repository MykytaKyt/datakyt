"""ORM models. Importing this package registers every table on ``Base.metadata``."""

from datakyt.models.assignments import EmployeeEquipment, EmployeeFurniture, EmployeeSoftwareLicense
from datakyt.models.auth import AppUser, AuditLog
from datakyt.models.base import Base, ItemStatus, Role
from datakyt.models.inventory import (
    Equipment,
    EquipmentPart,
    EquipmentType,
    Furniture,
    FurnitureType,
)
from datakyt.models.org import Employee, Office, Project
from datakyt.models.software import Software, SoftwareLicense

__all__ = [
    "AppUser",
    "AuditLog",
    "Base",
    "Employee",
    "EmployeeEquipment",
    "EmployeeFurniture",
    "EmployeeSoftwareLicense",
    "Equipment",
    "EquipmentPart",
    "EquipmentType",
    "Furniture",
    "FurnitureType",
    "ItemStatus",
    "Office",
    "Project",
    "Role",
    "Software",
    "SoftwareLicense",
]
