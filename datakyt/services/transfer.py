"""Bulk CSV/XLSX export and import for every CRUD entity."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from datakyt import schemas
from datakyt.models import AppUser
from datakyt.services import entities
from datakyt.services.crud import CrudService
from datakyt.services.errors import InvalidInputError, NotFoundError, ServiceError
from datakyt.services.tabular import Format, read_table, write_table

MAX_IMPORT_ROWS = 10_000


@dataclass(frozen=True)
class Entity:
    service: CrudService[Any]
    create_schema: type[BaseModel]


ENTITIES: dict[str, Entity] = {
    "offices": Entity(entities.offices, schemas.OfficeCreate),
    "projects": Entity(entities.projects, schemas.ProjectCreate),
    "equipment-types": Entity(entities.equipment_types, schemas.TypeCreate),
    "furniture-types": Entity(entities.furniture_types, schemas.TypeCreate),
    "employees": Entity(entities.employees, schemas.EmployeeCreate),
    "equipment": Entity(entities.equipment, schemas.EquipmentCreate),
    "equipment-parts": Entity(entities.equipment_parts, schemas.EquipmentPartCreate),
    "furniture": Entity(entities.furniture, schemas.FurnitureCreate),
    "software": Entity(entities.software, schemas.SoftwareCreate),
    "licenses": Entity(entities.licenses, schemas.LicenseCreate),
}

_HIDDEN_COLUMNS = {"deleted_at"}


def get_entity(name: str) -> Entity:
    """Look up an importable/exportable entity by its URL name."""
    try:
        return ENTITIES[name]
    except KeyError:
        raise NotFoundError(f"unknown entity {name!r}") from None


def export_columns(entity: Entity) -> tuple[str, ...]:
    """Columns written by :func:`export`, in table order."""
    mapper = inspect(entity.service.model)
    return tuple(c.key for c in mapper.column_attrs if c.key not in _HIDDEN_COLUMNS)


def export(session: Session, name: str, fmt: Format) -> bytes:
    """Serialize every visible row of an entity."""
    entity = get_entity(name)
    columns = export_columns(entity)
    stmt = entity.service.base_query().order_by(entity.service.model.id)
    rows = ({c: getattr(obj, c) for c in columns} for obj in session.scalars(stmt))
    return write_table(rows, columns, fmt)


def _format_validation(exc: ValidationError) -> list[str]:
    return [
        f"{'.'.join(str(p) for p in err['loc']) or 'row'}: {err['msg']}" for err in exc.errors()
    ]


def import_rows(
    session: Session,
    name: str,
    data: bytes,
    fmt: Format,
    actor: AppUser | None,
    *,
    dry_run: bool,
) -> schemas.ImportResult:
    """Validate and insert rows from an uploaded file.

    Every row is inserted inside its own savepoint so that database errors
    (duplicates, unknown references) are reported per row. Nothing is committed
    when ``dry_run`` is set or when any row fails.
    """
    entity = get_entity(name)
    rows = read_table(data, fmt)
    if len(rows) > MAX_IMPORT_ROWS:
        raise InvalidInputError(f"at most {MAX_IMPORT_ROWS} rows can be imported at once")

    errors: list[schemas.RowError] = []
    for number, raw in enumerate(rows, start=1):
        raw.pop("id", None)
        for column in ("created_at", "updated_at", *_HIDDEN_COLUMNS):
            raw.pop(column, None)
        try:
            values = entity.create_schema.model_validate(raw).model_dump(exclude_unset=True)
        except ValidationError as exc:
            errors.append(schemas.RowError(row=number, errors=_format_validation(exc)))
            continue
        savepoint = session.begin_nested()
        try:
            entity.service.add(session, values, actor)
        except ServiceError as exc:
            savepoint.rollback()
            errors.append(schemas.RowError(row=number, errors=[exc.message]))
        else:
            savepoint.commit()

    imported = 0
    if dry_run or errors:
        session.rollback()
    else:
        session.commit()
        imported = len(rows)
    return schemas.ImportResult(
        dry_run=dry_run, total_rows=len(rows), imported=imported, errors=errors
    )
