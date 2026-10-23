from typer.testing import CliRunner

from datakyt import cli
from datakyt.db import get_sessionmaker
from datakyt.models import AppUser, Employee
from datakyt.settings import get_settings

runner = CliRunner()


def invoke(*args, **kwargs):
    return runner.invoke(cli.app, list(args), catch_exceptions=False, **kwargs)


def test_migrate_is_idempotent(engine):
    result = invoke("migrate")
    assert result.exit_code == 0
    assert "upgraded to head" in result.output


def test_bootstrap_creates_admin_once(committed_db, monkeypatch):
    monkeypatch.setenv("DATAKYT_ADMIN_EMAIL", "root@example.com")
    monkeypatch.setenv("DATAKYT_SEED_DEMO", "true")
    get_settings.cache_clear()
    try:
        first = invoke("bootstrap")
        assert "created admin user root@example.com" in first.output
        assert "generated password:" in first.output
        assert "seeded demo data" in first.output
        second = invoke("bootstrap")
        assert "bootstrap skipped" in second.output
    finally:
        get_settings.cache_clear()
    with get_sessionmaker()() as session:
        assert session.query(AppUser).count() == 1
        assert session.query(Employee).count() == 20


def test_bootstrap_with_given_password(committed_db, monkeypatch):
    monkeypatch.setenv("DATAKYT_ADMIN_PASSWORD", "given-password")
    get_settings.cache_clear()
    try:
        result = invoke("bootstrap")
    finally:
        get_settings.cache_clear()
    assert "created admin user admin@example.com" in result.output
    assert "generated password" not in result.output


def test_seed_refuses_existing_data(committed_db):
    assert invoke("seed").exit_code == 0
    again = runner.invoke(cli.app, ["seed"])
    assert again.exit_code == 1
    assert "already has data" in again.output
    skipped = invoke("seed", "--if-empty")
    assert skipped.exit_code == 0
    assert "skipped" in skipped.output


def test_create_user(committed_db):
    result = invoke(
        "create-user", "Ops@Example.com", "--role", "admin", "--password", "password123"
    )
    assert result.exit_code == 0
    assert "created admin user ops@example.com" in result.output
    duplicate = runner.invoke(
        cli.app, ["create-user", "ops@example.com", "--password", "password123"]
    )
    assert duplicate.exit_code == 1
    assert "already exists" in duplicate.output


def test_backup_and_restore_commands(committed_db, tmp_path, monkeypatch):
    result = invoke("backup", "--dir", str(tmp_path), "--keep", "1")
    assert result.exit_code == 0
    dump = tmp_path / result.output.strip().split("/")[-1]
    assert dump.exists()
    restored = invoke("restore", str(dump), "--yes")
    assert restored.exit_code == 0
    aborted = runner.invoke(cli.app, ["restore", str(dump)], input="n\n")
    assert aborted.exit_code == 1


def test_backup_failure_exit_code(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise cli.backups.BackupError("pg_dump exited with 1: nope")

    monkeypatch.setattr(cli.backups, "create_backup", boom)
    monkeypatch.setattr(cli.backups, "restore_backup", boom)
    result = runner.invoke(cli.app, ["backup"])
    assert result.exit_code == 1
    assert "backup failed" in result.output
    dump = tmp_path / "x.dump"
    dump.write_bytes(b"")
    result = runner.invoke(cli.app, ["restore", str(dump), "--yes"])
    assert result.exit_code == 1
    assert "restore failed" in result.output


def test_serve_passes_options(monkeypatch):
    calls = {}
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: calls.update(k))
    assert invoke("serve", "--port", "9000").exit_code == 0
    assert calls["port"] == 9000
    assert calls["factory"] is True


def test_bootstrap_rejects_weak_password(monkeypatch):
    monkeypatch.setenv("DATAKYT_ADMIN_PASSWORD", "short")
    get_settings.cache_clear()
    try:
        result = runner.invoke(cli.app, ["bootstrap"])
    finally:
        get_settings.cache_clear()
    assert result.exit_code == 1
    assert "DATAKYT_ADMIN_PASSWORD" in result.output


def test_empty_env_values_are_ignored(monkeypatch):
    monkeypatch.setenv("DATAKYT_ADMIN_PASSWORD", "")
    get_settings.cache_clear()
    try:
        assert get_settings().admin_password is None
    finally:
        get_settings.cache_clear()
