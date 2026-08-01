"""The environment as a validated boundary.

`CLAUDE.md` names config among the places Pydantic validates (I5, C5), and ADR-0001 section 4
requires configuration to come from the environment rather than from a checked-in file with
real values. This module is that contract in one place: what the service needs to run, typed,
with no silent fallback for anything whose absence should stop the process.

It deliberately holds no Django import, which is what keeps it a pure decision testable
without a settings module, a database, or a network (`specs/testing.md` section 3).
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
    """No default on purpose. A secret with a fallback is a secret that ships by accident."""

    database_url: PostgresDsn
    """The scheme is `postgresql://`, never `postgis://`, which this type rejects.

    PostGIS is selected by Django's database ENGINE, not by the URL scheme, and the two are
    easy to confuse because the ratified database is always spoken of as PostgreSQL plus
    PostGIS. Also no default: the ratified database is PostgreSQL 18 with PostGIS, so there
    is no local fallback to quietly fall into.
    """

    debug: bool = False
    """Off unless the environment turns it on, so forgetting the variable cannot expose a trace."""

    allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)
    """`NoDecode` is load-bearing rather than decorative.

    Without it this library JSON-decodes the raw value before any validator runs, so the
    comma-separated form an operator actually writes in a .env file fails before the splitting
    below ever gets a chance.
    """

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [host.strip() for host in value.split(",") if host.strip()]
        return value

    def django_database(self) -> dict[str, str]:
        """Translate the validated URL into the connection settings Django expects.

        Kept here rather than inside the settings module so it stays a pure decision with a
        test, which is the split `specs/testing.md` section 3 asks for: the decision is a
        function over plain data, and the settings module only wires the result.

        The ENGINE is the PostGIS backend because the ratified database is PostgreSQL with
        PostGIS. `django.contrib.gis` is deliberately not in INSTALLED_APPS yet: it needs GDAL
        and GEOS present at import, there is no geometry model to serve, and the developer
        host is not required to carry those libraries (ADR-0001 section 3 puts running in the
        container and authoring on the host).
        """
        # This type is a multi-host URL, so the credentials live per host rather than on the
        # URL object: there is no `.username` or `.host` to read directly. Mapsift connects to
        # one database, so the first host is the whole story.
        host = self.database_url.hosts()[0]
        port = host["port"]
        return {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            # A path of `/mapsift` asks PostgreSQL for a database literally named `/mapsift`,
            # and the failure surfaces at connection time rather than here.
            "NAME": (self.database_url.path or "").removeprefix("/"),
            "USER": host["username"] or "",
            "PASSWORD": host["password"] or "",
            "HOST": host["host"] or "",
            # Empty means "let the driver use its default", which is a decision, not a gap.
            "PORT": str(port) if port else "",
        }
