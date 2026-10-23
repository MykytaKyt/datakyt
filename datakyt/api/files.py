"""Helpers for responses that can be JSON or a downloadable table."""

from typing import Any, Literal

from fastapi import Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from datakyt.services.reports import Report
from datakyt.services.tabular import MEDIA_TYPES, Format, write_table

OutputFormat = Literal["json", "csv", "xlsx"]


def file_response(content: bytes, fmt: Format, filename: str) -> Response:
    """Return ``content`` as an attachment named ``filename.<fmt>``."""
    return Response(
        content,
        media_type=MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}.{fmt}"'},
    )


def report_response(report: Report, fmt: OutputFormat, filename: str) -> Response:
    """Render a report as JSON rows or as a CSV/XLSX download."""
    if fmt == "json":
        content: Any = jsonable_encoder(report.rows)
        return JSONResponse(content)
    return file_response(write_table(report.rows, report.columns, fmt), fmt, filename)
