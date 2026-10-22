"""Command-line interface: ``datakyt --help``."""

import secrets
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config

from datakyt import backup as backups
from datakyt import seed as demo
from datakyt.db import get_sessionmaker
from datakyt.logging import configure_logging
from datakyt.models import Role
from datakyt.services import users
from datakyt.services.errors import ServiceError
from datakyt.settings import get_settings

app = typer.Typer(help="datakyt equipment accounting.", no_args_is_help=True)

PACKAGE_DIR = Path(__file__).resolve().parent


def alembic_config() -> Config:
    """Alembic configuration that works both from a checkout and an installed package."""
    config = Config()
    config.set_main_option("script_location", str(PACKAGE_DIR / "migrations"))
    config.attributes["configure_logger"] = False
    return config


@app.callback()
def main() -> None:
    configure_logging(get_settings().log_level)


@app.command()
def migrate(revision: Annotated[str, typer.Argument()] = "head") -> None:
    """Upgrade the database schema to REVISION (default: head)."""
    command.upgrade(alembic_config(), revision)
    typer.echo(f"database upgraded to {revision}")


@app.command()
def bootstrap() -> None:
    """Create the first admin user and, if DATAKYT_SEED_DEMO is set, demo data.

    Does nothing when users already exist. Without DATAKYT_ADMIN_PASSWORD a random
    password is generated and printed once.
    """
    settings = get_settings()
    email = settings.admin_email or "admin@example.com"
    generated = settings.admin_password is None
    password = (
        secrets.token_urlsafe(12)
        if settings.admin_password is None
        else settings.admin_password.get_secret_value()
    )
    with get_sessionmaker()() as session:
        user = users.ensure_admin(session, email, password)
        if user is None:
            typer.echo("users already exist; bootstrap skipped")
        else:
            typer.echo(f"created admin user {email}")
            if generated:
                typer.echo(f"generated password: {password}  (change it after first login)")
        if settings.seed_demo and not demo.has_data(session):
            counts = demo.seed(session)
            typer.echo(f"seeded demo data: {counts}")


@app.command()
def seed(
    if_empty: Annotated[
        bool, typer.Option("--if-empty", help="Skip silently when data exists.")
    ] = False,
) -> None:
    """Insert demo data (3 offices, 2 projects, 20 employees, 50 items)."""
    with get_sessionmaker()() as session:
        if demo.has_data(session):
            if if_empty:
                typer.echo("data already present; seed skipped")
                return
            typer.echo("refusing to seed: the database already has data", err=True)
            raise typer.Exit(1)
        typer.echo(f"seeded: {demo.seed(session)}")


@app.command("create-user")
def create_user(
    email: str,
    role: Annotated[Role, typer.Option(case_sensitive=False)] = Role.VIEWER,
    password: Annotated[
        str, typer.Option(prompt=True, hide_input=True, confirmation_prompt=True)
    ] = "",
) -> None:
    """Create an application user."""
    from datakyt.schemas import UserCreate

    data = UserCreate(email=email, password=password, role=role)
    with get_sessionmaker()() as session:
        try:
            users.users.create(session, data.model_dump(), None)
        except ServiceError as exc:
            typer.echo(f"error: {exc.message}", err=True)
            raise typer.Exit(1) from exc
    typer.echo(f"created {role.value} user {data.email}")


@app.command()
def backup(
    directory: Annotated[
        Path | None, typer.Option("--dir", help="Target directory (DATAKYT_BACKUP_DIR).")
    ] = None,
    keep: Annotated[
        int | None, typer.Option(min=1, help="Dumps to keep (DATAKYT_BACKUP_KEEP).")
    ] = None,
) -> None:
    """Dump the database with pg_dump and prune old dumps."""
    try:
        path = backups.create_backup(get_settings(), directory, keep)
    except backups.BackupError as exc:
        typer.echo(f"backup failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(str(path))


@app.command()
def restore(
    path: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    yes: Annotated[bool, typer.Option("--yes", help="Do not ask for confirmation.")] = False,
) -> None:
    """Replace the database contents with a dump created by `datakyt backup`."""
    if not yes:
        typer.confirm("This overwrites the current database. Continue?", abort=True)
    try:
        backups.restore_backup(get_settings(), path)
    except backups.BackupError as exc:
        typer.echo(f"restore failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"restored {path}")


@app.command()
def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1,
) -> None:
    """Run the web server."""
    import uvicorn

    uvicorn.run(
        "datakyt.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_config=None,
        proxy_headers=True,
    )
