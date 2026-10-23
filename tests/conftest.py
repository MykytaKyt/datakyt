"""Test fixtures.

Tests run against a real PostgreSQL. Set ``DATAKYT_TEST_DATABASE_URL`` to use an
existing server (CI does this with a service container); otherwise a throwaway
``postgres:16-alpine`` container is started with testcontainers. The URL must point
at a database the tests may wipe, using a role that can create databases.
"""

import os
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from alembic import command
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from datakyt.cli import alembic_config
from datakyt.db import get_engine, get_session, get_sessionmaker
from datakyt.models import AppUser, Base, Employee, Equipment, Role
from datakyt.services import entities, users
from datakyt.settings import get_settings

ADMIN_PASSWORD = "admin-password"
VIEWER_PASSWORD = "viewer-password"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    url = os.environ.get("DATAKYT_TEST_DATABASE_URL")
    if url:
        yield url
        return
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine", driver="psycopg") as container:
        yield container.get_connection_url()


@pytest.fixture(scope="session", autouse=True)
def _settings_env(database_url: str) -> Iterator[None]:
    patch = pytest.MonkeyPatch()
    patch.setenv("DATAKYT_DATABASE_URL", database_url)
    patch.setenv("DATAKYT_ENV", "test")
    patch.setenv("DATAKYT_JWT_SECRET", "test-secret-test-secret-test-secret")
    patch.setenv("DATAKYT_LOG_LEVEL", "WARNING")
    for name in ("DATAKYT_ADMIN_EMAIL", "DATAKYT_ADMIN_PASSWORD", "DATAKYT_SEED_DEMO"):
        patch.delenv(name, raising=False)
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    yield
    patch.undo()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


def reset_schema(connection: Connection) -> None:
    """Drop everything in the public schema."""
    connection.execute(text("DROP SCHEMA public CASCADE"))
    connection.execute(text("CREATE SCHEMA public"))
    connection.commit()


@pytest.fixture(scope="session")
def engine(_settings_env: None, database_url: str) -> Iterator[Engine]:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        reset_schema(connection)
        config = alembic_config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        connection.commit()
    yield engine
    engine.dispose()
    get_engine().dispose()


@pytest.fixture
def connection(engine: Engine) -> Iterator[Connection]:
    with engine.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()


@pytest.fixture
def session(connection: Connection) -> Iterator[Session]:
    """A session whose commits become savepoints of an outer, rolled-back transaction."""
    with Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    ) as session:
        yield session


@pytest.fixture
def committed_db(engine: Engine) -> Iterator[None]:
    """For tests that commit through their own connections; truncates every table after."""
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def app(session: Session) -> Any:
    from datakyt.api.app import create_app

    application = create_app()

    def override() -> Iterator[Session]:
        try:
            yield session
        except Exception:
            session.rollback()
            raise

    application.dependency_overrides[get_session] = override
    return application


@pytest.fixture
def admin(session: Session) -> AppUser:
    return users.users.create(
        session,
        {"email": "admin@example.com", "password": ADMIN_PASSWORD, "role": Role.ADMIN},
        None,
    )


@pytest.fixture
def viewer(session: Session) -> AppUser:
    return users.users.create(
        session,
        {"email": "viewer@example.com", "password": VIEWER_PASSWORD, "role": Role.VIEWER},
        None,
    )


def _client(app: Any, user: AppUser | None) -> TestClient:
    client = TestClient(app)
    if user is not None:
        client.headers["Authorization"] = f"Bearer {users.create_access_token(user)}"
    return client


@pytest.fixture
def anon_client(app: Any) -> TestClient:
    return _client(app, None)


@pytest.fixture
def client(app: Any, admin: AppUser) -> TestClient:
    """Client authenticated as an admin."""
    return _client(app, admin)


@pytest.fixture
def viewer_client(app: Any, viewer: AppUser) -> TestClient:
    return _client(app, viewer)


class Factory:
    """Small helpers to create valid rows through the service layer."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self._n = 0

    def _next(self) -> int:
        self._n += 1
        return self._n

    def office(self, city: str | None = None) -> Any:
        return entities.offices.create(self.session, {"city": city or f"City {self._next()}"}, None)

    def project(self, name: str | None = None) -> Any:
        return entities.projects.create(
            self.session, {"name": name or f"Project {self._next()}"}, None
        )

    def equipment_type(self, name: str | None = None) -> Any:
        return entities.equipment_types.create(
            self.session, {"name": name or f"Type {self._next()}"}, None
        )

    def furniture_type(self, name: str | None = None) -> Any:
        return entities.furniture_types.create(
            self.session, {"name": name or f"Furniture type {self._next()}"}, None
        )

    def employee(self, **overrides: Any) -> Employee:
        n = self._next()
        data = {
            "full_name": f"Employee {n}",
            "email": f"employee{n}@example.com",
            "project_id": overrides.pop("project_id", None) or self.project().id,
            "office_id": overrides.pop("office_id", None) or self.office().id,
        }
        data.update(overrides)
        result: Employee = entities.employees.create(self.session, data, None)
        return result

    def equipment(self, **overrides: Any) -> Equipment:
        n = self._next()
        data = {
            "inventory_number": f"EQ-{n:05d}",
            "name": f"Laptop {n}",
            "serial_number": f"SN{n}",
            "warranty_months": 24,
            "cost": Decimal("1000.00"),
            "purchase_date": date(2026, 1, 15),
            "equipment_type_id": overrides.pop("equipment_type_id", None)
            or self.equipment_type().id,
            "office_id": overrides.pop("office_id", None) or self.office().id,
        }
        data.update(overrides)
        result: Equipment = entities.equipment.create(self.session, data, None)
        return result

    def furniture(self, **overrides: Any) -> Any:
        n = self._next()
        data = {
            "inventory_number": f"FU-{n:05d}",
            "name": f"Desk {n}",
            "warranty_months": 60,
            "cost": Decimal("300.00"),
            "purchase_date": date(2026, 1, 15),
            "furniture_type_id": overrides.pop("furniture_type_id", None)
            or self.furniture_type().id,
            "office_id": overrides.pop("office_id", None) or self.office().id,
        }
        data.update(overrides)
        return entities.furniture.create(self.session, data, None)

    def software(self, name: str | None = None) -> Any:
        return entities.software.create(
            self.session, {"name": name or f"Software {self._next()}"}, None
        )

    def license(self, **overrides: Any) -> Any:
        data = {
            "software_id": overrides.pop("software_id", None) or self.software().id,
            "seats": 2,
            "purchased_on": date(2026, 1, 1),
            "expires_on": date(2027, 1, 1),
        }
        data.update(overrides)
        return entities.licenses.create(self.session, data, None)


@pytest.fixture
def factory(session: Session) -> Factory:
    return Factory(session)


def admin_database_url(database_url: str, database: str) -> str:
    """Return ``database_url`` pointing at another database on the same server."""
    return make_url(database_url).set(database=database).render_as_string(hide_password=False)
