"""Equipment and furniture: CRUD plus issue/return and printable labels."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from datakyt import labels, schemas
from datakyt.api.crud import crud_router
from datakyt.api.deps import AdminUser, CurrentUser, SessionDep
from datakyt.models import EmployeeEquipment, EmployeeFurniture, Equipment, Furniture
from datakyt.services import assignments, entities
from datakyt.services.errors import InvalidInputError, NotFoundError

equipment_router = crud_router(
    prefix="/equipment",
    tag="equipment",
    service=entities.equipment,
    create_schema=schemas.EquipmentCreate,
    update_schema=schemas.EquipmentUpdate,
    read_schema=schemas.EquipmentRead,
)
furniture_router = crud_router(
    prefix="/furniture",
    tag="furniture",
    service=entities.furniture,
    create_schema=schemas.FurnitureCreate,
    update_schema=schemas.FurnitureUpdate,
    read_schema=schemas.FurnitureRead,
)
labels_router = APIRouter(tags=["labels"])

PNG = "image/png"
PDF = "application/pdf"


@equipment_router.post(
    "/{item_id}/issue", response_model=schemas.EquipmentAssignmentRead, status_code=201
)
def issue_equipment(
    session: SessionDep, user: AdminUser, item_id: int, body: schemas.IssueRequest
) -> EmployeeEquipment:
    """Issue an available item to an employee; the item status becomes ``issued``."""
    return assignments.issue_equipment(session, item_id, body.employee_id, user, body.issued_on)


@equipment_router.post("/{item_id}/return", response_model=schemas.EquipmentAssignmentRead)
def return_equipment(
    session: SessionDep, user: AdminUser, item_id: int, body: schemas.ReturnRequest
) -> EmployeeEquipment:
    """Close the open assignment and set the item status (default ``reserved``)."""
    return assignments.return_equipment(session, item_id, user, body.returned_on, body.status)


@furniture_router.post(
    "/{item_id}/issue", response_model=schemas.FurnitureAssignmentRead, status_code=201
)
def issue_furniture(
    session: SessionDep, user: AdminUser, item_id: int, body: schemas.IssueRequest
) -> EmployeeFurniture:
    """Issue a furniture item to an employee."""
    return assignments.issue_furniture(session, item_id, body.employee_id, user, body.issued_on)


@furniture_router.post("/{item_id}/return", response_model=schemas.FurnitureAssignmentRead)
def return_furniture(
    session: SessionDep, user: AdminUser, item_id: int, body: schemas.ReturnRequest
) -> EmployeeFurniture:
    """Close the open assignment of a furniture item."""
    return assignments.return_furniture(session, item_id, user, body.returned_on)


def _label(item: Equipment | Furniture, kind: labels.Kind) -> labels.LabelData:
    return labels.LabelData(kind=kind, inventory_number=item.inventory_number, name=item.name)


@equipment_router.get("/{item_id}/label.png", response_class=Response)
def equipment_label(session: SessionDep, user: CurrentUser, item_id: int) -> Response:
    """Return a printable PNG label with a QR code."""
    item = entities.equipment.get(session, item_id)
    return Response(labels.label_png(_label(item, "equipment")), media_type=PNG)


@furniture_router.get("/{item_id}/label.png", response_class=Response)
def furniture_label(session: SessionDep, user: CurrentUser, item_id: int) -> Response:
    """Return a printable PNG label with a QR code."""
    item = entities.furniture.get(session, item_id)
    return Response(labels.label_png(_label(item, "furniture")), media_type=PNG)


def parse_ids(raw: str) -> list[int]:
    """Parse a comma-separated id list such as ``1,2,5``."""
    try:
        ids = [int(part) for part in raw.split(",") if part.strip()]
    except ValueError as exc:
        raise InvalidInputError("ids must be a comma-separated list of integers") from exc
    if not ids:
        raise InvalidInputError("ids must not be empty")
    if len(ids) > 480:
        raise InvalidInputError("at most 480 labels (20 pages) per request")
    return ids


@labels_router.get("/labels.pdf", response_class=Response)
def label_sheet(
    session: SessionDep,
    user: CurrentUser,
    ids: Annotated[str, Query(description="Comma-separated item ids, e.g. 1,2,3.")],
    kind: Annotated[labels.Kind, Query()] = "equipment",
) -> Response:
    """Return an A4 PDF with labels laid out in a 3x8 grid."""
    service = entities.equipment if kind == "equipment" else entities.furniture
    items: list[labels.LabelData] = []
    for item_id in parse_ids(ids):
        try:
            items.append(_label(service.get(session, item_id), kind))
        except NotFoundError as exc:
            raise InvalidInputError(exc.message) from exc
    return Response(
        labels.label_sheet_pdf(items),
        media_type=PDF,
        headers={"Content-Disposition": 'inline; filename="labels.pdf"'},
    )
