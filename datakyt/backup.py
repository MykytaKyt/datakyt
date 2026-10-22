"""Database backups with ``pg_dump`` and restores with ``pg_restore``."""

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from datakyt.settings import Settings

BACKUP_PREFIX = "datakyt-"
BACKUP_SUFFIX = ".dump"


class BackupError(RuntimeError):
    """``pg_dump`` or ``pg_restore`` failed."""


def libpq_env(settings: Settings) -> dict[str, str]:
    """Build libpq environment variables so the password never appears in argv."""
    url = make_url(settings.sqlalchemy_url)
    env = dict(os.environ)
    for key, value in {
        "PGHOST": url.host,
        "PGPORT": str(url.port) if url.port else None,
        "PGUSER": url.username,
        "PGPASSWORD": url.password,
        "PGDATABASE": url.database,
    }.items():
        if value:
            env[key] = str(value)
    return env


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise BackupError(f"{name} not found on PATH; install the PostgreSQL client tools")
    return path


def _run(args: list[str], env: dict[str, str]) -> None:
    result = subprocess.run(args, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BackupError(f"{Path(args[0]).name} exited with {result.returncode}: {detail}")


def list_backups(directory: Path) -> list[Path]:
    """Return existing backups, oldest first."""
    return sorted(directory.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"))


def create_backup(
    settings: Settings,
    directory: Path | None = None,
    keep: int | None = None,
    now: datetime | None = None,
) -> Path:
    """Dump the database in custom format and keep only the newest ``keep`` dumps.

    Raises:
        BackupError: if ``pg_dump`` is missing or fails.
    """
    directory = directory or settings.backup_dir
    keep = keep if keep is not None else settings.backup_keep
    if keep < 1:
        raise ValueError("keep must be at least 1")
    directory.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    target = directory / f"{BACKUP_PREFIX}{stamp}{BACKUP_SUFFIX}"
    partial = target.with_suffix(".partial")
    try:
        _run(
            [_tool("pg_dump"), "--format=custom", "--no-owner", f"--file={partial}"],
            libpq_env(settings),
        )
    except BackupError:
        partial.unlink(missing_ok=True)
        raise
    partial.replace(target)
    for old in list_backups(directory)[:-keep]:
        old.unlink()
    return target


def restore_backup(settings: Settings, path: Path) -> None:
    """Replace the current database contents with a dump made by :func:`create_backup`.

    Raises:
        BackupError: if the file is missing or ``pg_restore`` fails.
    """
    if not path.is_file():
        raise BackupError(f"backup file {path} does not exist")
    env = libpq_env(settings)
    _run(
        [
            _tool("pg_restore"),
            "--clean",
            "--if-exists",
            "--no-owner",
            "--single-transaction",
            f"--dbname={env.get('PGDATABASE', '')}",
            str(path),
        ],
        env,
    )
