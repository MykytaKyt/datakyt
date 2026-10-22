"""Reports, available as JSON, CSV or XLSX (``?format=``)."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from datakyt.api.deps import CurrentUser, SessionDep
from datakyt.api.files import OutputFormat, report_response
from datakyt.services import reports

router = APIRouter(prefix="/reports", tags=["reports"])

FormatParam = Annotated[OutputFormat, Query(alias="format")]
Days = Annotated[int, Query(ge=0, le=3650)]


@router.get("/inventory")
def inventory(session: SessionDep, user: CurrentUser, fmt: FormatParam = "json") -> Response:
    """Equipment counts grouped by office, type and status."""
    return report_response(reports.inventory(session), fmt, "inventory")


@router.get("/employee/{employee_id}")
def employee(
    session: SessionDep, user: CurrentUser, employee_id: int, fmt: FormatParam = "json"
) -> Response:
    """Everything currently issued to one employee."""
    return report_response(
        reports.employee_items(session, employee_id), fmt, f"employee-{employee_id}"
    )


@router.get("/licenses/expiring")
def expiring_licenses(
    session: SessionDep, user: CurrentUser, days: Days = 30, fmt: FormatParam = "json"
) -> Response:
    """Licenses expiring within ``days``."""
    return report_response(reports.expiring_licenses(session, days), fmt, "licenses-expiring")


@router.get("/warranty/expiring")
def expiring_warranties(
    session: SessionDep, user: CurrentUser, days: Days = 30, fmt: FormatParam = "json"
) -> Response:
    """Equipment and furniture whose warranty ends within ``days``."""
    return report_response(reports.expiring_warranties(session, days), fmt, "warranty-expiring")
