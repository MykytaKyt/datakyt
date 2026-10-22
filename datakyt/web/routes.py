"""Web UI routes under ``/ui``. Authentication uses an HTTP-only session cookie."""

from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from datakyt.api.deps import TOKEN_COOKIE, ForbiddenError, SessionDep
from datakyt.models import AppUser, Employee, EmployeeEquipment, ItemStatus, Role
from datakyt.services import assignments, entities, reports, users
from datakyt.services.assignments import RETURN_STATUSES
from datakyt.services.crud import ListParams
from datakyt.services.errors import AuthError, ServiceError
from datakyt.settings import get_settings
from datakyt.web.i18n import translate

WEB_DIR = Path(__file__).parent
PAGE_SIZE = 25

templates = Jinja2Templates(directory=WEB_DIR / "templates")
templates.env.globals["t"] = translate

router = APIRouter(prefix="/ui", include_in_schema=False)


class LoginRequiredError(Exception):
    """Raised when a UI page is requested without a valid session cookie."""


def login_redirect(request: Request, exc: Exception) -> Response:
    """Send the browser to the login page (HTMX requests get an ``HX-Redirect``)."""
    if request.headers.get("HX-Request"):
        return Response(status_code=204, headers={"HX-Redirect": "/ui/login"})
    return RedirectResponse("/ui/login", status_code=303)


def ui_user(request: Request, session: SessionDep) -> AppUser:
    token = request.cookies.get(TOKEN_COOKIE)
    if not token:
        raise LoginRequiredError
    try:
        return users.user_from_token(session, token)
    except AuthError as exc:
        raise LoginRequiredError from exc


def same_origin(request: Request) -> None:
    """Reject cross-site form posts (defense in depth on top of SameSite=Strict)."""
    origin = request.headers.get("origin")
    if origin and urlsplit(origin).netloc != request.url.netloc:
        raise ForbiddenError("cross-origin request rejected")


UiUser = Annotated[AppUser, Depends(ui_user)]


def ui_admin(user: UiUser) -> AppUser:
    if user.role != Role.ADMIN:
        raise ForbiddenError("admin role required")
    return user


UiAdmin = Annotated[AppUser, Depends(ui_admin)]
SameOrigin = Depends(same_origin)


def render(
    request: Request, name: str, context: dict[str, Any], status_code: int = 200
) -> Response:
    return templates.TemplateResponse(request, name, context, status_code=status_code)


@router.get("")
@router.get("/")
def index() -> Response:
    return RedirectResponse("/ui/equipment", status_code=303)


@router.get("/login")
def login_form(request: Request) -> Response:
    return render(request, "login.html", {"user": None})


@router.post("/login", dependencies=[SameOrigin])
def login(
    request: Request,
    session: SessionDep,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> Response:
    try:
        user = users.authenticate(session, email, password)
    except AuthError:
        return render(
            request, "login.html", {"user": None, "error": True, "email": email}, status_code=401
        )
    response = RedirectResponse("/ui/equipment", status_code=303)
    response.set_cookie(
        TOKEN_COOKIE,
        users.create_access_token(user),
        max_age=get_settings().jwt_ttl_minutes * 60,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
    )
    return response


@router.post("/logout", dependencies=[SameOrigin])
def logout() -> Response:
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie(TOKEN_COOKIE)
    return response


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


@router.get("/equipment")
def equipment_list(
    request: Request,
    session: SessionDep,
    user: UiUser,
    q: str | None = None,
    status: str | None = None,
    offset: int = 0,
) -> Response:
    chosen = ItemStatus(status) if status in set(ItemStatus) else None
    params = ListParams(
        offset=max(offset, 0),
        limit=PAGE_SIZE,
        q=q or None,
        sort="inventory_number",
        filters={"status": chosen},
    )
    page = entities.equipment.list_page(session, params)
    context = {
        "user": user,
        "page": page,
        "q": q,
        "status": chosen.value if chosen else None,
        "statuses": list(ItemStatus),
    }
    template = "_equipment_rows.html" if _is_htmx(request) else "equipment_list.html"
    return render(request, template, context)


def _equipment_context(session: Session, user: AppUser, item_id: int) -> dict[str, Any]:
    item = entities.equipment.get(session, item_id)
    history = list(
        session.scalars(
            select(EmployeeEquipment)
            .where(EmployeeEquipment.equipment_id == item_id)
            .order_by(EmployeeEquipment.issued_on.desc(), EmployeeEquipment.id.desc())
            .limit(20)
        )
    )
    holder = next((a for a in history if a.returned_on is None), None)
    employees = list(
        session.scalars(
            select(Employee).where(Employee.deleted_at.is_(None)).order_by(Employee.full_name)
        )
    )
    return {
        "user": user,
        "item": item,
        "history": history,
        "holder": holder,
        "employees": employees,
        "return_statuses": [s for s in ItemStatus if s in RETURN_STATUSES],
    }


@router.get("/equipment/{item_id}")
def equipment_detail(request: Request, session: SessionDep, user: UiUser, item_id: int) -> Response:
    return render(request, "equipment_detail.html", _equipment_context(session, user, item_id))


def _after_action(
    request: Request, session: SessionDep, user: AppUser, item_id: int, error: ServiceError | None
) -> Response:
    if error is None:
        return RedirectResponse(f"/ui/equipment/{item_id}", status_code=303)
    context = _equipment_context(session, user, item_id)
    context["error"] = error.message
    return render(request, "equipment_detail.html", context, status_code=error.status_code)


@router.post("/equipment/{item_id}/issue", dependencies=[SameOrigin])
def equipment_issue(
    request: Request,
    session: SessionDep,
    user: UiAdmin,
    item_id: int,
    employee_id: Annotated[int, Form()],
) -> Response:
    try:
        assignments.issue_equipment(session, item_id, employee_id, user)
    except ServiceError as exc:
        session.rollback()
        return _after_action(request, session, user, item_id, exc)
    return _after_action(request, session, user, item_id, None)


@router.post("/equipment/{item_id}/return", dependencies=[SameOrigin])
def equipment_return(
    request: Request,
    session: SessionDep,
    user: UiAdmin,
    item_id: int,
    status: Annotated[ItemStatus, Form()] = ItemStatus.RESERVED,
) -> Response:
    try:
        assignments.return_equipment(session, item_id, user, status=status)
    except ServiceError as exc:
        session.rollback()
        return _after_action(request, session, user, item_id, exc)
    return _after_action(request, session, user, item_id, None)


@router.get("/employees")
def employee_list(
    request: Request,
    session: SessionDep,
    user: UiUser,
    q: str | None = None,
    offset: int = 0,
) -> Response:
    params = ListParams(offset=max(offset, 0), limit=PAGE_SIZE, q=q or None, sort="full_name")
    page = entities.employees.list_page(session, params)
    context = {"user": user, "page": page, "q": q}
    template = "_employee_rows.html" if _is_htmx(request) else "employee_list.html"
    return render(request, template, context)


@router.get("/employees/{employee_id}")
def employee_detail(
    request: Request, session: SessionDep, user: UiUser, employee_id: int
) -> Response:
    employee = entities.employees.get(session, employee_id)
    items = reports.employee_items(session, employee_id).rows
    return render(
        request, "employee_detail.html", {"user": user, "employee": employee, "items": items}
    )


REPORT_LINKS = (
    ("reports.inventory", "/reports/inventory"),
    ("reports.licenses", "/reports/licenses/expiring?days=30"),
    ("reports.warranty", "/reports/warranty/expiring?days=30"),
)


@router.get("/reports")
def reports_page(request: Request, user: UiUser) -> Response:
    return render(request, "reports.html", {"user": user, "reports": REPORT_LINKS})
