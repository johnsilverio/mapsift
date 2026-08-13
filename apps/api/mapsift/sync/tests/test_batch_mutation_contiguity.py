"""The stream a batch carries, decided before anything is verified or bound.

Trace: ADR-0010 decision 6's addition of 2026-08-13 (a batch whose own mutation numbers do not
ascend by exactly one at every step is a fifth composition rule, refused at the Pydantic boundary
with 422 beside the other four, told apart by its body, and taken last, after the three
agreements);
PRD M10's Requirement (the server applies a client's operations only in contiguous mutation-number
order, within one flush domain) and its Shape (the mutation number is client-owned and contiguous);
PRD M15, which is what makes ascending part of the rule rather than a nicety, since the log is
replayed in the order it was appended as evidence; C12, the silent loss the axis exists against.

**Pure where the decision is pure, through the route where only the client can see it**, which is
the split the three sibling agreement modules already draw. The refusal and its type are asserted on
plain data with no database (specs/testing.md section 3); the boundary then flattens every typed
refusal into one status and one body, so "told apart by its body" and "before anything is bound" are
observable only through `POST /api/operations`.

**The three order cases are this module's own and not a repetition of the clientID's two.** The
fourth position was fixed on evidence and the fifth is fixed on evidence of the same shape: the
disagreeing batches in `apps/api/tests/test_authenticated_request.py` and in
`test_batch_client_agreement.py` are built from a helper that defaults every operation to mutation
number zero, so they collide on that axis as a side effect nobody chose, and two of them assert the
status and the empty binding list without ever comparing the body. A contiguity check reached before
any of the three agreements hands those batches the wrong refusal and they keep passing for the
wrong reason. They may not be edited, so each adjacency is stated here as behaviour.

**What a batch starts at is not this module's subject.** The number a contiguous batch begins on is
the client's, and whether it is the number the server can accept next is a comparison against the
cursor, which needs the tenant bound and a read and therefore cannot be taken here
(`test_the_typed_resend_on_a_gap.py`, ADR-0010 decision 6's addition of 2026-08-13).
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest

from conftest import JsonObject, Party, a_browser, a_feature_create_claiming, bindings_opened
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    BatchClaimsNoTenant,
    OperationsAreNotOneContiguousStream,
    OperationsDisagreeOnTheirClient,
    OperationsDisagreeOnTheirProject,
    OperationsDisagreeOnTheirTenant,
    the_mutation_number_this_unbroken_stream_starts_at,
)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"


def _as_authored(*operations: JsonObject) -> list[ClientHalf]:
    """The batch as the generated reader sees it, which is what the rule decides over (M8)."""
    return [ClientHalf.model_validate(operation) for operation in operations]


def _a_batch_of(*operations: JsonObject) -> JsonObject:
    """A flush body, spelled one operation at a time (ADR-0010 decision 6's addition of 2026-08-07).

    A builder that mints one correct queue is the wrong instrument for a module whose whole subject
    is a batch wrong about itself, which is why this takes operations rather than a count.
    """
    return {"operations": list(operations)}


def _authored_at(
    mutation_number: int,
    *,
    tenant_id: UUID,
    project_id: UUID,
    client_id: UUID,
) -> JsonObject:
    """One operation of one installation's stream, with every axis of the flush domain pinned.

    None of the four carries a default, so every call site states all four, because every case here
    is about one axis being wrong while the other three are right, and a default is what makes a
    second one wrong by accident. That accident is the reason this check is taken last at all
    (ADR-0010 decision 6's addition of 2026-08-13).
    """
    return a_feature_create_claiming(
        tenant_id,
        client_id=client_id,
        mutation_number=mutation_number,
        project_id=project_id,
    )


def _a_stream_of(*mutation_numbers: int, by: Party) -> JsonObject:
    """One installation's batch in one project of one tenant, carrying the numbers it is given.

    The three agreements hold by construction here, so the numbers are the only thing a case can be
    refused for, which is what lets the fifth rule be observed on its own.
    """
    installation = uuid4()
    return _a_batch_of(
        *(
            _authored_at(
                number,
                tenant_id=by.tenant_id,
                project_id=by.project_id,
                client_id=installation,
            )
            for number in mutation_numbers
        )
    )


def _a_batch_disagreeing_on_its_tenant_over_mutation_numbers(
    party: Party, *, at: tuple[int, int]
) -> JsonObject:
    """Two operations of one project and one installation, addressed at two tenants."""
    first, second = at
    installation = uuid4()
    return _a_batch_of(
        _authored_at(
            first,
            tenant_id=party.tenant_id,
            project_id=party.project_id,
            client_id=installation,
        ),
        _authored_at(
            second, tenant_id=uuid4(), project_id=party.project_id, client_id=installation
        ),
    )


def _a_batch_disagreeing_on_its_project_over_mutation_numbers(
    party: Party, *, at: tuple[int, int]
) -> JsonObject:
    """Two operations of one tenant and one installation, addressed at two projects."""
    first, second = at
    installation = uuid4()
    return _a_batch_of(
        _authored_at(
            first,
            tenant_id=party.tenant_id,
            project_id=party.project_id,
            client_id=installation,
        ),
        _authored_at(second, tenant_id=party.tenant_id, project_id=uuid4(), client_id=installation),
    )


def _a_batch_disagreeing_on_its_installation_over_mutation_numbers(
    party: Party, *, at: tuple[int, int]
) -> JsonObject:
    """Two operations of one tenant and one project, authored on two installations."""
    first, second = at
    return _a_batch_of(
        _authored_at(
            first, tenant_id=party.tenant_id, project_id=party.project_id, client_id=uuid4()
        ),
        _authored_at(
            second, tenant_id=party.tenant_id, project_id=party.project_id, client_id=uuid4()
        ),
    )


def test_a_batch_whose_mutation_numbers_ascend_one_at_a_time_answers_with_its_first() -> None:
    """ADR-0010 decision 6's addition of 2026-08-13 with M10's Requirement: a client mints one
    contiguous stream per clientID, tenant and project, so a batch cut from it ascends one at a
    time, and the number it starts at is what the comparison against the cursor is taken on. The
    positive control the three refusals below depend on, since a rule that refuses every batch
    satisfies all three of them on its own.

    **The stream starts at four rather than at zero deliberately.** Where a batch begins is the
    client's and is not this rule's business: a batch is a bounded slice of a queue (ADR-0004
    decision 3), so every slice after the first begins above zero, and a rule that answered zero
    regardless, or demanded it, would refuse every flush a long offline trip produces."""
    tenant, project, installation = uuid4(), uuid4(), uuid4()

    batch = _as_authored(
        _authored_at(4, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(5, tenant_id=tenant, project_id=project, client_id=installation),
    )

    assert the_mutation_number_this_unbroken_stream_starts_at(batch) == 4


def test_a_batch_that_skips_a_mutation_number_is_refused_rather_than_appended_around_the_hole() -> (
    None
):
    """ADR-0010 decision 6's addition of 2026-08-13, M10's Requirement. A gap inside the batch is
    the same loss a gap above the cursor is, arriving one request earlier: the client's queue is
    persistent and append-only, so a number missing from it means an operation was lost rather than
    never created, and appending what surrounds it writes a chain the client never authored. The
    second assertion is the addition's "told apart", stated on the value the act raised and against
    all four of the refusals it stands beside rather than one."""
    tenant, project, installation = uuid4(), uuid4(), uuid4()

    batch = _as_authored(
        _authored_at(0, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(2, tenant_id=tenant, project_id=project, client_id=installation),
    )

    with pytest.raises(OperationsAreNotOneContiguousStream) as refusal:
        the_mutation_number_this_unbroken_stream_starts_at(batch)

    assert not isinstance(
        refusal.value,
        (
            BatchClaimsNoTenant,
            OperationsDisagreeOnTheirClient,
            OperationsDisagreeOnTheirProject,
            OperationsDisagreeOnTheirTenant,
        ),
    )


def test_a_batch_holding_every_number_out_of_order_is_refused_for_the_chain_it_would_record() -> (
    None
):
    """ADR-0010 decision 6's addition of 2026-08-13: ascending is part of the rule rather than a
    nicety. `append_to_the_operation_log` stamps the per-project version in list order, so a batch
    contiguous as a set and shuffled as a list records a chain in an order the client never
    authored, and PRD M15 replays exactly that order as the evidence a legal-weight feature's
    authorship is made of.

    Not a variation on the case above, and the numbers say why: nothing is missing here, so a rule
    that compares the batch's numbers against a range as a set, or that sorts before it compares,
    is green on this batch and red on that one."""
    tenant, project, installation = uuid4(), uuid4(), uuid4()

    batch = _as_authored(
        _authored_at(0, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(2, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(1, tenant_id=tenant, project_id=project, client_id=installation),
    )

    with pytest.raises(OperationsAreNotOneContiguousStream):
        the_mutation_number_this_unbroken_stream_starts_at(batch)


def test_a_batch_repeating_a_mutation_number_is_refused_though_it_skips_nothing() -> None:
    """ADR-0010 decision 6's addition of 2026-08-13, in the phrasing it was corrected to the same
    day, and this case is what that correction exists for: the numbers ascend by **exactly one at
    every step**. The form it replaced read "skip, or arrive out of ascending order", and a repeat
    is neither, being non-decreasing and missing nothing, so a batch M10's Shape calls
    non-contiguous had no refusal at all.

    Not a variation on either case above, and the addition names the shape that separates them: a
    check reading the batch's numbers as a set against the range its own first and last span is
    green here, because the repeat vanishes into the set, while it is red on the hole and red on the
    shuffle. What the repeat costs is the cursor's meaning, which is the whole of C12: the dedup
    keeps what is strictly above the number the cursor says was applied
    (`the_operations_this_cursor_has_not_seen`), so a number standing for two operations leaves that
    cursor unable to name one of them without the other.

    The repeat is interior rather than at zero, so the number the batch starts at stays a legitimate
    one and this case is about the repeat alone. Repeating zero is the other shape, and it is the
    one the existing suites build by accident, which is the addition's own argument for taking this
    check last."""
    tenant, project, installation = uuid4(), uuid4(), uuid4()

    batch = _as_authored(
        _authored_at(0, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(1, tenant_id=tenant, project_id=project, client_id=installation),
        _authored_at(1, tenant_id=tenant, project_id=project, client_id=installation),
    )

    with pytest.raises(OperationsAreNotOneContiguousStream):
        the_mutation_number_this_unbroken_stream_starts_at(batch)


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_skips_a_mutation_number_is_refused_before_anything_is_bound(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-13: the fifth rule is decidable from the request
    body alone, so it is refused where nothing has been bound, which is the property the addition of
    2026-08-07 says these refusals exist to protect. What that buys is what the pure case cannot
    see: past this boundary the request would bind a real tenant, take that project's version row
    and order a chain with a hole in it under numbers a resync would read back as whole. The 422 is
    the addition's ratified status and stands as the positive control, because an empty binding list
    is what a 401 produces too."""
    browser = a_browser(authenticated_as=alice.user_id)
    skipping = _a_stream_of(0, 2, by=alice)

    with bindings_opened() as bindings:
        response = browser.post(OPERATIONS_PATH, skipping, JSON)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert bindings.tenants == []


@pytest.mark.django_db(transaction=True)
def test_the_contiguity_refusal_is_distinguishable_from_the_four_refusals_it_stands_beside(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-13, which puts the fifth refusal under every clause
    of the additions before it: the five share a status and are told apart by their bodies. Not a
    duplicate of the pure case, and the boundary is why: the validator flattens every typed refusal
    into one `ValueError`, so five distinct classes carrying one message reach the client as one
    answer while the pure assertion stays green. The cost is specific rather than general, and it is
    the one this axis makes worst: a client told only "malformed" regroups its queue by tenant, by
    project or by installation, none of which is what is wrong, and reflushes a batch that is still
    missing an operation it has to go and find. The status assertion is the positive control, since
    a batch this route accepted answers with a body that differs from all four just as readily."""
    browser = a_browser(authenticated_as=alice.user_id)

    skipping = browser.post(OPERATIONS_PATH, _a_stream_of(0, 2, by=alice), JSON)
    on_two_tenants = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    on_two_projects = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    on_two_installations = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_installation_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    empty = browser.post(OPERATIONS_PATH, _a_batch_of(), JSON)

    assert skipping.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert skipping.content not in {
        on_two_tenants.content,
        on_two_projects.content,
        on_two_installations.content,
        empty.content,
    }


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_also_breaks_its_contiguity_still_earns_the_tenant_refusal(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-08-13 puts the fifth check last, and the first of the
    three adjacencies that fixes. `a_feature_create_claiming` defaults every operation to mutation
    number zero, so the disagreeing batches the existing suites build collide on this axis without
    anybody choosing it, and two of those cases assert the status and the empty binding list without
    comparing the body: a contiguity check reached first hands them the wrong refusal and they keep
    passing for the wrong reason. The second assertion is the control that stops the first being
    satisfied by nothing, because if the refusals ever collapsed into one shared body every
    comparison of this shape would agree while the order was free."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_tenants = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    also_skipping = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_tenant_over_mutation_numbers(alice, at=(0, 2)),
        JSON,
    )
    skipping = browser.post(OPERATIONS_PATH, _a_stream_of(0, 2, by=alice), JSON)

    assert also_skipping.content == on_two_tenants.content
    assert skipping.content != on_two_tenants.content


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_also_breaks_its_contiguity_still_earns_the_project_refusal(
    alice: Party,
) -> None:
    """The second adjacency ADR-0010 decision 6's addition of 2026-08-13 fixes. A contiguity check
    placed first is caught by the case above, because the project refusal would collapse onto the
    tenant's in any comparison of the two; a contiguity check placed **between** the tenant and the
    project is caught by nothing that exists, and it is a wrong order all the same. What it costs a
    client is concrete: told its stream has a hole when its projects disagree, it goes looking for
    an operation it never lost and flushes the same batch again."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_projects = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    also_skipping = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_project_over_mutation_numbers(alice, at=(0, 2)),
        JSON,
    )
    skipping = browser.post(OPERATIONS_PATH, _a_stream_of(0, 2, by=alice), JSON)

    assert also_skipping.content == on_two_projects.content
    assert skipping.content != on_two_projects.content


@pytest.mark.django_db(transaction=True)
def test_a_batch_that_also_breaks_its_contiguity_still_earns_the_client_refusal(
    alice: Party,
) -> None:
    """The third adjacency, and the one the addition of 2026-08-13 states in its own words: the
    order is tenant, then project, then clientID, then contiguity. A check that ran fourth instead
    of fifth is invisible to both cases above, since neither posts a batch that disagrees on its
    installation, and it is the position a window would most easily land on by reading the two
    rules as one composition step. The cost is the sharpest of the three: contiguity is measured
    within one flush domain (M10), so a batch of two installations has no stream to be contiguous
    in at all, and answering it with a hole in the stream describes something that does not
    exist."""
    browser = a_browser(authenticated_as=alice.user_id)

    on_two_installations = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_installation_over_mutation_numbers(alice, at=(0, 1)),
        JSON,
    )
    also_skipping = browser.post(
        OPERATIONS_PATH,
        _a_batch_disagreeing_on_its_installation_over_mutation_numbers(alice, at=(0, 2)),
        JSON,
    )
    skipping = browser.post(OPERATIONS_PATH, _a_stream_of(0, 2, by=alice), JSON)

    assert also_skipping.content == on_two_installations.content
    assert skipping.content != on_two_installations.content
