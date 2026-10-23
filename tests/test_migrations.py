"""Migrations must apply cleanly and match the models exactly."""

import uuid

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

from datakyt.cli import alembic_config
from datakyt.models import Base
from tests.conftest import admin_database_url


@pytest.fixture
def empty_database(database_url):
    name = f"datakyt_migrations_{uuid.uuid4().hex[:8]}"
    admin = create_engine(database_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    url = admin_database_url(database_url, name)
    engine = create_engine(url)
    yield engine
    engine.dispose()
    with admin.connect() as connection:
        connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    admin.dispose()


def _run(engine, action, revision):
    with engine.begin() as connection:
        config = alembic_config()
        config.attributes["connection"] = connection
        action(config, revision)


def test_upgrade_downgrade_upgrade(empty_database):
    _run(empty_database, command.upgrade, "head")
    tables = set(inspect(empty_database).get_table_names())
    assert set(Base.metadata.tables) <= tables

    _run(empty_database, command.downgrade, "base")
    assert inspect(empty_database).get_table_names() == ["alembic_version"]
    with empty_database.connect() as connection:
        enums = connection.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'")).all()
    assert enums == []

    _run(empty_database, command.upgrade, "head")


def test_models_match_migrations(engine):
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        diff = compare_metadata(context, Base.metadata)
    assert diff == []
