"""Login and user management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from datakyt import schemas
from datakyt.api.crud import crud_router
from datakyt.api.deps import CurrentUser, SessionDep, require_role
from datakyt.models import AppUser, Role
from datakyt.services import users

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=schemas.Token)
def login(
    session: SessionDep, form: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> schemas.Token:
    """Exchange e-mail (``username`` field) and password for a bearer token."""
    user = users.authenticate(session, form.username, form.password)
    return schemas.Token(access_token=users.create_access_token(user))


@router.get("/auth/me", response_model=schemas.UserRead)
def me(user: CurrentUser) -> AppUser:
    """Return the authenticated user."""
    return user


users_router = crud_router(
    prefix="/users",
    tag="users",
    service=users.users,
    create_schema=schemas.UserCreate,
    update_schema=schemas.UserUpdate,
    read_schema=schemas.UserRead,
    # Listing and reading user accounts is limited to admins as well.
    dependencies=[Depends(require_role(Role.ADMIN))],
)
