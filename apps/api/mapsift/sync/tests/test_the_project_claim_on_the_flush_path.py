"""The project a flush addresses is verified against the tenant the principal was verified in.

Trace: PRD T6.5's cross-tenant clause (across tenants a resource is indistinguishable from one that
does not exist) and T6.4 as this path narrows it, membership plus containment, since no per-project
grant model exists yet; PRD M1 (a project resolves to exactly one workspace and one tenant) and M9
(a target carries its ancestors, so the project travels in the envelope the way the tenant does);
ADR-0010 decision 6 with its **addition of 2026-08-20** for where this check stands and what its
refusal looks like, and its addition of 2026-08-07 for the comparative form of not-found; ADR-0005
sections 3 and 4 for why the read behind it only answers once the tenant is bound; ADR-0004
decision 4's "what this costs", which is the hole this closes. I4 and C4 name what this is **not**:
the wall keys on the tenant and is intact, and every row a rogue address would write lands inside
the writer's own tenant, so this is authorisation one level below the wall.

**Everything goes through the route and never through the writer**, on the ground the sibling
modules already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only
transaction is one it opened is green against an implementation that has none. The writer keeps no
check of its own in any case, which is forced rather than chosen (ADR-0004 decision 4's forcing
half).

**Inside the wall a project of another tenant and a project that never existed are one silence by
construction**, so T6.5's indistinguishability is the mechanism here rather than something defended
against it. That is also what makes the positive case load-bearing: this refusal shares its status
and its constant body with the tenant claim's, so every refusal below is satisfied by a verification
that refuses everything, and
`test_a_project_the_verified_tenant_holds_is_addressable_by_its_member` is the only line that says
otherwise.

What is deliberately not here, each with the issue that owns it: that a refused flush left its
installation's cursor where it was, which is MAP-46's along with the instrument that witnesses it,
so what a refusal did not do is asserted on the log alone; T6.5's within-tenant half, the explicit
denial with a resolution path, and T6.4's three sharing modes, neither of which has a grant model
to stand on; T6.5's listings clause, since no surface in this backend enumerates a project; and a
batch that *disagrees* on its project, which is refused a step earlier at the Pydantic boundary
(`test_batch_project_agreement.py`).
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest

from conftest import JsonObject, Party, a_browser, a_feature_create_claiming
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"


def _a_queue_addressing(
    tenant_id: UUID,
    project_id: UUID,
    *,
    operation_id: UUID | None = None,
    starting_at: int = 0,
) -> JsonObject:
    """One installation's queue of one operation, addressed at one tenant and one project (M9).

    The two axes are separate arguments rather than one `Party`, which is what every other arranger
    in this package takes: the batch this module is about names a tenant and a project that belong
    to different accounts, and a `Party` cannot spell that.
    """
    return {
        "operations": [
            a_feature_create_claiming(
                tenant_id,
                operation_id=operation_id,
                project_id=project_id,
                mutation_number=starting_at,
            )
        ]
    }


def test_a_project_of_another_tenant_is_answered_exactly_as_one_that_never_existed(
    alice: Party, bob: Party
) -> None:
    """T6.5's cross-tenant clause on the project axis, in the comparative form ADR-0010 decision 6
    fixes in its addition of 2026-08-07 and extends here in its addition of 2026-08-20: not-found
    is a property of the whole response, so it is asserted by comparison and by nothing else. A
    body naming the project, the tenant that holds it, or the reason defeats the clause while the
    status line still reads 404, and a status-only assertion is blind to all three.

    Both claims come from a principal whose **tenant** claim is good, which is what makes this case
    about the project at all: Alice holds her tenant, so the only thing wrong with either request
    is the project it addresses.

    The status assertion stays as the positive control, since two identical 500s would satisfy the
    comparison on their own."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_a_project_that_exists = browser.post(
        OPERATIONS_PATH, _a_queue_addressing(alice.tenant_id, bob.project_id), JSON
    )
    on_a_project_that_never_did = browser.post(
        OPERATIONS_PATH, _a_queue_addressing(alice.tenant_id, uuid4()), JSON
    )

    assert on_a_project_that_exists.status_code == HTTPStatus.NOT_FOUND
    assert (on_a_project_that_exists.status_code, on_a_project_that_exists.content) == (
        on_a_project_that_never_did.status_code,
        on_a_project_that_never_did.content,
    )


def test_a_project_the_verified_tenant_holds_is_addressable_by_its_member(alice: Party) -> None:
    """T6.4 as this path narrows it, membership plus containment: there is no per-project grant
    model to deny against, so what stands until there is one is that a member of the verified
    tenant addresses that tenant's projects and nobody else's.

    **Born green, and that is the point rather than a defect.** It is the other arm of a
    conditional rule, and without it a verification that refused every project would leave every
    refusal in this module green while making the route unusable. It turns red the day the
    containment read stops answering for a project the tenant does hold, which is the single
    likeliest way to implement this task wrongly."""
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH, _a_queue_addressing(alice.tenant_id, alice.project_id), JSON
    )

    assert response.status_code == HTTPStatus.OK


def test_a_flush_refused_for_its_project_leaves_nothing_in_the_log(
    alice: Party, bob: Party
) -> None:
    """M15 with T6.5: the refusal is taken before anything is appended, so the append-only log a
    legal-weight feature is replayed from never holds an operation the client was answered 404 for.
    This is the half of ADR-0004 decision 4's "what this costs" that has a witness here; the cursor
    half is MAP-46's.

    **The accepted operation beside it is the control rather than a second subject**, and it closes
    the trap this suite is written against twice over. The log is read under Alice's own binding,
    which is exactly where the rogue row would have landed, and the wall answers a bound read with
    nothing as readily as an empty table does, so an assertion that the log is empty is also
    satisfied by a request that never arrived at all."""
    browser = a_browser(authenticated_as=alice.user_id)
    accepted, refused = uuid4(), uuid4()

    browser.post(
        OPERATIONS_PATH,
        _a_queue_addressing(alice.tenant_id, alice.project_id, operation_id=accepted),
        JSON,
    )
    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_addressing(alice.tenant_id, bob.project_id, operation_id=refused),
        JSON,
    )

    with tenant_scope(alice.tenant_id):
        landed = set(OperationLogEntry.objects.values_list("operation_id", flat=True))

    assert answered.status_code == HTTPStatus.NOT_FOUND
    assert landed == {accepted}


def test_a_project_this_tenant_does_not_hold_is_refused_before_its_cursor_is_ever_read(
    alice: Party, bob: Party
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-20, whose position clause is load-bearing rather
    than tidy: the cursor is keyed by clientID, tenant and project (M4), so a batch addressing a
    project its tenant does not hold would otherwise earn `no_cursor_in_this_domain`, a 409 telling
    the client to rehandshake against a project it may not address at all, which is the wrong
    recovery arriving with the wrong status.

    **The second post is what makes the first one about the order** rather than about the status.
    Both queues open above the first mutation number from an installation the server has never met,
    which is precisely the arrangement that earns that 409, and the second one earns it on a
    project the tenant does hold. Without that line an implementation answering 404 to every stream
    it could not continue would pass."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_a_project_this_tenant_lacks = browser.post(
        OPERATIONS_PATH,
        _a_queue_addressing(alice.tenant_id, bob.project_id, starting_at=1),
        JSON,
    )
    on_a_project_this_tenant_holds = browser.post(
        OPERATIONS_PATH,
        _a_queue_addressing(alice.tenant_id, alice.project_id, starting_at=1),
        JSON,
    )

    assert on_a_project_this_tenant_lacks.status_code == HTTPStatus.NOT_FOUND
    assert on_a_project_this_tenant_holds.status_code == HTTPStatus.CONFLICT
