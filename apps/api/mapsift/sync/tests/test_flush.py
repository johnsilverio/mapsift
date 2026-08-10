"""The flush: the call that puts a client's queued operations into the append-only log.

Trace: T2.2 (the clause this slice carries is that no authoritative state is read from the
WebSocket tier), M15 (a log entry is the M8 envelope as applied), M9 (an operation type outside the
closed catalog is refused with a typed error), C4 with N2 and ADR-0005 sections 3 and 4 (the wall,
and which of its two silences answered); C9, I2. The route, the request body and the client a write
test may use are ADR-0010 decision 6 with its addition of 2026-08-07, and not this suite's to pick.
Nor is what a batch may be composed of: the addition of 2026-08-10 makes one flush address exactly
one project as well as one tenant, so a batch here names one of each or it is refused before it
arrives, whatever the case around it was written to prove.

What is deliberately not here, each with the issue that owns it: the per-project version that will
order these rows (MAP-11), so what lands is asserted as a set and never as a sequence; the assertion
that the flush is one transaction (MAP-11, by boundary decision 7 of 2026-08-10, because no failure
reachable through this route can falsify it and a test written here would pass for the wrong
reason); the dedup and the echoed cursor (MAP-12); the contiguity and the typed resend on a gap
(MAP-13); and the projection, which no flush in this slice writes.
"""

from http import HTTPStatus
from uuid import uuid4

import pytest

from conftest import (
    POLICY_VIOLATION,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
    refused_with,
)
from mapsift.common.binding import tenant_scope
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry
from mapsift.sync.services import append_to_the_operation_log

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"


def test_a_flush_lands_every_operation_of_its_batch_in_the_log(alice: Party) -> None:
    """T2.2, C9: the flush is the API call that puts a client's queue into the database, which is
    the only place the order those operations are read back in can come from. Every operation of
    the batch lands and none is lost; the sequence they land in is the per-project version's and
    MAP-11 is what claims it. The two operations come from one client, carry consecutive mutation
    numbers and name one project, because that is what a flush is (M4, C12, and the project by the
    addition of 2026-08-10) and a batch spelled any other way asserts something about batches that
    this slice has no business deciding."""
    first, second, one_client = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        {
            "operations": [
                a_feature_create_claiming(
                    alice.tenant_id,
                    operation_id=first,
                    client_id=one_client,
                    mutation_number=1,
                    project_id=alice.project_id,
                ),
                a_feature_create_claiming(
                    alice.tenant_id,
                    operation_id=second,
                    client_id=one_client,
                    mutation_number=2,
                    project_id=alice.project_id,
                ),
            ]
        },
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    with tenant_scope(alice.tenant_id):
        landed = set(OperationLogEntry.objects.values_list("operation_id", flat=True))

    assert landed == {first, second}


def test_a_logged_entry_replays_the_operation_its_client_authored(alice: Party) -> None:
    """M15's Shape, the M8 envelope as applied. These rows are the only record this slice produces,
    so an entry that kept the identifier and dropped the envelope satisfies nothing downstream and
    starves MAP-12, whose dedup reads the clientID and the mutation number off them. The whole
    envelope is asserted through the generated reader rather than field by field, because a
    field-by-field assertion pins the fields somebody remembered."""
    authored = a_feature_create_claiming(alice.tenant_id)
    browser = a_browser(authenticated_as=alice.user_id)

    browser.post(OPERATIONS_PATH, {"operations": [authored]}, JSON)

    with tenant_scope(alice.tenant_id):
        entry = OperationLogEntry.objects.get()

    assert ClientHalf.model_validate(entry.client_half) == ClientHalf.model_validate(authored)


def test_a_logged_entry_replays_the_catalogs_other_operation_with_its_payload(
    alice: Party,
) -> None:
    """M15 with M9, and not a duplicate of the case above. The two catalog members carry
    structurally different targets and only this one carries a payload, so an entry shaped around
    `feature.create` drops the geometry of a `feature.geometry.set` while the case above stays
    green, which is exactly the log MAP-11's replay could not read back."""
    authored = a_geometry_set_claiming(alice.tenant_id)
    browser = a_browser(authenticated_as=alice.user_id)

    browser.post(OPERATIONS_PATH, {"operations": [authored]}, JSON)

    with tenant_scope(alice.tenant_id):
        entry = OperationLogEntry.objects.get()

    assert ClientHalf.model_validate(entry.client_half) == ClientHalf.model_validate(authored)


def test_an_operation_type_outside_the_closed_catalog_is_refused_at_the_flush_boundary(
    alice: Party,
) -> None:
    """M9, and ADR-0009 section 4 with it. The tell is the error type rather than the status: a
    hand-written schema in front of the generated union, or a discriminator that degraded to a
    plain union, still refuses this document, so a bare `422` would pass over both. The status is
    the ratified one of ADR-0010 decision 6's addition and stands as the positive control."""
    nobody_declared_it = {
        **a_feature_create_claiming(alice.tenant_id),
        "operation_type": "basin.dredge",
    }
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(OPERATIONS_PATH, {"operations": [nobody_declared_it]}, JSON)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert [refusal["type"] for refusal in response.json()["detail"]] == ["union_tag_invalid"]


def test_an_operation_addressed_at_another_tenant_is_refused_by_the_wall(
    alice: Party, bob: Party
) -> None:
    """C4, N2, ADR-0005 sections 3 and 4: a log entry carries the tenant its operation is
    addressed at, so the policy's WITH CHECK is what refuses this one, and a Python comparison that
    refused it first would leave the wall itself unexercised. Reached through the writer rather
    than the route, because ADR-0010 decision 6 refuses a disagreeing batch at the boundary and the
    wall has to hold for every caller, not only the one that route admits. The suite connects as
    the owner, which holds every privilege on this table, so the 42501 caught here can only be the
    policy and never the grant the append-only suite measures."""
    addressed_at_bob = ClientHalf.model_validate(a_feature_create_claiming(bob.tenant_id))

    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        append_to_the_operation_log([addressed_at_bob])
