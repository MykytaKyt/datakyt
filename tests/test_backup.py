import shutil
import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text

from datakyt import backup
from datakyt.settings import Settings, get_settings

needs_pg_tools = pytest.mark.skipif(
    shutil.which("pg_dump") is None or shutil.which("pg_restore") is None,
    reason="PostgreSQL client tools are not installed",
)


def test_password_goes_to_env_not_argv(monkeypatch, tmp_path):
    calls = []

    def fake_run(args, env, **kwargs):
        calls.append((args, env))
        target = next(a for a in args if a.startswith("--file=")).removeprefix("--file=")
        open(target, "wb").close()
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(backup.subprocess, "run", fake_run)
    monkeypatch.setattr(backup, "_tool", lambda name: f"/usr/bin/{name}")
    settings = Settings(
        database_url=None, db_password="s3cr3t!@#", db_host="db", db_port=5433, _env_file=None
    )
    path = backup.create_backup(settings, tmp_path, keep=1)
    assert path.exists()
    args, env = calls[0]
    assert not any("s3cr3t" in arg for arg in args)
    assert env["PGPASSWORD"] == "s3cr3t!@#"
    assert env["PGHOST"] == "db"
    assert env["PGPORT"] == "5433"


def test_failure_raises_and_cleans_up(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, "_tool", lambda name: "/bin/false")
    with pytest.raises(backup.BackupError, match="exited with 1"):
        backup.create_backup(get_settings(), tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_missing_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(backup.shutil, "which", lambda name: None)
    with pytest.raises(backup.BackupError, match="pg_dump not found"):
        backup.create_backup(get_settings(), tmp_path)


def test_keep_must_be_positive(tmp_path):
    with pytest.raises(ValueError):
        backup.create_backup(get_settings(), tmp_path, keep=0)


def test_restore_missing_file(tmp_path):
    with pytest.raises(backup.BackupError, match="does not exist"):
        backup.restore_backup(get_settings(), tmp_path / "nope.dump")


@needs_pg_tools
def test_backup_restore_round_trip(tmp_path, database_url, committed_db, engine):
    settings = get_settings()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO office (city) VALUES ('Backup City')"))

    start = datetime(2026, 1, 1, tzinfo=UTC)
    paths = [
        backup.create_backup(settings, tmp_path, keep=2, now=start + timedelta(minutes=i))
        for i in range(3)
    ]
    assert backup.list_backups(tmp_path) == paths[1:]

    with engine.begin() as connection:
        connection.execute(text("DELETE FROM office"))
    backup.restore_backup(settings, paths[-1])

    check = create_engine(database_url)
    with check.connect() as connection:
        cities = connection.execute(text("SELECT city FROM office")).scalars().all()
    check.dispose()
    assert cities == ["Backup City"]
