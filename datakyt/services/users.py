"""Application users, password hashing and access tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from datakyt.models import AppUser, Role
from datakyt.services import audit
from datakyt.services.crud import CrudService
from datakyt.services.errors import AuthError, translate_integrity_errors
from datakyt.settings import get_settings

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Return a bcrypt hash of ``password``."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Check ``password`` against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


# Compared against when the e-mail is unknown, so both paths take the same time.
_DUMMY_HASH = hash_password("timing-equalizer")


def authenticate(session: Session, email: str, password: str) -> AppUser:
    """Return the active user with these credentials or raise :class:`AuthError`."""
    user = session.scalar(select(AppUser).where(AppUser.email == email.lower()))
    if user is None:
        verify_password(password, _DUMMY_HASH)
        raise AuthError("incorrect e-mail or password")
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise AuthError("incorrect e-mail or password")
    return user


def create_access_token(user: AppUser, now: datetime | None = None) -> str:
    """Issue a signed JWT for ``user``."""
    settings = get_settings()
    issued = now or datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "iat": issued,
        "exp": issued + timedelta(minutes=settings.jwt_ttl_minutes),
    }
    return jwt.encode(payload, settings.resolved_jwt_secret(), algorithm=JWT_ALGORITHM)


def user_from_token(session: Session, token: str) -> AppUser:
    """Resolve a bearer token to an active user or raise :class:`AuthError`."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            get_settings().resolved_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise AuthError("invalid or expired token") from exc
    user = session.get(AppUser, user_id)
    if user is None or not user.is_active:
        raise AuthError("invalid or expired token")
    return user


class UserService(CrudService[AppUser]):
    """Users are created and updated with a plain password that is hashed here."""

    def add(self, session: Session, data: Any, actor: AppUser | None) -> AppUser:
        values = dict(data)
        password = values.pop("password")
        user = AppUser(**values, password_hash=hash_password(password))
        session.add(user)
        with translate_integrity_errors():
            session.flush()
        audit.record(session, actor, "create", self.entity, user.id, {"email": user.email})
        return user

    def update(self, session: Session, obj_id: int, data: Any, actor: AppUser | None) -> AppUser:
        values = dict(data)
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        user = super().update(session, obj_id, values, actor)
        return user


users = UserService(
    AppUser,
    entity="app_user",
    search_fields=("email",),
    filter_fields=("role", "is_active"),
    sort_fields=("email", "created_at"),
)


def count_users(session: Session) -> int:
    """Return how many users exist."""
    return session.scalar(select(func.count()).select_from(AppUser)) or 0


def ensure_admin(session: Session, email: str, password: str) -> AppUser | None:
    """Create the first admin user if the table is empty; return it, or ``None`` if skipped."""
    if count_users(session) > 0:
        return None
    user = users.create(
        session, {"email": email.lower(), "password": password, "role": Role.ADMIN}, None
    )
    return user
