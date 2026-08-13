"""The installation a batch comes from, decided before anything is verified or bound.

Trace: ADR-0010 decision 6's addition of 2026-08-11 (one flush addresses exactly one clientID, a
fourth typed refusal beside the three the tenant and the project already earned, told apart by its
body, and checked after both of them); M4 and M10, whose cursor and whose contiguity are keyed by
clientID, tenant and project together, so the composition rule below is what makes that key
readable off a batch at all; C12, the silent loss it exists against.

**This is the precondition of `test_dedup_and_the_echoed_cursor.py` rather than a neighbour of it.**
The dedup is keyed by the clientID, so a flush has to read one off its batch, and a flush that
reads it off its first operation applies one installation's cursor to another installation's work:
the second is deduplicated against a number it never issued. That is why the rule was decided at
this task's review rather than left for a later one, and why it is a module of its own rather than
a second subject inside the one that consumes it.

**Two halves, and the split is the one the two sibling modules already draw.** The decision is pure
(specs/testing.md section 3), so the refusal and its type are asserted on plain data with no
database, exactly as `test_batch_tenant_agreement.py` and `test_batch_project_agreement.py` do.
What a client actually receives is not pure: the boundary flattens every refusal into one status,
so "told apart by its body" and "before anything is bound" are only observable through the route,
which is where the other two axes assert them as well. Those live in
`apps/api/tests/test_authenticated_request.py` because that suite's subject is the authenticated
request and its bindings; the clientID's are here because this rule is the sync package's and
`apps/api/tests/` holds only what crosses packages (ADR-0007 section 6).

**The case the two siblings carry and this one does not, said rather than left to be noticed.**
Both of them prove the rule over the catalog's two members, because the tenant and the project ride
on the **target**, whose two variants are structurally different types, so a rule reading one
variant is green on a batch of it. The clientID rides on the envelope root and is one field on both
members (M8), so there is no variant for a rule to be narrowed to and the case would assert
nothing.

**One deliberate gap, with the issue that owns it:** the order between the tenant and the project
is not this module's, and no case here touches it. ADR-0010 decision 6's addition is explicit that
only the clientID's last position rests on the evidence it carries, and the tenant-before-project
order is the validator's own older contract.
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    bindings_opened,
)
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    BatchClaimsNoTenant,
    OperationsDisagreeOnTheirClient,
    OperationsDisagreeOnTheirProject,
    OperationsDisagreeOnTheirTenant,
    the_client_every_operation_claims,
)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"


def _as_authored(*operations: JsonObject) -> list[ClientHalf]:
    """The batch as the generated reader sees it, which is what the rule decides over (M8)."""
    return [ClientHalf.model_validate(operation) for operation in operations]


def _a_batch_of(*operations: JsonObject) -> JsonObject:
    """A flush body, spelled one operation at a time (ADR-0010 decision 6's addition of 2026-08-07).

    A builder that mints one correct queue is the wrong instrument for a module whose whole subject
    is a batch disagreeing with itself, which is why this takes operations rather than a count.
    """
    return {"operations": list(operations)}


def _one_installation() -> tuple[UUID, UUID]:
    """The same installation twice, so the axis a batch is about is the only thing wrong with it."""
    installation = uuid4()
    return installation, installation


def _two_installations() -> tuple[UUID, UUID]:
    """Two installations, for the cases about which refusal a batch wrong on two axes earns."""
    return uuid4(), uuid4()


def _a_batch_disagreeing_on_its_installation(party: Party) -> JsonObject:
    """Two operations of one tenant and one project, authored on two installations."""
    return _a_batch_of(
        a_feature_create_claiming(party.tenant_id, project_id=party.project_id, client_id=uuid4()),
        a_feature_create_claiming(party.tenant_id, project_id=party.project_id, client_id=uuid4()),
    )


def _a_batch_disagreeing_on_its_tenant(
    party: Party, *, authored_on: tuple[UUID, UUID]
) -> JsonObject:
    """Two operations of one project, addressed at two tenants, from the installations given."""
    first, second = authored_on
    return _a_batch_of(
        a_feature_create_claiming(party.tenant_id, project_id=party.project_id, client_id=first),
        a_feature_create_claiming(uuid4(), project_id=party.project_id, client_id=second),
    )


def _a_batch_disagreeing_on_its_project(
    party: Party, *, authored_on: tuple[UUID, UUID]
) -> JsonObject:
    """Two operations of one tenant, addressed at two projects, from the installations given."""
    first, second = authored_on
    return _a_batch_of(
        a_feature_create_claiming(party.tenant_id, project_id=party.project_id, client_id=first),
        a_feature_create_claiming(party.tenant_id, project_id=uuid4(), client_id=second),
    )


def test_a_batch_whose_operations_all_come_from_one_installation_answers_with_it() -> None:
    """ADR-0010 decision 6's addition of 2026-08-11, M8: the clientID travels in the envelope, so
    it is read there and not inferred from the session, which is a different thing entirely (M4).
    The positive control the refusal below depends on, since a rule that refuses every batch
    satisfies that one on its own."""
    tenant, project, installation = uuid4(), uuid4(), uuid4()

    batch = _as_authored(
        a_feature_create_claiming(tenant, project_id=project, client_id=installation),
        a_feature_create_claiming(tenant, project_id=project, client_id=installation),
    )

    assert the_client_every_operation_claims(batch) == installation


def test_two_installations_in_one_batch_are_refused_rather_than_read_first_wins() -> None:
    """ADR-0010 decision 6's addition of 2026-08-11. The tenant and the project are held constant
    deliberately, as the project module holds the tenant: a batch wrong on more than one axis is
    refused by whichever rule runs first and says nothing about this one. First-wins is the
    concrete defect, and here it is not a wrong value but a wrong stream: the flush answers with
    one echo, so the installation whose cursor was not the one read advances onto a number the
    server never applied for it, which is the silent client-side loss C12 exists against. The
    second assertion is the addition's "told apart", stated on the value the act raised, against
    all three of the refusals it stands beside rather than one."""
    tenant, project = uuid4(), uuid4()

    batch = _as_authored(
        a_feature_create_claiming(tenant, project_id=project, client_id=uuid4()),
        a_feature_create_claiming(tenant, project_id=project, client_id=uuid4()),
    )

    with pytest.raises(OperationsDisagreeOnTheirClient) as refusal:
        the_client_every_operation_claims(batch)

    assert not isinstance(
        refusal.value,
        (BatchClaimsNoTenant, OperationsDisagreeOnTheirProject, OperationsDisagreeOnTheirTenant),
    )


@pytest.mark.django_db(transaction=True)
def test_a_batch_of_two_installations_is_refused_before_anything_is_bound(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-11: refused at the boundary, before anything is
    bound. What that buys is what the pure case above cannot see: past this boundary the request
    would bind a real tenant, take a real cursor and deduplicate one installation's queue against
    another's, and the log it wrote would be indistinguishable afterwards from one that was always
    right. The 422 is the addition's ratified status and stands as the positive control, because an
    empty binding list is what a 401 produces too."""
    browser = a_browser(authenticated_as=alice.user_id)
    two_installations = _a_batch_disagreeing_on_its_installation(alice)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, two_installations, JSON)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert bindings.tenants == []


@pytest.mark.django_db(transaction=True)
def test_the_client_refusal_is_distinguishable_from_the_three_refusals_it_stands_beside(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-11, which puts the fourth refusal under every
    clause of the two additions before it: the four share a status and are told apart by their
    bodies. Not a duplicate of the pure case, and the boundary is why: the validator flattens every
    typed refusal into one `ValueError`, so three distinct classes carrying one message reach the
    client as one answer and the pure assertion stays green. Asserted in the client's terms because
    that is where the addition states the cost, and the cost here is specific: a client told only
    "malformed" regroups its queue by the wrong key and flushes the same broken batch again, which
    is a stall rather than an error it can act on. The status assertion is the positive control,
    since a batch this route accepted answers with a body that differs from all three just as
    readily."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_installations = browser.post(
        OPERATIONS_PATH, _a_batch_disagreeing_on_its_installation(alice), JSON
    )
    on_two_tenants = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant(alice, authored_on=_one_installation()),
        JSON,
    )
    on_two_projects = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project(alice, authored_on=_one_installation()),
        JSON,
    )
    empty = browser.post(OPERATIONS_PATH, _a_batch_of(), JSON)

    assert on_two_installations.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert on_two_installations.content not in {
        on_two_tenants.content,
        on_two_projects.content,
        empty.content,
    }


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_also_disagrees_on_its_client_still_earns_the_tenant_refusal(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-11 fixes the clientID last, and the reason is
    empirical rather than aesthetic: four cases in `apps/api/tests/test_authenticated_request.py`
    build batches that disagree on their tenant or their project **and** on their clientID, because
    the shared helper mints a fresh one whenever a caller does not pin it, and one of those four
    asserts the status without the body, so a clientID check running first would hand it the wrong
    refusal and it would keep passing for the wrong reason. Those cases may not be edited, so the
    order is stated here as behaviour rather than inferred from what they happen to catch.

    Quiet until the fourth check exists, like its sibling below and for the same reason. The
    control beside the subject is what stops it being satisfied by nothing once it does: if the
    refusals ever collapsed into one shared body, every comparison of this shape would agree while
    the order was free."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_tenants = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant(alice, authored_on=_one_installation()),
        JSON,
    )
    also_on_two_installations = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant(alice, authored_on=_two_installations()),
        JSON,
    )
    on_two_installations = browser.post(
        OPERATIONS_PATH, _a_batch_disagreeing_on_its_installation(alice), JSON
    )

    assert also_on_two_installations.content == on_two_tenants.content
    assert on_two_installations.content != on_two_tenants.content


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_also_disagrees_on_its_client_still_earns_the_project_refusal(
    alice: Party,
) -> None:
    """The sibling of the case above on the axis the existing suite does not reach. A clientID
    check placed first is caught elsewhere, because the project refusal would collapse onto the
    tenant's in a case that compares the two; a clientID check placed **between** the tenant and
    the project is caught by nothing that exists, and it is a wrong order all the same (ADR-0010
    decision 6's addition of 2026-08-11). What it costs a client is concrete: told its
    installations disagree when its projects do, it regroups the queue by installation and meets
    the project refusal on the next flush, having paid a round trip to learn the first answer was
    the second question.

    Quiet until the fourth check exists, with the same control as the case above."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_projects = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project(alice, authored_on=_one_installation()),
        JSON,
    )
    also_on_two_installations = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project(alice, authored_on=_two_installations()),
        JSON,
    )
    on_two_installations = browser.post(
        OPERATIONS_PATH, _a_batch_disagreeing_on_its_installation(alice), JSON
    )

    assert also_on_two_installations.content == on_two_projects.content
    assert on_two_installations.content != on_two_projects.content
