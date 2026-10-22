"""Bulk export and import of entities as CSV or XLSX."""

from pathlib import PurePath
from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile

from datakyt import schemas
from datakyt.api.deps import AdminUser, CurrentUser, SessionDep
from datakyt.api.files import file_response
from datakyt.services import transfer
from datakyt.services.errors import InvalidInputError
from datakyt.services.tabular import Format

router = APIRouter(tags=["import/export"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ENTITY_NAMES = ", ".join(transfer.ENTITIES)


@router.get(
    "/export/{entity}.{fmt}",
    response_class=Response,
    description=f"Download all rows of an entity. Entities: {ENTITY_NAMES}.",
)
def export(session: SessionDep, user: CurrentUser, entity: str, fmt: Format) -> Response:
    """Export one entity."""
    return file_response(transfer.export(session, entity, fmt), fmt, entity)


def _upload_format(upload: UploadFile) -> Format:
    suffix = PurePath(upload.filename or "").suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".xlsx":
        return "xlsx"
    raise InvalidInputError("upload a .csv or .xlsx file")


@router.post(
    "/import/{entity}",
    response_model=schemas.ImportResult,
    description=(
        "Import rows from a CSV or XLSX file whose header row names the entity's fields. "
        "With dry_run=true (the default) nothing is written and per-row errors are returned. "
        f"Entities: {ENTITY_NAMES}."
    ),
)
def import_entity(
    session: SessionDep,
    user: AdminUser,
    entity: str,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()] = True,
) -> schemas.ImportResult:
    """Validate and (unless ``dry_run``) import rows."""
    transfer.get_entity(entity)
    fmt = _upload_format(file)
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidInputError("file is larger than 10 MB")
    return transfer.import_rows(session, entity, data, fmt, user, dry_run=dry_run)
