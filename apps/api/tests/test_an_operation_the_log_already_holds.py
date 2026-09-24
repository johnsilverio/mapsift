"""An operation the log already holds is answered with the log's verdict and changes nothing.

Trace: PRD **T2.3**, the addition of 2026-08-11 **as sharpened 2026-09-24 (MAP-74), whole**: an
operation the server already holds, resent and surviving the dedup filter because it arrived under a
different mutation number, is answered with **the verdict the log already holds for it**, applied or
refused, the cursor passes it, and it leaves the current state as it found it, being neither judged,
projected nor appended again; an operation is the one its identifier names (M3), whatever a resend
carries. PRD **M15**'s reproducibility clause, on the half MAP-65's task spec split off as having a
runtime: a resend of a held operation leaves the current state equal to what the applied log replays
to. **ADR-0010 decision 6's addition of 2026-09-24** is the contract for how a held operation is
answered, what keys it and why it takes no per-project version; **ADR-0014 decision 7's addition**
of the same date for its receiving no new verdict; ADR-0004 decision 2 for a flush left with nothing
to append taking no range; ADR-0012 decision 3's note of 2026-09-24; ADR-0005 sections 3 and 4 for
the binding every read here happens inside. I2, I9; C12, C7.

**Here rather than under either package, on the gate ADR-0007 section 6 keeps this directory for**:
the cases proving a resend changed nothing read `sync`'s log and `layers`' current state together.

**Everything goes through the route and never through the writer**, on the ground the flush modules
already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only transaction
is its own context manager is green against an implementation that has none. **Every read forces
its rows inside the binding that authorised it**, because a queryset evaluated after the block
closes is answered by the policy with zero rows and no exception.

**Every resend here keeps its operation identifier and moves its mutation number above the
cursor**, which is the one shape that reaches this rule at all: at or below the cursor the dedup
drops it first (`mapsift/sync/tests/test_dedup_and_the_echoed_cursor.py`).

What is deliberately not here, each with the issue that owns it: the record a held operation
leaves, which is `mapsift/sync/tests/test_the_flush_decision_trail.py`'s; **two flushes of one
installation in flight at once**, where the loser decides before the winner's log holds anything
and the append's tolerance of an identity conflict is still what it needs (**MAP-76**); **one
operation identifier twice inside one batch**, and whether a resend reusing a held identifier with
different content is a violation to be recorded (**MAP-73**); the resync read's verdict filter
(**MAP-22**).
"""

import json
from collections.abc import Sequence
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import GEOSGeometry, Point
from django.test import Client

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
    a_layer_this_project_lacks,
    second_project_of,
    statements_reaching,
)
from mapsift.common.binding import tenant_scope
from mapsift.layers.models import Feature
from mapsift.layers.rules import GeometryKind, StorageClass
from mapsift.layers.services import create_layer
from mapsift.sync.models import OperationLogEntry, ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# M5 rule 1: SIRGAS 2000, the one frame stored geometry is in.
STORAGE_FRAME_SRID = 4674

# The success body as ADR-0010 decision 6's addition of 2026-09-17 closes it. Literals rather than
# reads off the enum that carries a reason, because a case comparing an enum against itself cannot
# notice a member being renamed.
THE_ECHO = "last_decided_mutation_number"
THE_REFUSALS = "refused"
THE_MUTATION_NUMBER_REFUSED = "mutation_number"
THE_REASON = "reason"
NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"

# The log column the server writes its decision on and the member saying it applied the operation
# (ADR-0014 decisions 3 and 4), which is what the replay the reproducibility clause runs is read
# through (M15's Shape as added 2026-09-17).
THE_VERDICT = "verdict"
APPLIED = "applied"

# The catalog member that carries a geometry (M9), as the envelope spells its type.
THE_OPERATION_THAT_SETS_A_GEOMETRY = "feature.geometry.set"

# Two places a field client surveys, differing in both coordinates so a geometry stored with its
# axes swapped is equal to neither, and neither the place `a_geometry_set_claiming` carries by
# default, so an arranger that stopped forwarding `at` leaves a geometry assertion red.
A_PLACE_IN_THE_FIELD = (-47.6, -15.9)
ANOTHER_PLACE_IN_THE_FIELD = (-47.5, -15.4)


def _an_element_point_layer_of(party: Party, *, layer_id: UUID) -> None:
    """One element layer of the point family in this party's project (M2).

    Element and point because a served layer's operations and a geometry outside the family are
    refused for reasons of their own, and a resend this module needs applied the first time would
    otherwise be refused for one of them.
    """
    with tenant_scope(party.tenant_id):
        create_layer(
            layer_id=layer_id,
            tenant_id=party.tenant_id,
            project_id=party.project_id,
            name="vegetation cover",
            geometry_kind=GeometryKind.POINT,
            storage_class=StorageClass.ELEMENT,
        )


def _a_queue_of(*operations: JsonObject) -> JsonObject:
    """One flush's body: one installation's operations in one project of one tenant (M8, M9)."""
    return {"operations": list(operations)}


def _a_feature_create(
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    from_installation: UUID,
    mutation_number: int,
    operation_id: UUID | None = None,
) -> JsonObject:
    """The catalog's create, addressed at one layer and one feature of this party's project."""
    return a_feature_create_claiming(
        party.tenant_id,
        operation_id=operation_id,
        client_id=from_installation,
        mutation_number=mutation_number,
        project_id=party.project_id,
        layer_id=layer_id,
        feature_id=feature_id,
    )


def _a_geometry_set(
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    at: tuple[float, float],
    from_installation: UUID,
    mutation_number: int,
    operation_id: UUID | None = None,
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


def _resent_under(mutation_number: int, operation: JsonObject) -> JsonObject:
    """One operation as its client sends it again, identical but for the mutation number.

    The resend T2.3 is about is the same operation, so everything but the number is carried over
    rather than rebuilt, and a case that changes anything else says so at its own call site.
    """
    return {**operation, "mutation_number": mutation_number}


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The reason the flush modules give: an arrange step that quietly starts being refused leaves the
    assertions standing and the case vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _as_the_storage_frame_holds_it(place: tuple[float, float]) -> Point:
    """A place as a geometry in the one frame storage declares (M5 rule 1)."""
    return Point(place[0], place[1], srid=STORAGE_FRAME_SRID)


def _the_features_the_projection_holds(party: Party) -> set[UUID]:
    """Every feature the current-state table holds for a tenant (M15, ADR-0012 decision 1)."""
    with tenant_scope(party.tenant_id):
        return set(Feature.objects.values_list("id", flat=True))


def _the_layer_the_projection_files(party: Party, feature_id: UUID) -> UUID:
    """The layer one projected feature belongs to, read by identifier so an absent row raises."""
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).layer_id


def _the_geometry_the_projection_holds(party: Party, feature_id: UUID) -> GEOSGeometry | None:
    """The current geometry of one feature, which is the state the application reads (M15)."""
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).geometry


def _the_applied_chain_of(party: Party, feature_id: UUID) -> list[JsonObject]:
    """One feature's **applied** operations in server order, which is the chain M15's
    reproducibility clause replays: a refused entry is on the log and outside the replay (M15's
    Shape as added 2026-09-17), and the per-project version is the only axis that is server order
    rather than a client's claim (M10, ADR-0004 decision 2)."""
    with tenant_scope(party.tenant_id):
        return [
            entry.client_half
            for entry in OperationLogEntry.objects.filter(
                client_half__target__feature_id=str(feature_id), **{THE_VERDICT: APPLIED}
            ).order_by("project_version")
        ]


def _the_geometry_a_chain_replays_to(chain: Sequence[JsonObject]) -> GEOSGeometry:
    """The last whole geometry an ordered chain carries (M15, M9's whole-geometry rule).

    Indexes the chain's last geometry operation, so a chain read back empty raises rather than
    agreeing with a projection nobody wrote. The frame is assigned after parsing because GeoJSON
    declares none and GEOS equality compares it (M5 rule 1).
    """
    setting_a_geometry = [
        entry for entry in chain if entry["operation_type"] == THE_OPERATION_THAT_SETS_A_GEOMETRY
    ]
    read = GEOSGeometry(json.dumps(setting_a_geometry[-1]["payload"]["geometry"]))
    read.srid = STORAGE_FRAME_SRID
    return read


def _the_version_of_each_operation(party: Party) -> dict[UUID, int]:
    """What the log recorded as each operation's place in its project's order (ADR-0004 4)."""
    with tenant_scope(party.tenant_id):
        return dict(OperationLogEntry.objects.values_list("operation_id", "project_version"))


def test_a_create_the_log_holds_resent_is_answered_as_applied_rather_than_as_already_created(
    alice: Party,
) -> None:
    """T2.3 as sharpened 2026-09-24, where it meets M9's clause of the same day. The most ordinary
    resend there is, a client sending its own create again because the acknowledgement never
    arrived, names a feature the tenant now holds, **because that create is what made it held**.
    Judged again, it is `feature_already_created`; T2.3 answers it with the verdict the log holds,
    which is applied, so the refusal list is empty and the flush echoes past it.

    **The operation is resent identical but for its mutation number**, which is the shape that sets
    the two rules against each other. The dedup module's
    `test_an_operation_the_server_already_holds_is_answered_as_applied_rather_than_refused`
    resends a held identifier carrying a freshly minted feature, which a second judgement admits
    anyway, so it cannot tell answering from judging and this case can.

    **Green before MAP-68 and MAP-74 land, and not deletable for it**: nothing refuses a create
    today, so this is the case that turns red the moment the refusal lands without the held rule in
    front of it, and a legitimate resend becomes an error a client cannot tell from a real one."""
    layer_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=layer_id)
    created = _a_feature_create(
        alice,
        layer_id=layer_id,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(created))

    resent = browser.post(OPERATIONS_PATH, _a_queue_of(_resent_under(1, created)), JSON)

    assert resent.status_code == HTTPStatus.OK
    assert resent.json() == {THE_ECHO: 1, THE_REFUSALS: []}


def test_a_create_the_log_holds_resent_naming_another_layer_leaves_its_feature_where_it_was(
    alice: Party,
) -> None:
    """T2.3 as sharpened 2026-09-24: held means the operation's **identifier** is on the tenant's
    log, **whatever the resend carries** (M3; ADR-0010 decision 6's addition of 2026-09-24), and a
    held operation is not projected again. Measured at the pickup, a create resent under its held
    identifier naming a second layer re-filed the feature there, while the log's only entry for the
    operation still named the first.

    **The resend names another layer the project holds**, so nothing but the identifier says this
    is the operation already applied, and it is the arrangement ADR-0010's addition gives for the
    keying: a resend carrying another address that went around the refusals about the feature.
    The layer is read by identifier, so a projection that lost the row raises.

    **The answer is asserted before the state**, the control the feature module uses for every case
    about where a feature stayed: a held rule keyed on the operation's content rather than its
    identifier judges this resend a second create of a held feature, refuses it
    `feature_already_created`, and leaves the feature exactly where this rule does."""
    the_layer_it_was_created_in, another_layer, feature_id = uuid4(), uuid4(), uuid4()
    the_create, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=the_layer_it_was_created_in)
    _an_element_point_layer_of(alice, layer_id=another_layer)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_was_created_in,
                feature_id=feature_id,
                operation_id=the_create,
                from_installation=installation,
                mutation_number=0,
            )
        ),
    )

    resent_naming_another_layer = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=another_layer,
                feature_id=feature_id,
                operation_id=the_create,
                from_installation=installation,
                mutation_number=1,
            )
        ),
        JSON,
    )

    assert resent_naming_another_layer.json() == {THE_ECHO: 1, THE_REFUSALS: []}
    assert _the_layer_the_projection_files(alice, feature_id) == the_layer_it_was_created_in


def test_a_geometry_the_log_holds_resent_leaves_the_state_what_the_applied_chain_replays_to(
    alice: Party,
) -> None:
    """M15's reproducibility clause, on the half this task owns (MAP-65's split): a resend of a
    held operation leaves the current state equal to what the applied log replays to, which T2.3 as
    sharpened 2026-09-24 delivers by not projecting it again. Measured at the pickup, an older
    geometry set resent under a new mutation number put the older geometry back over a newer one,
    while the log's chain still ended on the newer one: the projection had stopped being the log's.

    **The resent geometry is the older of two**, which is the direction that makes this observable
    at all: resending the newer one leaves the state where it was whether or not it is projected.

    **The replay is asserted against a literal first**, on the ground the projection module gives: a
    chain that replays to the wrong place and a projection holding the same wrong place agree, and
    only the literal says which place the chain ends on."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=layer_id)
    the_older_geometry = _a_geometry_set(
        alice,
        layer_id=layer_id,
        feature_id=feature_id,
        at=A_PLACE_IN_THE_FIELD,
        from_installation=installation,
        mutation_number=1,
    )
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            the_older_geometry,
        ),
    )
    _the_server_took(
        browser,
        _a_queue_of(
            _a_geometry_set(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            )
        ),
    )

    _the_server_took(browser, _a_queue_of(_resent_under(3, the_older_geometry)))
    replayed = _the_geometry_a_chain_replays_to(_the_applied_chain_of(alice, feature_id))

    assert replayed == _as_the_storage_frame_holds_it(ANOTHER_PLACE_IN_THE_FIELD)
    assert _the_geometry_the_projection_holds(alice, feature_id) == replayed


def test_an_operation_the_log_holds_refused_is_answered_with_that_refusal_when_resent(
    alice: Party,
) -> None:
    """T2.3 as sharpened 2026-09-24, for a held **refused** operation: it is answered with the
    verdict the log holds, listed under `refused` **under the mutation number it arrived with and
    the reason the log holds** (ADR-0010 decision 6's addition of 2026-09-24). Answering it refused
    is not the refusal T2.3's addition of 2026-08-11 forbids, which was refusing a legitimate
    resend; it reports a decision already taken.

    **The layer the create named is created between the two flushes**, which is what makes the
    answer the log's rather than a second judgement's: judged again, the resend names a layer the
    project now holds and is admitted, which is what the route did when this was measured at the
    pickup, projecting an operation the log records as refused (ADR-0014 decision 3).

    The whole body is compared, because ADR-0010 decision 6 closes it and the echo passes the
    resend, which is decided (ADR-0014 decision 5)."""
    a_layer_created_too_late, installation = a_layer_this_project_lacks(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    refused_the_first_time = _a_feature_create(
        alice,
        layer_id=a_layer_created_too_late,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(refused_the_first_time))
    _an_element_point_layer_of(alice, layer_id=a_layer_created_too_late)

    resent = browser.post(
        OPERATIONS_PATH, _a_queue_of(_resent_under(1, refused_the_first_time)), JSON
    )

    assert resent.status_code == HTTPStatus.OK
    assert resent.json() == {
        THE_ECHO: 1,
        THE_REFUSALS: [{THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT}],
    }


def test_an_operation_the_log_holds_refused_is_not_projected_when_resent(alice: Party) -> None:
    """T2.3 as sharpened 2026-09-24 on the state rather than the answer, with ADR-0014 decision 3:
    a refused entry is not part of the current state, and a resend of it is not projected, so the
    state still carries nothing of it once the reason it was refused has gone away.

    **A create of another feature travels beside the resend and is applied**, so the projection is
    compared whole, and a flush that projected nothing at all is red rather than right by chance."""
    a_layer_created_too_late, installation = a_layer_this_project_lacks(), uuid4()
    drawn_since = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    refused_the_first_time = _a_feature_create(
        alice,
        layer_id=a_layer_created_too_late,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(refused_the_first_time))
    _an_element_point_layer_of(alice, layer_id=a_layer_created_too_late)

    _the_server_took(
        browser,
        _a_queue_of(
            _resent_under(1, refused_the_first_time),
            _a_feature_create(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=drawn_since,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
    )

    assert _the_features_the_projection_holds(alice) == {drawn_since}


def test_a_flush_whose_every_new_operation_the_log_already_holds_takes_no_per_project_version(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-24: a held operation is not appended, so it takes
    no per-project version, and **ADR-0004 decision 2's rule against reaching the allocation with
    nothing to append applies when every fresh operation is held**. The allocating statement creates
    the counter row on first use and holds it to the commit, so reaching it here takes the one hot
    row per project for a flush that orders nothing.

    Asserted as statements reaching the counter rather than as a version that did not move, on the
    argument the dedup and gap modules make for this instrument: a range of zero leaves the number
    untouched while still taking the row. The status is the positive control, since a batch refused
    before the allocation touches the row zero times too."""
    layer_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=layer_id)
    created = _a_feature_create(
        alice,
        layer_id=layer_id,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(created))

    with statements_reaching(ProjectVersionCounter._meta.db_table) as allocation:
        resent = browser.post(OPERATIONS_PATH, _a_queue_of(_resent_under(1, created)), JSON)

    assert resent.status_code == HTTPStatus.OK
    assert allocation == []


def test_a_flush_resending_only_a_refusal_the_log_holds_takes_no_per_project_version(
    alice: Party,
) -> None:
    """T2.3 as sharpened 2026-09-24, *nor appended again*, for the verdict the case above does not
    hold: a held **refused** operation is not appended either, so it takes no per-project version,
    and ADR-0004 decision 2's rule against reaching the allocation with nothing to append holds for
    a flush whose every fresh operation is a refusal the log already keeps (ADR-0010 decision 6's
    addition of 2026-09-24).

    **The refusal is where a second append is nearest to hand**, since the held one is listed under
    `refused` and every other refusal on that list is written to the log, while the log's identity
    constraint drops the duplicate silently and leaves only the allocation to show it. The status is
    the positive control, for the reason the case above gives."""
    installation = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    refused_the_first_time = _a_feature_create(
        alice,
        layer_id=a_layer_this_project_lacks(),
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(refused_the_first_time))

    with statements_reaching(ProjectVersionCounter._meta.db_table) as allocation:
        resent = browser.post(
            OPERATIONS_PATH, _a_queue_of(_resent_under(1, refused_the_first_time)), JSON
        )

    assert resent.status_code == HTTPStatus.OK
    assert allocation == []


def test_a_flush_whose_every_new_operation_the_log_already_holds_still_moves_the_cursor_past_it(
    alice: Party,
) -> None:
    """PRD T2.3 as sharpened 2026-09-24, *the cursor passes it*, with ADR-0010 decision 6's addition
    of the same date, *the cursor still passes it, since it is decided*: a flush whose every
    operation above the cursor is held appends nothing and projects nothing, and it still raises
    this installation's stored cursor, because under C12 the client advances from the echo it was
    told, and that echo names the resend.

    **What is read is the next flush of the same installation**, because the all-held flush's own
    echo is taken from the batch it carried and says the same number whether or not the cursor was
    written. A stored cursor left behind answers the operation drawn next with `gap_above_cursor`
    and asks the client to resend from an operation the server has already decided, which the
    client's own dedup will never send again: the stream stalls against I2.

    The whole body is compared, because ADR-0010 decision 6 closes it."""
    layer_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=layer_id)
    created = _a_feature_create(
        alice,
        layer_id=layer_id,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(created))
    _the_server_took(browser, _a_queue_of(_resent_under(1, created)))

    drawn_since = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert drawn_since.json() == {THE_ECHO: 2, THE_REFUSALS: []}


def test_an_operation_the_tenants_log_holds_is_held_though_it_arrives_in_another_projects_stream(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-24: held means the operation identifier is on
    **the tenant's log**, whatever the resend carries (M3), and the log keeps one entry per
    operation within its tenant rather than within a project. An operation applied in one project
    and arriving in another project's stream is therefore held there too: answered with the verdict
    the log holds and not projected again (T2.3 as sharpened that day).

    **The second flush is another installation's, opening at mutation number zero in the tenant's
    second project**, because a flush addresses one project and its stream is per project (M10),
    and the operation carries a target there naming a feature nobody holds on a layer that project
    holds. A second judgement admits it and projects that feature, which is what a held lookup
    scoped to the flush's project does, finding nothing on that project's part of the log.

    **The answer is asserted first, as the control**: a resend refused for its arrangement leaves
    the projection as this rule does. The projection is compared whole, the feature the first flush
    created being the positive control."""
    the_operation, applied_first, named_by_the_resend = uuid4(), uuid4(), uuid4()
    the_layer_it_was_applied_to = uuid4()
    the_other_project = second_project_of(alice)
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=the_layer_it_was_applied_to)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_was_applied_to,
                feature_id=applied_first,
                operation_id=the_operation,
                from_installation=uuid4(),
                mutation_number=0,
            )
        ),
    )

    arriving_in_the_other_project = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            a_feature_create_claiming(
                alice.tenant_id,
                operation_id=the_operation,
                client_id=uuid4(),
                mutation_number=0,
                project_id=the_other_project,
                feature_id=named_by_the_resend,
            )
        ),
        JSON,
    )

    assert arriving_in_the_other_project.json() == {THE_ECHO: 0, THE_REFUSALS: []}
    assert _the_features_the_projection_holds(alice) == {applied_first}


def test_an_operation_the_log_already_holds_leaves_no_hole_in_its_projects_version(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-24 on the arm the case above cannot reach, a held
    operation travelling beside a new one: **a version allocated for an entry the identity
    constraint then drops is a hole in the resync axis** (M10), and the held operation takes none.

    **This is not an assertion that the axis is contiguous**, which the addition's clarification of
    the same day says its sentence is not: the per-project version is monotonic (M10), a refused
    entry takes a version the resync read filters out (ADR-0014 decision 3), and
    `test_a_later_flush_continues_the_projects_version_above_the_flush_before_it` asserts only
    monotonic for that reason. It names **this** burn. Here the only operation appended beside the
    held one is the new create, and ADR-0004 decision 2's RANGE rule allocates exactly the width of
    what is appended, so a held operation taking no version is the new create landing one above the
    held one's version, and a version burnt for the resend puts it two above."""
    layer_id, installation, drawn_since = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_point_layer_of(alice, layer_id=layer_id)
    held = uuid4()
    created = _a_feature_create(
        alice,
        layer_id=layer_id,
        feature_id=uuid4(),
        operation_id=held,
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(created))

    _the_server_took(
        browser,
        _a_queue_of(
            _resent_under(1, created),
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                operation_id=drawn_since,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
    )
    version_of = _the_version_of_each_operation(alice)

    assert version_of[drawn_since] == version_of[held] + 1


def test_a_held_refusal_takes_its_place_in_the_refusal_list_by_the_mutation_number_it_arrived_with(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-24 with its addition of 2026-09-17: a held refused
    operation is listed under `refused` under the mutation number it arrived with, and **the list
    ascends by mutation number**, so a held refusal sits among the fresh ones by that number rather
    than being gathered at either end of the list.

    **The held refusal travels between two fresh ones**, which is the only arrangement that tells
    the promised order from both concatenations an implementation deciding the two kinds apart can
    reach: held first or held last is red either way. The layer the held operation named exists by
    the time it is resent, so a second judgement admits it and leaves it out of the list entirely,
    which is red too."""
    a_layer_created_too_late, installation = a_layer_this_project_lacks(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    refused_the_first_time = _a_feature_create(
        alice,
        layer_id=a_layer_created_too_late,
        feature_id=uuid4(),
        from_installation=installation,
        mutation_number=0,
    )
    _the_server_took(browser, _a_queue_of(refused_the_first_time))
    _an_element_point_layer_of(alice, layer_id=a_layer_created_too_late)

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_this_project_lacks(),
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=1,
            ),
            _resent_under(2, refused_the_first_time),
            _a_feature_create(
                alice,
                layer_id=a_layer_this_project_lacks(),
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=3,
            ),
        ),
        JSON,
    )

    assert answered.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        {THE_MUTATION_NUMBER_REFUSED: 2, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        {THE_MUTATION_NUMBER_REFUSED: 3, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
    ]
