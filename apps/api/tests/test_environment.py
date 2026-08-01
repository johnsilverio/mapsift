"""The environment is a validated boundary, not a bag of strings.

Requirements under test: I5 and C5 (Pydantic at every boundary, config named explicitly
among them), ADR-0001 section 4 (configuration comes from the environment, never from a
checked-in file with real values), and PRD N3 (no secret enters the repository or a bundle).

These are pure-decision tests in the sense of `specs/testing.md` section 3: plain data in,
plain data out, no Django, no database, no network. If any of them ever needs a live
service to run, the boundary was factored wrong.
"""

import pytest
from pydantic import ValidationError

from config.env import Environment

VALID_DATABASE_URL = "postgresql://mapsift:secret@db:5432/mapsift"


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's real shell out of these assertions.

    Without this the suite passes or fails depending on what happens to be exported in the
    terminal that ran it, which is the kind of test that erodes trust in the whole suite.
    """
    for name in ("SECRET_KEY", "DATABASE_URL", "DEBUG", "ALLOWED_HOSTS"):
        monkeypatch.delenv(name, raising=False)


def _failing_fields(error: pytest.ExceptionInfo[ValidationError]) -> set[str]:
    """Which fields the validation actually rejected.

    Asserting only that *something* raised is how a test passes for the wrong reason. That
    happened once while writing these: a wrongly-cased argument reached no field at all, so
    the object failed to build and two tests went green without ever exercising the rule they
    claimed to cover. Naming the field is what closes that gap.
    """
    return {str(detail["loc"][0]) for detail in error.value.errors()}


def test_a_missing_secret_key_is_rejected_rather_than_defaulted() -> None:
    """A secret with a fallback is a secret that ships by accident."""
    with pytest.raises(ValidationError) as error:
        Environment(_env_file=None, database_url=VALID_DATABASE_URL)

    assert _failing_fields(error) == {"secret_key"}


def test_a_missing_database_url_is_rejected_rather_than_defaulted() -> None:
    """The ratified database is PostgreSQL with PostGIS, so there is no fallback to fall into."""
    with pytest.raises(ValidationError) as error:
        Environment(_env_file=None, secret_key="test-only-not-a-real-key")

    assert _failing_fields(error) == {"database_url"}


def test_debug_is_off_unless_the_environment_turns_it_on() -> None:
    """The safe value is the default, so forgetting the variable cannot expose a stack trace."""
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
        pytest.param("sqlite:///db.sqlite3", id="sqlite reaching production by way of a typo"),
        pytest.param(
            "postgis://mapsift:secret@db:5432/mapsift",
            id="postgis:// which is a real and easy confusion",
        ),
    ],
)
def test_a_database_url_that_is_not_postgresql_is_rejected(url: str) -> None:
    """The second case is the one that will actually bite somebody.

    The ratified database is always spoken of as PostgreSQL plus PostGIS, so `postgis://`
    reads as the obvious scheme and is not a valid one. PostGIS is selected by Django's
    database ENGINE; the URL scheme stays `postgresql://`.
    """
    with pytest.raises(ValidationError) as error:
        Environment(
            _env_file=None,
            secret_key="test-only-not-a-real-key",
            database_url=url,
        )

    assert _failing_fields(error) == {"database_url"}


def test_allowed_hosts_reads_the_comma_separated_form_a_human_actually_writes() -> None:
    """An operator writes `a,b` in a .env file, never a JSON array, so that is what is parsed."""
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
    """The path that actually runs in production, and the one that hides the trap.

    Settings libraries commonly try to JSON-decode a value before any validator sees it, so a
    list field fed `a,b` from a real variable can blow up while the same value passed as an
    argument sails through. Asserting only the argument path would leave that difference
    untested and green.
    """
    monkeypatch.setenv("SECRET_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("DATABASE_URL", VALID_DATABASE_URL)
    monkeypatch.setenv("ALLOWED_HOSTS", "api.mapsift.local, localhost")

    environment = Environment(_env_file=None)

    assert environment.allowed_hosts == ["api.mapsift.local", "localhost"]


def test_the_database_url_becomes_django_connection_settings() -> None:
    """Translating one URL into the framework's dict is a pure decision, so it is tested as one.

    The leading slash is the interesting part: a path of `/mapsift` carried through unchanged
    asks PostgreSQL for a database literally named `/mapsift`, which fails at connection time,
    far from the line that caused it.
    """
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
    """An empty port is how Django is told to use the default, rather than a number we invented."""
    environment = Environment(
        _env_file=None,
        secret_key="test-only-not-a-real-key",
        database_url="postgresql://mapsift_user:pw@db.internal/mapsift",
    )

    assert environment.django_database()["PORT"] == ""
    assert environment.django_database()["HOST"] == "db.internal"


def test_the_secret_key_does_not_leak_through_the_representation() -> None:
    """Logs and tracebacks print objects. This one must not print the key (N9, N3)."""
    environment = Environment(
        _env_file=None, secret_key="test-only-not-a-real-key", database_url=VALID_DATABASE_URL
    )
    assert "test-only-not-a-real-key" not in repr(environment)
    assert "test-only-not-a-real-key" not in str(environment)
    assert environment.secret_key.get_secret_value() == "test-only-not-a-real-key"
