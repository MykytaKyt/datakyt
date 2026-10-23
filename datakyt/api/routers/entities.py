"""Standard CRUD routers for every entity."""

from fastapi import APIRouter

from datakyt import schemas
from datakyt.api.crud import crud_router
from datakyt.services import entities

routers: list[APIRouter] = [
    crud_router(
        prefix="/offices",
        tag="offices",
        service=entities.offices,
        create_schema=schemas.OfficeCreate,
        update_schema=schemas.OfficeUpdate,
        read_schema=schemas.OfficeRead,
    ),
    crud_router(
        prefix="/projects",
        tag="projects",
        service=entities.projects,
        create_schema=schemas.ProjectCreate,
        update_schema=schemas.ProjectUpdate,
        read_schema=schemas.ProjectRead,
    ),
    crud_router(
        prefix="/types/equipment",
        tag="types",
        service=entities.equipment_types,
        create_schema=schemas.TypeCreate,
        update_schema=schemas.TypeUpdate,
        read_schema=schemas.TypeRead,
    ),
    crud_router(
        prefix="/types/furniture",
        tag="types",
        service=entities.furniture_types,
        create_schema=schemas.TypeCreate,
        update_schema=schemas.TypeUpdate,
        read_schema=schemas.TypeRead,
    ),
    crud_router(
        prefix="/employees",
        tag="employees",
        service=entities.employees,
        create_schema=schemas.EmployeeCreate,
        update_schema=schemas.EmployeeUpdate,
        read_schema=schemas.EmployeeRead,
    ),
    crud_router(
        prefix="/equipment-parts",
        tag="equipment",
        service=entities.equipment_parts,
        create_schema=schemas.EquipmentPartCreate,
        update_schema=schemas.EquipmentPartUpdate,
        read_schema=schemas.EquipmentPartRead,
    ),
    crud_router(
        prefix="/software",
        tag="software",
        service=entities.software,
        create_schema=schemas.SoftwareCreate,
        update_schema=schemas.SoftwareUpdate,
        read_schema=schemas.SoftwareRead,
    ),
    crud_router(
        prefix="/licenses",
        tag="licenses",
        service=entities.licenses,
        create_schema=schemas.LicenseCreate,
        update_schema=schemas.LicenseUpdate,
        read_schema=schemas.LicenseRead,
    ),
]
