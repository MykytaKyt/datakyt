"""Router factory producing list/get/create/update/delete endpoints for an entity."""

import inspect
from collections.abc import Callable, Sequence
from typing import Any

from fastapi import APIRouter, Query, Response, status
from fastapi.params import Depends as DependsMarker
from pydantic import BaseModel

from datakyt.api.deps import AdminUser, CurrentUser, SessionDep
from datakyt.services.crud import CrudService, ListParams


class PageOut[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int


def _with_params(func: Callable[..., Any], params: list[inspect.Parameter]) -> Callable[..., Any]:
    """Give ``func`` an explicit signature so FastAPI can build docs and validation."""
    func.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    return func


def _param(name: str, annotation: Any, default: Any = inspect.Parameter.empty) -> inspect.Parameter:
    return inspect.Parameter(
        name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation, default=default
    )


def crud_router(
    *,
    prefix: str,
    tag: str,
    service: CrudService[Any],
    create_schema: type[BaseModel],
    update_schema: type[BaseModel],
    read_schema: type[BaseModel],
    dependencies: Sequence[DependsMarker] = (),
) -> APIRouter:
    """Build a router with the five standard endpoints for ``service``.

    Reads are open to every authenticated user; writes require the admin role.
    Extra ``dependencies`` apply to every endpoint of the router.
    """
    router = APIRouter(prefix=prefix, tags=[tag], dependencies=list(dependencies))
    page_schema = PageOut[read_schema]  # type: ignore[valid-type]
    table = service.model.__table__
    filter_types = {name: table.c[name].type.python_type for name in service.filter_fields}

    def list_items(**kwargs: Any) -> Any:
        session = kwargs.pop("session")
        kwargs.pop("user")
        params = ListParams(
            offset=kwargs.pop("offset"),
            limit=kwargs.pop("limit"),
            q=kwargs.pop("q"),
            sort=kwargs.pop("sort"),
            filters=kwargs,
        )
        page = service.list_page(session, params)
        return {
            "items": page.items,
            "total": page.total,
            "offset": page.offset,
            "limit": page.limit,
        }

    sortable = ", ".join(("id", *service.sort_fields))
    router.add_api_route(
        "",
        _with_params(
            list_items,
            [
                _param("session", SessionDep),
                _param("user", CurrentUser),
                _param("offset", int, Query(0, ge=0)),
                _param("limit", int, Query(50, ge=1, le=500)),
                _param("q", str | None, Query(None, description="Case-insensitive text search.")),
                _param(
                    "sort",
                    str | None,
                    Query(None, description=f"One of: {sortable}. Prefix with '-' to reverse."),
                ),
                *(_param(name, typ | None, Query(None)) for name, typ in filter_types.items()),
            ],
        ),
        methods=["GET"],
        response_model=page_schema,
        summary=f"List {tag}",
    )

    def get_item(*, session: Any, user: Any, item_id: int) -> Any:
        return service.get(session, item_id)

    router.add_api_route(
        "/{item_id}",
        _with_params(
            get_item,
            [_param("session", SessionDep), _param("user", CurrentUser), _param("item_id", int)],
        ),
        methods=["GET"],
        response_model=read_schema,
        summary=f"Get one {tag} item",
    )

    def create_item(*, session: Any, user: Any, body: BaseModel) -> Any:
        return service.create(session, body.model_dump(exclude_unset=True), user)

    router.add_api_route(
        "",
        _with_params(
            create_item,
            [
                _param("session", SessionDep),
                _param("user", AdminUser),
                _param("body", create_schema),
            ],
        ),
        methods=["POST"],
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        summary=f"Create a {tag} item",
    )

    def update_item(*, session: Any, user: Any, item_id: int, body: BaseModel) -> Any:
        return service.update(session, item_id, body.model_dump(exclude_unset=True), user)

    router.add_api_route(
        "/{item_id}",
        _with_params(
            update_item,
            [
                _param("session", SessionDep),
                _param("user", AdminUser),
                _param("item_id", int),
                _param("body", update_schema),
            ],
        ),
        methods=["PATCH"],
        response_model=read_schema,
        summary=f"Update a {tag} item",
    )

    def delete_item(*, session: Any, user: Any, item_id: int) -> Response:
        service.delete(session, item_id, user)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    router.add_api_route(
        "/{item_id}",
        _with_params(
            delete_item,
            [_param("session", SessionDep), _param("user", AdminUser), _param("item_id", int)],
        ),
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        summary=f"Delete a {tag} item" + (" (soft delete)" if service.soft_delete else ""),
    )
    return router
