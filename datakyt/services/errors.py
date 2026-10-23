"""Domain errors raised by services and translated to HTTP responses by the API."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError


class ServiceError(Exception):
    """Base class for expected, user-facing failures."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    """The request clashes with existing data (duplicates, references, state)."""

    status_code = 409


class InvalidInputError(ServiceError):
    status_code = 422


class AuthError(ServiceError):
    status_code = 401


_SQLSTATE_MESSAGES = {
    "23505": "a record with the same unique value already exists",
    "23503": "the record references a missing row or is still referenced by other rows",
    "23514": "a value violates a check constraint",
    "23502": "a required value is missing",
}


def integrity_message(exc: IntegrityError) -> str:
    """Build a readable message from a database integrity error."""
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None) or ""
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    base = _SQLSTATE_MESSAGES.get(sqlstate, "the change violates a database constraint")
    return f"{base} ({constraint})" if constraint else base


@contextmanager
def translate_integrity_errors() -> Iterator[None]:
    """Re-raise :class:`IntegrityError` as a :class:`ServiceError`."""
    try:
        yield
    except IntegrityError as exc:
        sqlstate = getattr(exc.orig, "sqlstate", None)
        error_cls = InvalidInputError if sqlstate in {"23514", "23502"} else ConflictError
        raise error_cls(integrity_message(exc)) from exc
