"""Application settings read from ``DATAKYT_*`` environment variables."""

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Runtime configuration.

    Every field can be overridden with an environment variable named
    ``DATAKYT_<FIELD>`` or with a line in a ``.env`` file in the working directory.
    """

    model_config = SettingsConfigDict(env_prefix="DATAKYT_", env_file=".env", extra="ignore")

    env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "datakyt"
    db_user: str = "datakyt"
    db_password: SecretStr = SecretStr("")
    database_url: SecretStr | None = Field(
        default=None,
        description="Full SQLAlchemy URL; overrides the db_* fields when set.",
    )

    jwt_secret: SecretStr | None = Field(default=None, min_length=32)
    jwt_ttl_minutes: int = 8 * 60

    admin_email: str | None = None
    admin_password: SecretStr | None = None
    seed_demo: bool = False

    backup_dir: Path = Path("backups")
    backup_keep: int = Field(default=7, ge=1)

    @property
    def sqlalchemy_url(self) -> URL | str:
        """Return the URL SQLAlchemy should connect to."""
        if self.database_url is not None:
            return self.database_url.get_secret_value()
        return URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value() or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    def resolved_jwt_secret(self) -> str:
        """Return the JWT signing key, generating an ephemeral one outside production."""
        if self.jwt_secret is not None:
            return self.jwt_secret.get_secret_value()
        if self.env == "production":
            raise RuntimeError("DATAKYT_JWT_SECRET must be set when DATAKYT_ENV=production")
        return _ephemeral_secret()


@lru_cache
def _ephemeral_secret() -> str:
    return secrets.token_urlsafe(32)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
