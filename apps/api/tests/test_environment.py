"""Covers I5 and C5 (Pydantic at every boundary, config among them), ADR-0001 section 4 and N3."""

import pytest
from pydantic import ValidationError

from config.env import Environment

VALID_DATABASE_URL = "postgresql://mapsift:secret@db:5432/mapsift"


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("SECRET_KEY", "DATABASE_URL", "DEBUG", "ALLOWED_HOSTS"):
        monkeypatch.delenv(name, raising=False)


def _failing_fields(error: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    return {str(detail["loc"][0]) for detail in error.value.errors()}


def test_a_missing_secret_key_is_rejected_rather_than_defaulted() -> None:
    with pytest.raises(ValidationError) as error:
        Environment(_env_file=None, database_url=VALID_DATABASE_URL)

    assert _failing_fields(error) == {"secret_key"}


def test_a_missing_database_url_is_rejected_rather_than_defaulted() -> None:
    with pytest.raises(ValidationError) as error:
        Environment(_env_file=None, secret_key="test-only-not-a-real-key")

    assert _failing_fields(error) == {"database_url"}


def test_debug_is_off_unless_the_environment_turns_it_on() -> None:
    off = Environment(
        _env_file=None, secret_key="test-only-not-a-real-key", database_url=VALID_DATABASE_URL
    )
    assert off.debug is False

    on = Environment(
        _env_file=None,
        secret_key="test-only-not-a-real-key",
        database_url=VALID_DATABASE_URL,
        debug="true",
    )
    assert on.debug is True


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("sqlite:///db.sqlite3", id="sqlite"),
        # PostGIS is selected by Django's ENGINE, so this scheme reads as the obvious one and is
        # not a valid one.
        pytest.param("postgis://mapsift:secret@db:5432/mapsift", id="postgis-scheme"),
    ],
)
def test_a_database_url_that_is_not_postgresql_is_rejected(url: str) -> None:
    with pytest.raises(ValidationError) as error:
        Environment(_env_file=None, secret_key="test-only-not-a-real-key", database_url=url)

    assert _failing_fields(error) == {"database_url"}


def test_allowed_hosts_reads_the_comma_separated_form_a_human_actually_writes() -> None:
    environment = Environment(
        _env_file=None,
        secret_key="test-only-not-a-real-key",
        database_url=VALID_DATABASE_URL,
        allowed_hosts="api.mapsift.local, localhost",
    )
    assert environment.allowed_hosts == ["api.mapsift.local", "localhost"]


def test_allowed_hosts_reads_that_same_form_from_a_real_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The path that hides the trap: a list field is JSON-decoded before any validator sees it,
    so `a,b` can fail from a variable while sailing through as an argument."""
    monkeypatch.setenv("SECRET_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("DATABASE_URL", VALID_DATABASE_URL)
    monkeypatch.setenv("ALLOWED_HOSTS", "api.mapsift.local, localhost")

    environment = Environment(_env_file=None)

    assert environment.allowed_hosts == ["api.mapsift.local", "localhost"]


def test_the_database_url_becomes_django_connection_settings() -> None:
    environment = Environment(
        _env_file=None,
        secret_key="test-only-not-a-real-key",
        database_url="postgresql://mapsift_user:pw@db.internal:5433/mapsift",
    )

    assert environment.django_database() == {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "mapsift",
        "USER": "mapsift_user",
        "PASSWORD": "pw",
        "HOST": "db.internal",
        "PORT": "5433",
    }


def test_a_url_without_a_port_leaves_the_port_to_the_driver() -> None:
    environment = Environment(
        _env_file=None,
        secret_key="test-only-not-a-real-key",
        database_url="postgresql://mapsift_user:pw@db.internal/mapsift",
    )

    assert environment.django_database()["PORT"] == ""
    assert environment.django_database()["HOST"] == "db.internal"


def test_the_secret_key_does_not_leak_through_the_representation() -> None:
    environment = Environment(
        _env_file=None, secret_key="test-only-not-a-real-key", database_url=VALID_DATABASE_URL
    )
    assert "test-only-not-a-real-key" not in repr(environment)
    assert "test-only-not-a-real-key" not in str(environment)
    assert environment.secret_key.get_secret_value() == "test-only-not-a-real-key"
