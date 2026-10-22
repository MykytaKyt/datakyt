"""FastAPI application factory."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from datakyt import __version__
from datakyt.api.routers import assignments, auth, entities, items, ops, reports, transfer
from datakyt.logging import configure_logging, request_id_var
from datakyt.services.errors import AuthError, ServiceError
from datakyt.settings import get_settings
from datakyt.web import routes as web

logger = logging.getLogger("datakyt.access")

REQUEST_ID_HEADER = "X-Request-ID"


def create_app() -> FastAPI:
    """Build the application with all routers, middleware and error handlers."""
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.resolved_jwt_secret()  # fail fast in production without a secret

    app = FastAPI(
        title="datakyt",
        version=__version__,
        description="Equipment accounting: employees, equipment, furniture and licenses.",
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if 0 < len(incoming) <= 64 else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled error", extra={"path": request.url.path})
            response = JSONResponse({"detail": "internal server error"}, status_code=500)
        finally:
            request_id_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return response

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthError) else None
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code, headers=headers)

    app.include_router(ops.router)
    app.include_router(auth.router)
    app.include_router(auth.users_router)
    for router in entities.routers:
        app.include_router(router)
    app.include_router(items.equipment_router)
    app.include_router(items.furniture_router)
    app.include_router(items.labels_router)
    app.include_router(assignments.router)
    app.include_router(reports.router)
    app.include_router(transfer.router)

    app.include_router(web.router)
    app.add_exception_handler(web.LoginRequiredError, web.login_redirect)
    app.mount("/static", StaticFiles(directory=web.WEB_DIR / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/ui/", status_code=307)

    return app
