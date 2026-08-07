"""A request arrives with a principal, and the tenant it claims is verified before anything binds.

Trace: T5.1 and C13 (the authoritative identity is the authenticated session, never a field the
request supplied), T6.5's cross-tenant half (the refusal is indistinguishable from a resource that
never existed), M8 (the tenant travels in the envelope); foundation I4 and I10; C4, C5; ADR-0005
sections 3, 4 and 8; ADR-0010, whose seven decisions this suite is the gate for. Cross-package by
nature, so it lives here (ADR-0007 section 6): the mechanism is `config`, the route is `sync`, the
membership it verifies against is `accounts`.

**Four mechanisms can refuse a request here and three of them are wrong for any given case**: the
framework refusing an unauthenticated caller, the CSRF check, the verification refusing a claim the
principal cannot back, and the wall answering with nothing (ADR-0005 section 4). A status code
alone separates only the first three, because T6.5 requires the fourth to be indistinguishable from
the third. What separates those two is `bindings_opened`: the verification refuses with no tenant
ever bound, the wall could only refuse after one was, and Django's own URL resolver would open
neither. Every refusal here therefore asserts which bindings the request opened, and that assertion
is the test rather than an embellishment of it.

**No assertion that something is absent stands alone.** An empty binding list is what a request
refused by any earlier mechanism produces, and an empty `session_scoped` or `interpolated` list is
what a recorder that cannot read the argument it is about produces. So each of those sits beside a
positive assertion in the same test that fails when the request did not get where the test says it
did, and the recorder's own two arms are controlled by two tests of their own:
`test_the_recorder_separates_a_correct_binding_from_each_way_it_can_be_spelled_wrong` executes
every wrong spelling on purpose, and
`test_a_binding_statement_the_recorder_cannot_read_reports_as_wrong_not_as_fine` pins what
the parser does with a statement it cannot parse. Deleting either arm of the recorder costs two
failures; deleting neither costs none, which is how the gap in the first version of this paragraph
was found.

**What this suite cannot prove, stated so it is not mistaken for coverage.** The Django test client
is same-process: it exercises neither the origin nor the cookie over the wire, so the same-origin
premise ADR-0010 decision 2 rests on is out of reach here and is MAP-20's to prove.
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.db import connection

from config.api import api
from conftest import (
    REVERTED_WITH_ITS_TRANSACTION,
    TENANT_PARAMETER,
    USER_PARAMETER,
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    bindings_opened,
)
from mapsift.accounts.services import create_organization_account, create_personal_account

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# The availability probes of N12, as the schema names them. A probe that needs a credential cannot
# answer whatever restarts the process, so these two are the deliberate public surface (ADR-0010
# decision 6's addition).
LIVENESS_OPERATION = ("/api/health", "get")
READINESS_OPERATION = ("/api/ready", "get")


def a_batch_claiming(*tenant_ids: UUID) -> JsonObject:
    return {"operations": [a_feature_create_claiming(tenant_id) for tenant_id in tenant_ids]}


def _the_tenant_parameter_now() -> str | None:
    """What the connection answers for the tenant parameter, outside any binding of ours."""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT current_setting('{TENANT_PARAMETER}', true)")
        answered: str | None = cursor.fetchone()[0]
        return answered


def _operations_needing_no_credential() -> set[tuple[str, str]]:
    """Every published operation the schema documents as reachable without authentication.

    Read from the API's own OpenAPI document rather than from a list, for the reason the N2
    catalogue test reads from `pg_class`: a route added later is missing from a list silently and
    from the document never (ADR-0010 decision 4).
    """
    return {
        (path, method)
        for path, operations in api.get_openapi_schema()["paths"].items()
        for method, operation in operations.items()
        if "security" not in operation
    }


def test_an_unauthenticated_request_is_refused_by_the_framework_with_nothing_bound(
    alice: Party,
) -> None:
    """T5.1, C13, I10: the identity the server acts on is the authenticated session's, so a request
    that carries none never reaches the point where a tenant could be resolved for it. The refusal
    is the framework's and is asserted rather than implemented (measured 2026-08-07); the CSRF pair
    is carried so that this case is refused for the reason it names and not by the check below."""
    with bindings_opened() as bindings:
        response = a_browser().post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {"detail": "Unauthorized"}
    assert (bindings.users, bindings.tenants) == ([], [])


def test_an_authenticated_write_without_its_csrf_token_is_refused_by_the_csrf_check(
    alice: Party,
) -> None:
    """ADR-0010 decision 1. Not deletable once it goes green: it is what stops a later pass from
    constructing the session auth with `csrf=False` to make a suite pass, which is precisely what
    the default test client already does silently. The cookie is present and only the header is
    missing, which is the shape the web client's one-line adaptation fixes (decision 3)."""
    browser = a_browser(authenticated_as=alice.user_id, carrying_its_csrf_token=False)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {"detail": "CSRF check Failed"}
    assert (bindings.users, bindings.tenants) == ([], [])


def test_a_claim_the_principal_holds_is_accepted_and_binds_exactly_that_tenant(
    alice: Party,
) -> None:
    """C4, ADR-0005 section 3: the binding is made once per request, and the value it carries is
    the one the envelope claimed and the principal was proven to hold."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert response.status_code == HTTPStatus.OK
    assert bindings.tenants == [alice.tenant_id]


def test_the_wall_is_bound_to_the_session_user_and_never_to_a_field_of_the_request(
    alice: Party,
) -> None:
    """T5.1, C13, ADR-0005 section 8: the user binding is what makes the login question answerable
    before a tenant exists, and the identity it carries is the session's, not the client's."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert bindings.users == [alice.user_id]


def test_the_tenant_reaches_its_binding_as_a_parameter_and_never_as_statement_text(
    alice: Party,
) -> None:
    """ADR-0005 section 3, measurement E: the parameter is settable by the same unprivileged role
    and is not revocable, so an injection on the binding path re-binds the tenant and the wall does
    not stop it. Parameterising the statement is the control, not the tidier spelling."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert bindings.tenants == [alice.tenant_id]
    assert bindings.interpolated == []


def test_the_binding_a_request_opened_is_transaction_scoped_and_does_not_survive_it(
    alice: Party,
) -> None:
    """ADR-0005 section 3, measurements C and D: Django holds a connection open across requests, so
    a session-scoped binding reaches the next request on it, which may belong to another tenant.

    Three assertions and one behaviour, because the arm that catches measurement D is invisible on
    its own twice over. `session_scoped` is empty for a request that bound nothing at all, so the
    first line is what makes the second mean something; and the parameter already answers the empty
    string before the act, because the arrange step's own `tenant_scope` defined it and let it
    revert (measured 2026-08-07: an untouched parameter answers NULL, this one answers ''), so the
    third line cannot tell a correct request from one that bound nothing either."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert bindings.tenants == [alice.tenant_id]
    assert bindings.session_scoped == []
    assert _the_tenant_parameter_now() == REVERTED_WITH_ITS_TRANSACTION


def test_the_recorder_separates_a_correct_binding_from_each_way_it_can_be_spelled_wrong(
    alice: Party,
) -> None:
    """The instrument's own control, and the reason it is a test rather than a probe somebody ran
    once: every `interpolated == []` and `session_scoped == []` above is satisfied by a recorder
    that cannot read the argument it is about, and a witness that fails towards "fine" is worse
    than no witness. So each wrong spelling is executed here, on a parameter of its own so no
    verdict is ambiguous, and the recorder is required to separate all three (ADR-0005 section 3,
    measurement E for the interpolated one and D for the session-scoped one).

    The session-scoped write below needs no cleanup and adding one would be defending against
    nothing: measured 2026-08-07, pytest-django gives each transactional test its own backend
    (distinct `pg_backend_pid`), and the parameter answers NULL in the next test rather than the
    value written here. What would make it leak is a connection held across tests, which is
    measurement D itself and is the day this comment stops being true."""
    interpolated_tenant = f"SELECT set_config('{TENANT_PARAMETER}', '{alice.tenant_id}', true)"

    with bindings_opened() as bindings, connection.cursor() as cursor:
        cursor.execute(f"SELECT set_config('{TENANT_PARAMETER}', %s, true)", [str(alice.tenant_id)])
        cursor.execute(interpolated_tenant)
        cursor.execute(f"SELECT set_config('{USER_PARAMETER}', %s, false)", [str(alice.user_id)])

    assert bindings.tenants == [alice.tenant_id]
    assert bindings.users == [alice.user_id]
    assert bindings.interpolated == [TENANT_PARAMETER]
    assert bindings.session_scoped == [USER_PARAMETER]


def test_a_binding_statement_the_recorder_cannot_read_reports_as_wrong_not_as_fine() -> None:
    """The other half of the control, pinning what `_the_value_and_the_scope_of` promises. A value
    carrying a comma is valid SQL and splits into more arguments than `set_config` takes, so it is
    the cheapest statement the parser genuinely cannot read. An instrument that answered "neither
    wrong" here would go silent on exactly the statements nobody anticipated, which is the failure
    mode the whole recorder exists against."""
    with bindings_opened() as bindings, connection.cursor() as cursor:
        cursor.execute(f"SELECT set_config('{TENANT_PARAMETER}', 'not,a,uuid', true)")

    assert bindings.tenants == []
    assert bindings.interpolated == [TENANT_PARAMETER]
    assert bindings.session_scoped == [TENANT_PARAMETER]


def test_a_claim_on_a_tenant_the_principal_lacks_is_answered_exactly_as_one_that_never_existed(
    alice: Party, bob: Party
) -> None:
    """T6.5, I4, ADR-0010 decision 6's addition of 2026-08-07, which states the testable form:
    indistinguishability is comparative, so it is asserted by comparison and by nothing else. A
    body naming the tenant, the membership or the reason defeats it while the status line still
    reads 404, and a status-only assertion is blind to every one of those. The status assertion
    stays as the positive control: two identical 500s would satisfy the comparison alone."""
    browser = a_browser(authenticated_as=bob.user_id)

    on_a_tenant_that_exists = browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)
    on_a_tenant_that_never_did = browser.post(OPERATIONS_PATH, a_batch_claiming(uuid4()), JSON)

    assert on_a_tenant_that_exists.status_code == HTTPStatus.NOT_FOUND
    assert (on_a_tenant_that_exists.status_code, on_a_tenant_that_exists.content) == (
        on_a_tenant_that_never_did.status_code,
        on_a_tenant_that_never_did.content,
    )


def test_an_unbacked_claim_is_refused_before_the_wall_is_ever_bound_to_it(
    alice: Party, bob: Party
) -> None:
    """T6.5, ADR-0005 sections 4 and 8, ADR-0010 decision 6. The assertion is the whole point of
    this suite's discrimination rule: three different mechanisms produce a 404 on this request, and
    only one of them is correct. The wall would have had to be bound to Alice's tenant first, and
    Django's URL resolver would have opened neither binding. Bound user, unbound tenant is the
    verification, and it is the only state that also proves the check ran before the wall did."""
    browser = a_browser(authenticated_as=bob.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id), JSON)

    assert bindings.users == [bob.user_id]
    assert bindings.tenants == []


def test_one_body_is_accepted_for_the_principal_holding_the_tenant_and_not_for_the_one_who_is_not(
    alice: Party, bob: Party
) -> None:
    """T5.1, C13, I10: the answer is a function of the authenticated session and never of a field
    the request supplied, which one body sent by two principals is what proves."""
    body = a_batch_claiming(alice.tenant_id)

    for_alice = a_browser(authenticated_as=alice.user_id).post(OPERATIONS_PATH, body, JSON)
    for_bob = a_browser(authenticated_as=bob.user_id).post(OPERATIONS_PATH, body, JSON)

    assert for_alice.status_code == HTTPStatus.OK
    assert for_bob.status_code == HTTPStatus.NOT_FOUND


def test_a_principal_holding_two_tenants_binds_the_one_this_request_claims() -> None:
    """ADR-0005 section 8, M1: a user belonging to two tenants has one identity and two
    memberships, and the request reaches exactly the one it claimed."""
    personal = create_personal_account(email="ana@example.com")
    organization = create_organization_account(name="Acme Ambiental", owner=personal.user)
    browser = a_browser(authenticated_as=personal.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(organization.tenant_id), JSON)

    assert bindings.tenants == [organization.tenant_id]


def test_the_same_principal_binds_its_other_tenant_when_that_is_what_the_request_claims() -> None:
    """ADR-0005 section 8: the mirror of the case above, and not a duplicate of it. Without this
    one an implementation that binds whichever membership it happens to read first stays green."""
    personal = create_personal_account(email="ana@example.com")
    create_organization_account(name="Acme Ambiental", owner=personal.user)
    browser = a_browser(authenticated_as=personal.user_id)

    with bindings_opened() as bindings:
        browser.post(OPERATIONS_PATH, a_batch_claiming(personal.tenant_id), JSON)

    assert bindings.tenants == [personal.tenant_id]


def test_a_disagreeing_batch_binds_nothing_rather_than_the_tenant_its_first_operation_claims(
    alice: Party,
) -> None:
    """ADR-0010 decision 6, C4: first-wins is the concrete defect the rule exists against, and it
    is invisible in the status code alone, because a batch led by a tenant the principal does hold
    would be bound, accepted and reported as success. The status is the ratified 422 of decision
    6's addition and it stands here as the positive control rather than as a second subject: an
    empty binding list is what a 401 produces too, so without it this test is satisfied by
    authentication being broken."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id, uuid4()), JSON)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert bindings.tenants == []


def test_a_batch_with_no_operations_is_refused_rather_than_bound_to_anything(
    alice: Party,
) -> None:
    """ADR-0010 decision 6, M8: the tenant is read from the envelope, so a batch carrying no
    envelope carries no tenant, and there is nothing for the verification to check or the wall to
    be configured from."""
    browser = a_browser(authenticated_as=alice.user_id)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, a_batch_claiming(), JSON)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert bindings.tenants == []


def test_the_two_refusals_a_malformed_batch_can_earn_are_distinguishable_to_the_client(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-07: two named refusals, not one. The addition
    states the cost of collapsing them in the client's terms, so that is where it is asserted: a
    caller that cannot tell "your operations disagree" from "you sent nothing" cannot act on
    either. The two status assertions are the positive control, since two responses that both
    failed to arrive would differ just as readily as two that carried distinct refusals."""
    browser = a_browser(authenticated_as=alice.user_id)

    disagreeing = browser.post(OPERATIONS_PATH, a_batch_claiming(alice.tenant_id, uuid4()), JSON)
    empty = browser.post(OPERATIONS_PATH, a_batch_claiming(), JSON)

    assert disagreeing.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert empty.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert disagreeing.content != empty.content


def test_every_published_operation_needs_a_credential_except_the_availability_probes() -> None:
    """ADR-0010 decision 4, and decision 6's addition for the exemption: the mechanism lives at one
    point, so a route added later is protected because of where the mechanism sits and not because
    its author remembered, and what that point does not cover is stated by name or N12's liveness
    and readiness stop being reachable. Asserted against the whole published surface, which is what
    makes the next route's omission a red build rather than an open door."""
    assert _operations_needing_no_credential() == {LIVENESS_OPERATION, READINESS_OPERATION}
