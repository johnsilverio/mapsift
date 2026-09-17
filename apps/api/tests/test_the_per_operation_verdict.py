"""The flush decides each operation of its batch rather than the batch.

Trace: PRD **T5.2**'s acceptance as added 2026-09-17 (the flag is a verdict on that operation
alone, so the operations after it in the same stream still reach the server); **M9**'s final
acceptance clause for the shape that refusal takes, flagged and retained and never discarded;
**M10**'s acceptance as revised 2026-09-17 (the cursor the dedup reads is the last-**decided**, so
a refused operation is deduplicated on resend exactly as an applied one is) together with its
applies-nothing-at-all clause, which is about a **gap** and is untouched; **M4** and **T2.3** for
the cursor and the one echo a client advances from; **M15**'s Shape as added 2026-09-17 (a refused
operation is a log entry as well, carrying its verdict and its reason, and is **not** part of the
projection **nor of the replay the reproducibility clause runs**, whose second half is witnessed in
`test_the_projection_at_the_flush.py`, where the chain reader that would otherwise walk a refusal
lives); **M8**'s server half, whose verdict set gained a second declarant the same day;
**M13**, whose three members are deliberately not this one. Invariants **I2**, **I9**, **I10**;
constraints **C7**, **C12**, **C13**.

**ADR-0014 is the mechanism and this module is its acceptance.** Decision 1 for the criterion that
separates a whole-batch refusal from an operation verdict, decision 2 for `no_layer_in_this_project`
leaving the `409` set, decision 3 for the retention on the log, decision 4 for the verdict's name,
decision 5 for the cursor advancing over a refusal and being renamed with its meaning (foundation
v0.19), decision 6 for the response object and its status, and decision 7 for each operation being
judged against the state the operations before it leave. ADR-0010 decision 6's addition of
2026-09-17 is where that response shape lands; ADR-0012 decision 3's narrowing of the same day is
where the projection's fold does; ADR-0005 sections 3 and 4 are why every read below happens inside
a binding.

**Here rather than under either package, and the reason is a gate rather than a preference**, the
same one `test_the_projection_at_the_flush.py` records: the subject spans two packages, because the
verdict is written on `sync`'s log and withheld from `layers`' projection, and a module under either
package's `tests/` breaks the `protected` import contract reading the other's models. ADR-0007
section 6 keeps `apps/api/tests/` for exactly this.

**Everything goes through the route and never through the writer**, on the ground the flush modules
already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only transaction
is the one it opened is green against an implementation that has none.

**A state read after a per-operation refusal is a real read, and that is what separates this module
from its neighbours.** The measurement carried from MAP-45 and MAP-46 is that state read after a
refusal is blind to whatever the refusal unwinds, because the cursor write and the log append sit
inside the `atomic()` block `tenant_scope` opens and the refusal is caught outside it. That holds
for the two cursor refusals, which still refuse the whole batch and still roll it back, and it stops
holding for the verdict this task creates: the flush **commits**, so what the projection holds
afterwards is evidence rather than silence. The one case below that reads a refusal which does roll
back witnesses the statements as they run instead.

What is deliberately not here, each with the issue that owns it: the two refusals a layer's own
declarations make, its storage class and its geometry family (**MAP-66**, parked, its pure
predicates on this branch with no caller); the author who lost authorization, T5.2's other half
(**MAP-37**), which has no runtime because the permission model PRD 10.6 defers is not built; the
client's local queue, the optimistic preview a refusal must not leave standing and the resolution
surface (**MAP-15**, **MAP-16**, T5.2's open `Open / ADR`); the resync read that must filter on the
verdict (**MAP-22**); the per-feature version, the applied rule version and the legal weight in
force (**MAP-38**, **OQ-8**, and the third with no owner in the canon), which ADR-0014 decision 3
says it decides nothing about; the log's `applied_at` column and the nullability paired to the
verdict (**MAP-53**, whose column this branch does not carry); what a wire-legal geometry payload is
(**MAP-70**) and what a create addressing an existing feature means (**MAP-68**).
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import GEOSGeometry, Point
from django.test import Client

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_geometry_set_claiming,
    a_layer_this_project_lacks,
    an_operation_on_a_layer_this_project_holds,
    an_operation_on_a_layer_this_project_lacks,
    statements_reaching,
)
from mapsift.common.binding import tenant_scope
from mapsift.layers.models import Feature
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# The success body as ADR-0010 decision 6's addition of 2026-09-17 closes it. The echo is renamed
# with its meaning (foundation v0.19): the cursor counts what the server decided, applied or
# refused, and a key reading last-applied would lie about the number a client advances from.
THE_ECHO = "last_decided_mutation_number"
THE_REFUSALS = "refused"
# The refusal names its axis rather than an index into the batch, because a position in a list is
# not an axis and does not survive a client regrouping its queue (that addition, and of 2026-08-11).
THE_MUTATION_NUMBER_REFUSED = "mutation_number"
THE_REASON = "reason"

# The first member of the refusal set, which keeps the spelling it had while it was a stream
# refusal (ADR-0014 decision 2). A literal rather than a read off the enum that carries it, on this
# suite's standing rule for a wire value: a case comparing an enum against itself cannot notice a
# member being renamed.
NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"

# The object the two cursor refusals still answer with, and the two members that set returns to
# (ADR-0010 decision 6's addition of 2026-08-13, as ADR-0014 decision 2 leaves it).
THE_RESTART_POINT = "resend_from_mutation_number"
A_GAP_ABOVE_THE_CURSOR = "gap_above_cursor"
NO_CURSOR_IN_THIS_DOMAIN = "no_cursor_in_this_domain"

# The two columns a log entry gains and the two members the envelope's closed verdict set carries
# once the refusal joins it (ADR-0014 decisions 3 and 4). The column is storage for that contract
# and never a second declaration of it (ADR-0004 decision 4's rule), and the values are spelled as
# literals for the reason the reason above is.
THE_VERDICT = "verdict"
THE_REFUSAL_REASON = "refusal_reason"
APPLIED = "applied"
REFUSED = "refused"

# M5 rule 1: SIRGAS 2000, the one frame stored geometry is in. Spelled here rather than imported
# for the reason `test_the_projection_at_the_flush.py` spells it: the frame a case asserts against
# is the requirement's value, and a case reading it from the code it checks cannot disagree with it.
STORAGE_FRAME_SRID = 4674

# Two places a field client draws in, differing in both coordinates so a geometry that reached
# storage with its axes swapped is equal to neither. Neither is the place `a_geometry_set_claiming`
# carries by default, so an arranger that stopped forwarding `at` leaves the geometry case red.
A_PLACE_IN_THE_FIELD = (-47.7, -15.7)
ANOTHER_PLACE_IN_THE_FIELD = (-47.3, -15.2)


def _a_queue_of(*operations: JsonObject) -> JsonObject:
    """One flush's body: one installation's operations in one project of one tenant (M8, M9)."""
    return {"operations": list(operations)}


def _a_geometry_set(
    party: Party,
    *,
    feature_id: UUID,
    at: tuple[float, float],
    from_installation: UUID,
    mutation_number: int,
    operation_id: UUID | None = None,
    layer_id: UUID | None = None,
) -> JsonObject:
    """The catalog's geometry set, carrying the whole geometry rather than a delta (M9)."""
    return a_geometry_set_claiming(
        party.tenant_id,
        operation_id=operation_id,
        client_id=from_installation,
        mutation_number=mutation_number,
        project_id=party.project_id,
        layer_id=layer_id,
        feature_id=feature_id,
        at=at,
    )


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The reason the three flush modules give: this route collects a typed refusal with nearly every
    task in this milestone, so an arrange step that quietly starts being refused leaves the
    assertions standing and the case vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _the_features_the_projection_holds(party: Party) -> set[UUID]:
    """Every feature the current-state table holds for a tenant (M15, ADR-0012 decision 1).

    Forced inside the binding that authorised it, because a queryset evaluated after the block
    closes is answered by the policy with zero rows and no exception (ADR-0005 sections 3 and 4).
    """
    with tenant_scope(party.tenant_id):
        return set(Feature.objects.values_list("id", flat=True))


def _the_geometry_the_projection_holds(party: Party, feature_id: UUID) -> GEOSGeometry | None:
    """The current geometry of one feature, which is the state the application reads (M15).

    Read by identifier, so a projection that dropped the feature raises rather than answering the
    same nothing a cleared column would.
    """
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).geometry


def _the_verdict_the_log_holds_for(party: Party, operation_id: UUID) -> dict[str, object]:
    """What the server decided about one operation, as the log keeps it (M15, ADR-0014 decision 3).

    Asked for **the** entry rather than for the first of however many there are, which is the
    sibling below's reading and is load-bearing in a module whose subject is retention on an
    append-only log: an implementation that appended the operation twice, once as it walked the
    batch and once as it recorded the verdict, is the defect nearest to hand here, and an index
    answers it with whichever row came back first. It raises here instead, and it raises on an
    absent entry too, rather than answering a missing verdict a case could read as an applied one.

    Answered as the two columns named rather than as a bare pair, so a case comparing it says which
    column it is comparing.
    """
    with tenant_scope(party.tenant_id):
        verdict, refusal_reason = OperationLogEntry.objects.values_list(
            THE_VERDICT, THE_REFUSAL_REASON
        ).get(operation_id=operation_id)

    return {THE_VERDICT: verdict, THE_REFUSAL_REASON: refusal_reason}


def _the_operation_as_its_client_authored_it(party: Party, operation_id: UUID) -> ClientHalf:
    """One operation as its client authored it, read back off the log through the contract (M8).

    Named for what it answers rather than for the table it reads, because `the log holds` and
    `the log kept` are one word apart and this suite already has two readers spelled the first way.

    Through the generated reader rather than field by field, because a field-by-field comparison
    pins the fields somebody remembered.
    """
    with tenant_scope(party.tenant_id):
        return ClientHalf.model_validate(
            OperationLogEntry.objects.get(operation_id=operation_id).client_half
        )


def _as_the_storage_frame_holds_it(place: tuple[float, float]) -> Point:
    """A place as a geometry in the one frame storage declares (M5 rule 1).

    GEOS equality compares the frame beside the coordinates, so a geometry compared without it is
    two frames being compared rather than two places.
    """
    return Point(place[0], place[1], srid=STORAGE_FRAME_SRID)


def test_a_flush_the_server_applies_whole_answers_with_an_empty_refusal_list(
    alice: Party,
) -> None:
    """ADR-0014 decision 6 on the side that must not move: a batch the server can apply whole is
    unaffected by any of this, and the only visible difference is the key it echoes from and the
    empty list beside it.

    **The whole body is compared rather than one key of it**, because ADR-0010 decision 6 closes
    this object and has since its addition of 2026-08-11: an unexpected key is a contract change
    that goes through that decision, and this addition is one of those rather than a licence to open
    it.

    **This is the quiet side of the rule the rest of the module is about**, and it is here for the
    reason the dedup suite gives for its own quiet cases: a verdict witnessed only where it refuses
    is satisfied by an implementation that refuses everything, and a client reading a refusal list
    that is absent rather than empty has to tell those two apart itself."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {THE_ECHO: 1, THE_REFUSALS: []}


def test_a_flush_that_refused_one_operation_names_it_by_its_mutation_number_and_answers_two_hundred(
    alice: Party,
) -> None:
    """ADR-0014 decision 6: the batch **was** processed, every operation in it has a verdict, and a
    client that advances from the echo loses nothing, so the status stays `200` and the body grows
    the list of what was refused.

    **`200` is the load-bearing half and it is the argument of 2026-08-13 taken the other way.**
    There, a gap answering `200` would have been read as an acknowledgement and the client's own
    dedup would then have dropped the operations the gap reported. Here there is nothing to resend:
    the queue is append-only, so the client cannot author anything that changes this answer, and
    `409`'s meaning is unchanged, this stream cannot continue here, which after this decision is
    true of exactly the two cursor reasons.

    **The refusal names its mutation number rather than a position in the batch**, because a
    position is not one of M10's five axes and does not survive a client regrouping its queue.

    The refused operation travels between two the server applies, so a body naming the whole
    batch, or naming the first operation it happened to look at, is red rather than coincidentally
    right."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=2
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        THE_ECHO: 2,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        ],
    }


def test_a_batch_whose_every_operation_is_refused_still_moves_the_cursor_past_them_all(
    alice: Party,
) -> None:
    """ADR-0014 decision 5 at the arm where nothing was applied: the cursor advances to the highest
    mutation number the flush **decided**, and every other case in this module leaves an
    implementation reading it off what it applied a number to answer with.

    **This is the installation's first flush, and that is the arrangement rather than tidiness.** A
    server that writes its cursor row only when something was applied leaves no cursor at all here,
    and the client's next batch then meets `no_cursor_in_this_domain` and is told to rehandshake
    over a stream the server has already decided two operations of; with an applied operation
    anywhere in this batch the row exists and the defect is invisible. It is the same permanent
    stall ADR-0014's Context is about, reached from the other end.

    **Both operations are refused for one reason and both are reported**, which is what says the
    verdicts are per operation rather than one verdict standing for the batch it was found in
    (decision 1). The body is compared whole because ADR-0010 decision 6 closes this object, and a
    list of one here is as red as a list of none.

    Nothing about what an all-refused batch applies is asserted here, because that is not this arm's
    risk: a flush deciding each operation separately applies none of them by construction, and the
    cases beside this one already witness that a refused operation reaches neither the projection
    nor the state the application reads."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        THE_ECHO: 1,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        ],
    }


def test_a_flush_whose_highest_operation_was_refused_still_echoes_that_number(
    alice: Party,
) -> None:
    """Foundation v0.19 with ADR-0014 decision 5 and T2.3: the cursor counts what the server
    **decided**, applied or refused, which is why the key is named the way it is.

    **The refusal is the last operation of the batch, and that is the whole arrangement.** With the
    refusal anywhere else the highest number is one the server applied and a cursor holding
    last-applied answers correctly by accident; with it last, an implementation echoing the highest
    it applied answers zero, the client advances to zero under C12, and its next flush opens at one
    against a server that already holds that number decided.

    The status is the positive control: every other end this route has is a refusal carrying a
    status of its own, so any other answer means this batch never reached a verdict at all."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()[THE_ECHO] == 1


def test_the_operations_around_a_refused_one_are_applied(alice: Party) -> None:
    """T5.2's acceptance as added 2026-09-17 and M9's final clause on the same shape: the refusal
    falls on that operation alone, so the stream behind it still reaches the server.

    **This is the requirement the whole decision exists to deliver.** The client's queue is
    persistent and append-only, so nothing it can send changes the answer to the refused operation,
    and the server applies a stream only in contiguous order (M10); a refusal the batch does not
    survive therefore blocks every operation that installation captured after it, permanently, which
    is the divergence **I2** forbids.

    **One operation on each side of the refusal, rather than one after it.** A batch refused from
    the first bad operation onward leaves the earlier one applied and satisfies a case that only
    looks behind the refusal, so the feature drawn *after* it is what says the stream carried on.

    The projection is what says applied, rather than the log: the log holds the refused operation
    too, by ADR-0014 decision 3, so counting log rows would call a retention an application."""
    drawn_before, drawn_after = uuid4(), uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=drawn_before, from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=drawn_after, from_installation=installation, mutation_number=2
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_features_the_projection_holds(alice) == {drawn_before, drawn_after}


def test_a_refused_operation_is_kept_on_the_log_with_its_verdict_and_its_reason(
    alice: Party,
) -> None:
    """ADR-0014 decision 3 with M15's Shape as added 2026-09-17: the log is the retention T5.2 and
    M9 mean, and the entry carries what the server decided and why.

    **This is where the decision departs from every system it was researched against**, and the
    departure is the product's reason for existing: the geometry was drawn in the field, and a
    refusal that keeps only an error message has discarded the work while reporting it (C7).

    A separate table would be a second home for the same authored operation and M15's chain would
    then have to be read from two places to be complete, which is why the verdict is a column on the
    entry rather than a row somewhere else.

    The status is the positive control: a batch refused whole leaves no entry at all, and an
    assertion about what an entry carries cannot tell that apart from a wrong verdict on its own."""
    refused = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice,
                feature_id=uuid4(),
                operation_id=refused,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_verdict_the_log_holds_for(alice, refused) == {
        THE_VERDICT: REFUSED,
        THE_REFUSAL_REASON: NO_LAYER_IN_THIS_PROJECT,
    }


def test_an_applied_operation_is_kept_on_the_log_with_no_refusal_reason(alice: Party) -> None:
    """ADR-0014 decision 3's other half: the reason is null for an applied entry, and the verdict
    says applied rather than saying nothing.

    **The quiet side of a conditional rule, and it is here for the reason `specs/testing.md` gives
    for every such case:** a verdict witnessed only where it refuses is satisfied by an
    implementation that stamps every entry refused, which would make the resync read MAP-22 inherits
    stream nothing at all to any client.

    It is the same batch as its sibling above, read at the other operation, because two operations
    of one flush differing only in their layer is the narrowest arrangement that can tell the two
    verdicts apart."""
    applied = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice,
                feature_id=uuid4(),
                operation_id=applied,
                from_installation=installation,
                mutation_number=0,
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_verdict_the_log_holds_for(alice, applied) == {
        THE_VERDICT: APPLIED,
        THE_REFUSAL_REASON: None,
    }


def test_a_refused_operation_is_kept_on_the_log_as_the_client_authored_it(alice: Party) -> None:
    """ADR-0014 decision 3 with M8: the entry is written exactly as an applied one is, the client
    half verbatim, because M8 forbids the server rewriting what the client sent.

    **The refused operation carries a geometry, and that is the point of the case rather than
    decoration.** What preserve-not-discard protects here is the work, not the record of a failure:
    an implementation retaining the identifier, the verdict and the reason satisfies every other
    case in this module while the surveyed place it was refused for is gone, which is the
    preserve-not-discard sin wearing a validation costume (C7, M9's own wording).

    The geometry set follows a create for its own feature, because whether an operation addressing a
    feature no applied operation ever created is refused or applied is what ADR-0014 decision 7
    deliberately leaves open."""
    surveyed, drawn_and_refused = uuid4(), uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    refused_where_it_was_drawn = _a_geometry_set(
        alice,
        feature_id=surveyed,
        at=A_PLACE_IN_THE_FIELD,
        operation_id=drawn_and_refused,
        layer_id=a_layer_this_project_lacks(),
        from_installation=installation,
        mutation_number=1,
    )

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=surveyed, from_installation=installation, mutation_number=0
            ),
            refused_where_it_was_drawn,
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_operation_as_its_client_authored_it(
        alice, drawn_and_refused
    ) == ClientHalf.model_validate(refused_where_it_was_drawn)


def test_a_refused_geometry_never_reaches_the_current_state_the_application_reads(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 as narrowed 2026-09-17: the fold walks the operations the flush
    **applied**, not every operation in the batch, or a refusal would leave exactly the state it
    exists to withhold.

    **The feature is surveyed first and moved second, which is what makes the withholding
    observable.** A projection nobody wrote holds nothing and a refusal that wrote nothing leaves
    nothing, and those two are the same answer; a projection that already holds a place is the only
    arrangement where an implementation folding the whole batch is visible, and what it does there
    is overwrite a surveyed point while telling the client the operation was refused.

    **This state read is evidence rather than silence, unlike the ones the two cursor refusals
    admit.** Those roll their transaction back, so a later read is blind to what they unwound; this
    flush commits, because the refusal is itself a write (ADR-0014 decision 3), so what the
    projection holds afterwards is what the server holds.

    The status is the positive control and separates this from the shape it replaces: a whole-batch
    `409` also leaves the stored place alone, so the assertion below is green against it."""
    surveyed = uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=surveyed, from_installation=installation, mutation_number=0
            ),
            _a_geometry_set(
                alice,
                feature_id=surveyed,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )
    moved_on_a_layer_this_project_lacks = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set(
                alice,
                feature_id=surveyed,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                layer_id=a_layer_this_project_lacks(),
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert moved_on_a_layer_this_project_lacks.status_code == HTTPStatus.OK
    assert _the_geometry_the_projection_holds(alice, surveyed) == _as_the_storage_frame_holds_it(
        A_PLACE_IN_THE_FIELD
    )


def test_a_resent_batch_carrying_a_refused_operation_is_deduplicated_rather_than_refused_again(
    alice: Party,
) -> None:
    """M10's acceptance as revised 2026-09-17 with ADR-0014 decision 5: the cursor passes a refused
    operation, so a resend is deduplicated exactly as an applied one is and the client learns of the
    refusal once.

    **A client that resends and is refused a second time is a client that cannot tell a permanent
    verdict from a transport failure**, which is the fragility T2.3's own acceptance already refuses
    on the neighbouring path, and it is what a cursor holding last-applied would produce here for as
    long as that installation holds the operation.

    **The first answer is witnessed rather than assumed.** A route that stopped refusing this
    operation at all would leave the second assertion true and the case green about nothing, and
    this arrangement is exactly the one where that is easy to reach, both flushes carrying the same
    body."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    queued = _a_queue_of(
        an_operation_on_a_layer_this_project_holds(
            alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
        ),
        an_operation_on_a_layer_this_project_lacks(
            alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
        ),
    )

    first = browser.post(OPERATIONS_PATH, queued, JSON)
    resent = browser.post(OPERATIONS_PATH, queued, JSON)

    assert first.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT}
    ]
    assert resent.json() == {THE_ECHO: 1, THE_REFUSALS: []}


def test_the_stream_above_a_refused_operation_still_reaches_the_server(alice: Party) -> None:
    """**I2 through ADR-0014's own Context, and the case the whole decision was taken for.** Three
    rules already closed in the canon combine into a permanent stall: the queue is append-only
    (foundation section 4), the server applies only in contiguous order (M10), and resending
    reproduces the refusal forever. One polygon drawn on the wrong layer therefore blocked every
    operation that installation captured after it, permanently.

    **The second flush is a separate request, which is what the first case about the stream cannot
    show.** There the operations travel in the batch that carried the refusal; here the client comes
    back later with work it drew afterwards, and under a cursor that did not pass the refusal that
    batch opens above a cursor the server never moved and earns a gap it can never fill.

    The projection is compared whole, so a flush that applied the later work and lost the earlier is
    as red as one that applied nothing."""
    drawn_before, drawn_after = uuid4(), uuid4()
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=drawn_before, from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
    )
    drawn_since_the_refusal = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=drawn_after, from_installation=installation, mutation_number=2
            )
        ),
        JSON,
    )

    assert drawn_since_the_refusal.status_code == HTTPStatus.OK
    assert _the_features_the_projection_holds(alice) == {drawn_before, drawn_after}


def test_a_gap_is_measured_against_the_cursor_a_refusal_moved(alice: Party) -> None:
    """M10's gap clause meeting ADR-0014 decision 5: the gap still refuses the whole batch and still
    carries its restart point, and the point it carries is one above the number the server
    **decided**, which is the refused one.

    **The two halves are why this case exists rather than being covered next door.**
    `test_the_typed_resend_on_a_gap.py` already proves a gap is a `409` carrying the first number
    the server has not applied; what has no witness there is that a refused operation counts as
    decided for that arithmetic, so a server answering `1` here would be asking this client to
    resend an operation it has already been given a permanent verdict on.

    The whole body is compared because ADR-0010 decision 6 closes this object too, and its two
    members are untouched by this task: taking the third reason out of that set is what moves, and a
    gap keeps its shape, its status and its restart point."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    _the_server_took(
        browser,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=0
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=1
            ),
        ),
    )
    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            an_operation_on_a_layer_this_project_holds(
                alice, feature_id=uuid4(), from_installation=installation, mutation_number=3
            )
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {THE_REASON: A_GAP_ABOVE_THE_CURSOR, THE_RESTART_POINT: 2}


def test_a_batch_with_no_cursor_is_refused_whole_though_it_carries_an_operation_a_verdict_would_own(
    alice: Party,
) -> None:
    """ADR-0014 decision 1's criterion, on the side that must not move: the batch is refused whole
    where the **remedy is a resend**, and an installation the server holds no cursor for is that
    case whatever else the batch carries.

    **The order is what this pins.** The cursor comparison is taken before any operation is judged,
    so a batch that would earn a per-operation verdict and also opens above a cursor that does not
    exist is answered by the cursor, with M4's reconciliation and its null restart point. An
    implementation deciding the verdicts first answers `200` with a refusal list and tells a client
    that may no longer hold its queue that its stream is fine.

    **The append is witnessed as it runs and never as the rows it left**, the measurement of
    2026-08-14 carried through MAP-45 and MAP-46: this refusal exits the transaction the append
    would have sat in, so nothing survives for a later read to find and a case reading the log
    afterwards is green against a writer that appended. That is the one place in this module where a
    state read proves nothing, because this is the one refusal here that still rolls back."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    with statements_reaching(OperationLogEntry._meta.db_table) as the_append:
        refused = browser.post(
            OPERATIONS_PATH,
            _a_queue_of(
                an_operation_on_a_layer_this_project_holds(
                    alice, feature_id=uuid4(), from_installation=installation, mutation_number=2
                ),
                an_operation_on_a_layer_this_project_lacks(
                    alice, feature_id=uuid4(), from_installation=installation, mutation_number=3
                ),
            ),
            JSON,
        )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {THE_REASON: NO_CURSOR_IN_THIS_DOMAIN, THE_RESTART_POINT: None}
    assert the_append == []
