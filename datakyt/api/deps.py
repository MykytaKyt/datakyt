"""Shared FastAPI dependencies: database session, current user and role checks."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from datakyt.db import get_session
from datakyt.models import AppUser, Role
from datakyt.services import users
from datakyt.services.errors import AuthError, ServiceError

TOKEN_COOKIE = "datakyt_token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

SessionDep = Annotated[Session, Depends(get_session)]


class ForbiddenError(ServiceError):
    status_code = 403


def current_user(
    request: Request,
    session: SessionDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> AppUser:
    """Resolve the user from a bearer token or, for the web UI, the session cookie."""
    token = token or request.cookies.get(TOKEN_COOKIE)
    if not token:
        raise AuthError("not authenticated")
    return users.user_from_token(session, token)


def require_role(role: Role) -> Callable[[AppUser], AppUser]:
    """Return a dependency that allows only users with ``role`` (admins pass every check)."""

    def check(user: Annotated[AppUser, Depends(current_user)]) -> AppUser:
        if user.role != role and user.role != Role.ADMIN:
            raise ForbiddenError(f"{role.value} role required")
        return user

    return check


CurrentUser = Annotated[AppUser, Depends(current_user)]
AdminUser = Annotated[AppUser, Depends(require_role(Role.ADMIN))]
