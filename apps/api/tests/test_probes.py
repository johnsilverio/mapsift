"""The probe pair of N12: two different questions, asked of different things, answered apart.

Trace: PRD N12; foundation section 10 (the availability decision, v0.16).
"""

from collections.abc import Iterator
from http import HTTPStatus

import pytest
from django.db import connection
from django.test import Client

LIVENESS_PATH = "/api/health"
READINESS_PATH = "/api/ready"

# Nothing listens on port 1, so the outage arrives as a refusal from the kernel rather than as a
# connect timeout, which is what makes it instant instead of a suite that hangs for a minute.
UNREACHABLE_ADDRESS = {"HOST": "127.0.0.1", "PORT": "1"}


@pytest.fixture
def database_reachable(transactional_db: None) -> Iterator[None]:
    """The database answers and nothing is open, so a probe has to connect to find that out."""
    # `transactional_db` reads as superfluous, since no test here touches a model, and dropping it
    # leaves pytest-django's block in place: `ensure_connection` raises RuntimeError, which a probe
    # catching broadly reports as an outage that never happened.
    connection.close()
    yield
    connection.close()


@pytest.fixture
def database_unreachable(database_reachable: None) -> Iterator[None]:
    """The database is gone for this process alone, with the container the suite runs on left up.

    Moving the address is what makes the outage real rather than simulated: the probe opens a
    socket and is refused, on the same path a probe takes when the server is genuinely down.
    """
    address = {key: connection.settings_dict[key] for key in UNREACHABLE_ADDRESS}
    connection.settings_dict.update(UNREACHABLE_ADDRESS)
    try:
        yield
    finally:
        connection.settings_dict.update(address)
        connection.close()


def test_liveness_answers_while_the_database_is_unreachable(
    client: Client, database_unreachable: None
) -> None:
    """N12: green on the day it was written, and not deletable for it. It is what stops a later
    pass from teaching liveness to check the database, which restarts a healthy service."""
    response = client.get(LIVENESS_PATH)

    assert response.status_code == HTTPStatus.OK


def test_readiness_refuses_traffic_while_the_database_is_unreachable(
    client: Client, database_unreachable: None
) -> None:
    response = client.get(READINESS_PATH)

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_readiness_names_the_dependency_that_is_out(
    client: Client, database_unreachable: None
) -> None:
    response = client.get(READINESS_PATH)

    assert response.json()["unavailable"] == ["database"]


def test_readiness_accepts_traffic_while_the_database_answers(
    client: Client, database_reachable: None
) -> None:
    response = client.get(READINESS_PATH)

    assert response.status_code == HTTPStatus.OK
    assert response.json()["unavailable"] == []
