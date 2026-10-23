"""Pydantic models for request bodies and responses."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from datakyt.models import ItemStatus, Role

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
ShortName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
InventoryNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"
    ),
]
Phone = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=20, pattern=r"^\+?[0-9 ()-]{5,20}$")
]
Cost = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]
Months = Annotated[int, Field(ge=0, le=600)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=72)]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


def _lower(value: str | None) -> str | None:
    return value.lower() if value is not None else None


# Offices, projects, types -------------------------------------------------------------------


class OfficeCreate(Schema):
    city: ShortName


class OfficeUpdate(Schema):
    city: ShortName | None = None


class OfficeRead(ReadSchema):
    city: str


class ProjectCreate(Schema):
    name: Name


class ProjectUpdate(Schema):
    name: Name | None = None


class ProjectRead(ReadSchema):
    name: str


class TypeCreate(Schema):
    name: ShortName


class TypeUpdate(Schema):
    name: ShortName | None = None


class TypeRead(ReadSchema):
    name: str


# Employees ----------------------------------------------------------------------------------


class EmployeeCreate(Schema):
    full_name: Name
    email: EmailStr
    phone: Phone | None = None
    position: ShortName | None = None
    project_id: int
    office_id: int

    _normalize_email = field_validator("email")(_lower)


class EmployeeUpdate(Schema):
    full_name: Name | None = None
    email: EmailStr | None = None
    phone: Phone | None = None
    position: ShortName | None = None
    project_id: int | None = None
    office_id: int | None = None

    _normalize_email = field_validator("email")(_lower)


class EmployeeRead(ReadSchema):
    full_name: str
    email: str
    phone: str | None
    position: str | None
    project_id: int
    office_id: int


# Equipment and furniture --------------------------------------------------------------------


class EquipmentCreate(Schema):
    inventory_number: InventoryNumber
    name: Name
    serial_number: ShortName
    status: ItemStatus = ItemStatus.RESERVED
    warranty_months: Months
    cost: Cost
    purchase_date: date
    description: str | None = None
    equipment_type_id: int
    office_id: int


class EquipmentUpdate(Schema):
    inventory_number: InventoryNumber | None = None
    name: Name | None = None
    serial_number: ShortName | None = None
    status: ItemStatus | None = None
    warranty_months: Months | None = None
    cost: Cost | None = None
    purchase_date: date | None = None
    description: str | None = None
    equipment_type_id: int | None = None
    office_id: int | None = None


class EquipmentRead(ReadSchema):
    inventory_number: str
    name: str
    serial_number: str
    status: ItemStatus
    warranty_months: int
    cost: Decimal
    purchase_date: date
    description: str | None
    equipment_type_id: int
    office_id: int


class EquipmentPartCreate(Schema):
    name: Name
    serial_number: ShortName | None = None
    equipment_id: int


class EquipmentPartUpdate(Schema):
    name: Name | None = None
    serial_number: ShortName | None = None


class EquipmentPartRead(ReadSchema):
    name: str
    serial_number: str | None
    equipment_id: int


class FurnitureCreate(Schema):
    inventory_number: InventoryNumber
    name: Name
    warranty_months: Months
    cost: Cost
    purchase_date: date
    furniture_type_id: int
    office_id: int


class FurnitureUpdate(Schema):
    inventory_number: InventoryNumber | None = None
    name: Name | None = None
    warranty_months: Months | None = None
    cost: Cost | None = None
    purchase_date: date | None = None
    furniture_type_id: int | None = None
    office_id: int | None = None


class FurnitureRead(ReadSchema):
    inventory_number: str
    name: str
    warranty_months: int
    cost: Decimal
    purchase_date: date
    furniture_type_id: int
    office_id: int


# Software -----------------------------------------------------------------------------------


class SoftwareCreate(Schema):
    name: Name
    vendor: Name | None = None


class SoftwareUpdate(Schema):
    name: Name | None = None
    vendor: Name | None = None


class SoftwareRead(ReadSchema):
    name: str
    vendor: str | None


class LicenseCreate(Schema):
    software_id: int
    product_key: Name | None = None
    seats: Annotated[int, Field(ge=1)] = 1
    cost: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)] | None = None
    purchased_on: date
    expires_on: date | None = None


class LicenseUpdate(Schema):
    software_id: int | None = None
    product_key: Name | None = None
    seats: Annotated[int, Field(ge=1)] | None = None
    cost: Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)] | None = None
    purchased_on: date | None = None
    expires_on: date | None = None


class LicenseRead(ReadSchema):
    software_id: int
    product_key: str | None
    seats: int
    cost: Decimal | None
    purchased_on: date
    expires_on: date | None


# Assignments --------------------------------------------------------------------------------


class IssueRequest(Schema):
    employee_id: int
    issued_on: date | None = Field(default=None, description="Defaults to today.")


class ReturnRequest(Schema):
    returned_on: date | None = Field(default=None, description="Defaults to today.")
    status: ItemStatus = Field(
        default=ItemStatus.RESERVED,
        description="Equipment status after the return: reserved, in_repair or broken.",
    )


class LicenseAssignRequest(Schema):
    employee_id: int
    software_license_id: int
    issued_on: date | None = None


class EquipmentAssignmentRead(ReadSchema):
    employee_id: int
    equipment_id: int
    issued_on: date
    returned_on: date | None


class FurnitureAssignmentRead(ReadSchema):
    employee_id: int
    furniture_id: int
    issued_on: date
    returned_on: date | None


class LicenseAssignmentRead(ReadSchema):
    employee_id: int
    software_license_id: int
    issued_on: date


# Users and auth -----------------------------------------------------------------------------


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(Schema):
    email: EmailStr
    password: Password
    role: Role = Role.VIEWER

    _normalize_email = field_validator("email")(_lower)


class UserUpdate(Schema):
    password: Password | None = None
    role: Role | None = None
    is_active: bool | None = None


class UserRead(ReadSchema):
    email: str
    role: Role
    is_active: bool


# Import -------------------------------------------------------------------------------------


class RowError(BaseModel):
    row: int = Field(description="1-based data row number (the header is row 0).")
    errors: list[str]


class ImportResult(BaseModel):
    dry_run: bool
    total_rows: int
    imported: int
    errors: list[RowError]
