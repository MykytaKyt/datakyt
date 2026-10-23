"""Database engine and session management."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from datakyt.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    """Return the process-wide engine built from settings."""
    return create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    """Return a session factory bound to :func:`get_engine`."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """Yield a session for one unit of work (a request or a CLI command)."""
    with get_sessionmaker()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def ping(session: Session) -> None:
    """Raise if the database cannot answer a trivial query."""
    session.execute(text("SELECT 1"))
