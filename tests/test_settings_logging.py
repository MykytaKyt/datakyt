import json
import logging

import pytest
from pydantic import ValidationError

from datakyt.logging import JsonFormatter, configure_logging, request_id_var
from datakyt.settings import Settings


def test_url_from_parts():
    settings = Settings(
        _env_file=None,
        database_url=None,
        db_host="db",
        db_port=6543,
        db_user="u",
        db_password="p@ss",
        db_name="n",
    )
    url = settings.sqlalchemy_url
    assert url.render_as_string(hide_password=False) == "postgresql+psycopg://u:p%40ss@db:6543/n"


def test_database_url_overrides_parts():
    settings = Settings(_env_file=None, database_url="postgresql+psycopg://x@h/d")
    assert settings.sqlalchemy_url == "postgresql+psycopg://x@h/d"


def test_jwt_secret_rules(monkeypatch):
    monkeypatch.delenv("DATAKYT_JWT_SECRET", raising=False)
    dev = Settings(_env_file=None, env="development")
    assert dev.resolved_jwt_secret() == dev.resolved_jwt_secret()
    assert len(dev.resolved_jwt_secret()) >= 32
    with pytest.raises(RuntimeError, match="DATAKYT_JWT_SECRET"):
        Settings(_env_file=None, env="production").resolved_jwt_secret()
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret="short")


def test_json_formatter_includes_request_id_and_extras():
    record = logging.makeLogRecord(
        {"name": "t", "levelname": "INFO", "msg": "hello %s", "args": ("x",), "status": 200}
    )
    token = request_id_var.set("rid-1")
    try:
        payload = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert payload["msg"] == "hello x"
    assert payload["request_id"] == "rid-1"
    assert payload["status"] == 200


def test_json_formatter_exceptions():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.makeLogRecord({"msg": "failed", "exc_info": sys.exc_info()})
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exc"]


def test_configure_logging_is_idempotent():
    configure_logging("debug")
    handlers = list(logging.getLogger().handlers)
    configure_logging("warning")
    assert logging.getLogger().handlers == handlers
    assert logging.getLogger().level == logging.WARNING


def test_unhandled_errors_return_500(app, client):
    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    response = client.get("/boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert "X-Request-ID" in response.headers


def test_health_reports_database_failure(app, anon_client, monkeypatch):
    from datakyt import db

    def broken(session):
        raise RuntimeError("down")

    monkeypatch.setattr(db, "ping", broken)
    response = anon_client.get("/health")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"
