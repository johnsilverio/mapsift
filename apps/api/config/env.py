"""The environment as a validated boundary (I5, C5, ADR-0001 section 4).

Holds no Django import, which is what keeps it testable without a settings module.
"""

from typing import Annotated

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Environment(BaseSettings):
    """Everything the API reads from its environment, validated once at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    secret_key: SecretStr

    # The scheme is `postgresql://`, never `postgis://`: PostGIS is selected by the ENGINE below.
    database_url: PostgresDsn

    debug: bool = False

    # `NoDecode` is load-bearing: without it pydantic-settings JSON-decodes the raw value before
    # any validator runs, so the comma-separated form an operator writes fails before the split.
    allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    def django_database(self) -> dict[str, str]:
        """Translate the validated URL into Django's connection settings."""
        # This type is a multi-host URL, so credentials live per host and there is no `.username`
        # or `.host` on the URL itself.
        host = self.database_url.hosts()[0]
        port = host["port"]
        return {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            # A path of `/mapsift` would ask PostgreSQL for a database named `/mapsift`.
            "NAME": (self.database_url.path or "").removeprefix("/"),
            "USER": host["username"] or "",
            "PASSWORD": host["password"] or "",
            "HOST": host["host"] or "",
            "PORT": str(port) if port else "",
        }
