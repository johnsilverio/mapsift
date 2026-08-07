"""The flush: one transactional call that appends a batch of client operations to the log.

Trace: T2.2 (the op-queue flush is the transactional API call the database orders), M9 (an
operation type outside the closed catalog is refused with a typed error), C4 with N2 and ADR-0005
sections 3 and 4 (the wall, and which of its two silences answered); C9, I2.

What is deliberately not here, each with the issue that owns it: the per-project version that will
order these rows (MAP-11), the dedup and the echoed cursor (MAP-12), the contiguity and the typed
resend on a gap (MAP-13), and the projection, which no flush in this slice writes.
"""

from http import HTTPStatus
from uuid import uuid4

import pytest
from django.test import Client

from conftest import POLICY_VIOLATION, Party, refused_with
from mapsift.common.binding import tenant_scope
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry
from mapsift.sync.services import append_to_the_operation_log
from mapsift.sync.tests.envelopes import an_operation_addressed_at

pytestmark = pytest.mark.django_db(transaction=True)

FLUSH_PATH = "/api/sync/flush"


def _an_entry_of(party: Party, *, mutation_number: int = 0) -> ClientHalf:
    return ClientHalf.model_validate(
        an_operation_addressed_at(party, operation_id=uuid4(), mutation_number=mutation_number)
    )


def test_a_flush_lands_every_operation_of_its_batch_in_the_log(
    client: Client, alice: Party
) -> None:
    """T2.2, C9: the flush is the API call that puts a client's queue into the database, which is
    the only place the order those operations are read back in can come from."""
    first, second = uuid4(), uuid4()

    response = client.post(
        FLUSH_PATH,
        data=[
            an_operation_addressed_at(alice, operation_id=first, mutation_number=0),
            an_operation_addressed_at(alice, operation_id=second, mutation_number=1),
        ],
        content_type="application/json",
    )

    assert response.status_code == HTTPStatus.OK
    with tenant_scope(alice.tenant_id):
        landed = set(OperationLogEntry.objects.values_list("operation_id", flat=True))

    assert landed == {first, second}


def test_an_operation_type_outside_the_closed_catalog_is_refused_at_the_flush_boundary(
    client: Client, alice: Party
) -> None:
    """M9, and ADR-0009 section 4 with it. The tell is the error type rather than the status: a
    hand-written schema in front of the generated union, or a discriminator that degraded to a
    plain union, still refuses this document, so a bare `422` would pass over both."""
    nobody_declared_it = {
        **an_operation_addressed_at(alice, operation_id=uuid4(), mutation_number=0),
        "operation_type": "basin.dredge",
    }

    response = client.post(FLUSH_PATH, data=[nobody_declared_it], content_type="application/json")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [refusal["type"] for refusal in response.json()["detail"]] == ["union_tag_invalid"]


def test_a_batch_carrying_an_operation_nobody_declared_lands_none_of_it(
    client: Client, alice: Party
) -> None:
    """M9 with T2.2: the batch is one transaction, so the well-formed operation beside a refused
    one is not half-applied. Green from the first line, because the whole body is one generated
    union and no handler is entered; kept because an implementation that validated operation by
    operation would land the first one and report nothing about it."""
    well_formed = an_operation_addressed_at(alice, operation_id=uuid4(), mutation_number=0)
    nobody_declared_it = {
        **an_operation_addressed_at(alice, operation_id=uuid4(), mutation_number=1),
        "operation_type": "basin.dredge",
    }

    client.post(FLUSH_PATH, data=[well_formed, nobody_declared_it], content_type="application/json")

    with tenant_scope(alice.tenant_id):
        assert not OperationLogEntry.objects.exists()


def test_an_operation_addressed_at_another_tenant_is_refused_by_the_wall(
    alice: Party, bob: Party
) -> None:
    """C4, N2, ADR-0005 sections 3 and 4: a log entry carries the tenant its operation is
    addressed at, so the policy's WITH CHECK is what refuses this one, and a Python comparison
    that refused it first would leave the wall itself unexercised. The suite connects as the
    owner, which holds every privilege on this table, so 42501 here can only be the policy."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        append_to_the_operation_log([_an_entry_of(bob)])


def test_a_batch_the_wall_refuses_lands_none_of_its_operations(alice: Party, bob: Party) -> None:
    """T2.2 with C4: one transaction for the whole batch, so the operation the wall accepts does
    not survive beside the one it refuses."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        append_to_the_operation_log([_an_entry_of(alice), _an_entry_of(bob, mutation_number=1)])

    with tenant_scope(alice.tenant_id):
        assert not OperationLogEntry.objects.exists()
