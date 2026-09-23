"""The flush leaves the current state behind it, in the same transaction that appends the log.

Trace: PRD M15 (the current state the application reads **is** a projection of the append-only log,
and the reproducibility clause that makes the chain evidence) as its materialization is settled by
**ADR-0012 decisions 1, 2, 3 and 6**, with **M15's Shape as added 2026-09-17**, which puts a refused
operation on that log and outside both the projection and the replay the reproducibility clause
runs, so the two readers below are two chains rather than one; PRD T2.2's **requirement sentence**,
the transactionality that
keeps the append and the projection consistent or neither, and not its acceptance list, which is
about a dropped notification recovered by resync and is MAP-22's; PRD M9 (one target path per
operation, and a geometry operation carrying the whole geometry, which is what makes a replay a
latest-row-per-target-path read rather than a fold); PRD M2 (the layer is where the storage class
sits, so every layer arranged here is an element layer); PRD M3 and M5 rule 1 for the identifier the
row is stored under and the frame its geometry is held in; **ADR-0010 decision 6's addition of
2026-09-08** for the typed refusal this write makes reachable, **ADR-0014 decisions 1, 2, 3 and 6**
with **ADR-0012 decision 3's narrowing of 2026-09-17** for the verdict that refusal became and for
what the fold now walks, and **ADR-0012 decision 3's addition of
2026-09-09** for what an operation leaves alone by saying nothing about it; PRD T6.5 with **ADR-0010
decision 6's addition of 2026-08-07** for the comparative form a cross-tenant answer is tested in,
which a feature identifier reaches because it is minted by the client rather than allocated per
tenant (M3, ADR-0006); ADR-0004 decision 2 for where the projection write sits in the flush order;
ADR-0005 sections 3 and 4 for the binding every read and write here happens inside. Invariants I2
and I10; constraints C4, C9, C12.

**Here rather than under either package, and the reason is a gate rather than a preference.** The
subject spans two packages: the flush is `sync`'s and the projection is `layers`', and the
reproducibility case has to read the log and the projection together. Measured 2026-09-08 with
`lint-imports`: a module under `mapsift/sync/tests/` reading `mapsift.layers.models` breaks the
`protected` contract, and one under `mapsift/layers/tests/` reading `mapsift.sync.models` breaks
both the tier contract and the other `protected` one. ADR-0007 section 6 keeps `apps/api/tests/`
for exactly this, and ADR-0007's Consequences say the rest: a feature that needs the layers
contract relaxed is in the wrong package, and so is a test.

**Everything goes through the route and never through the writer**, on the ground the sibling flush
modules already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only
transaction is the one its own context manager opened is green against an implementation that has
none, and the atomicity this task is about is precisely what that would hide.

**Every read of either table forces its rows inside the binding that authorised it.** A queryset
built inside `tenant_scope` and evaluated after that block closes has lost
`SET LOCAL mapsift.tenant_id` and is answered by the policy with **zero rows and no exception**
(measured 2026-08-28 by two parties: 0 rows outside the binding, 2 inside). `TenantOwnedManager`
raises only when a selector is *called* unbound, so nothing in this repository catches the lazy
direction, and every helper below is written against it: nothing answers with a queryset.

What is deliberately not here, each with the issue that owns it: the **per-feature version** and
its column (MAP-38); **`applied_at`** (MAP-53), whose absence is half of why M15's reproducibility
clause is proven as a mechanism here rather than whole; the **legal-weight** qualifier of that same
clause (OQ-8, the environmental engineer's) and the **normalized author** (MAP-37), which is the
other half, so what these cases prove is that replaying one feature's ordered chain reproduces the
geometry the projection holds and never that the chain is attributed; the two refusals a layer's
**own** declarations make once it exists, its storage class and its geometry family (MAP-66), which
is why every layer arranged here is an element layer of the family its features carry; the
**rebuild** path for the projection, whose owner ADR-0012's Consequences decline to name and whose
test M15's acceptance explicitly is not; every **read** of the projection, the container-scoped
selectors of MAP-51 gaining no caller here; and the **sorted batched statement** of ADR-0012
decision 3, whose property is a deadlock count under four concurrent writers rather than anything
one flush can show, and which that ADR spends its own measurement on rather than handing over; the
**frame a wire geometry declares for itself** (MAP-69), the write stamping the storage frame on a
parsed payload being a relabel rather than a transformation, so no payload below carries a `crs`
member of its own and every geometry here is written in the frame it is read back in; a **geometry
payload the parser or the column cannot take** (MAP-70), which this write makes reachable for the
first time by carrying a client's payload to GEOS and PostGIS, so every payload below is one they
take; and whether a **create for a feature that already exists** is legitimate at all (MAP-68),
which the two cases over that shape leave exactly where the ADR left it, pinning what the projection
does with a flush the route accepts today and never that it should.

**One shape nothing here arranges, because nobody has decided it:** a `feature.geometry.set` for a
feature no operation ever created. Every geometry below follows a create for its own feature, in an
earlier flush or in the same batch.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import GEOSGeometry, Point

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
    a_layer_this_project_lacks,
    second_project_of,
)
from mapsift.common.binding import tenant_scope
from mapsift.layers.models import Feature
from mapsift.layers.rules import GeometryKind, StorageClass
from mapsift.layers.services import create_layer
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# M5 rule 1: SIRGAS 2000, the one frame stored geometry is in.
STORAGE_FRAME_SRID = 4674

# The closed success object this route answers with and the refusal the projection makes reachable
# (ADR-0010 decision 6's addition of 2026-09-17, which is where that refusal landed once ADR-0014
# decision 2 took it out of the `409` set). Spelled as literals rather than read off the enums that
# carry them, because these are the wire values those decisions fix and a case comparing an enum
# against itself cannot notice a member being renamed.
THE_ECHO = "last_decided_mutation_number"
THE_REFUSALS = "refused"
THE_MUTATION_NUMBER_REFUSED = "mutation_number"
THE_REASON = "reason"
NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"

# The log column the server writes its decision on, and the member of the envelope's closed verdict
# set that says it applied the operation (ADR-0014 decisions 3 and 4). Named the way
# `test_the_per_operation_verdict.py` names them, which is the module that owns this contract: the
# column is storage for it and never a second declaration of it (ADR-0004 decision 4's rule), and
# the member is a literal rather than a read off the enum, because a case comparing an enum against
# itself cannot notice a member being renamed.
THE_VERDICT = "verdict"
APPLIED = "applied"

# The catalog member that carries a geometry (M9), as the envelope spells its type.
THE_OPERATION_THAT_SETS_A_GEOMETRY = "feature.geometry.set"

# Two places a field client draws in, and they differ in both coordinates so a geometry that
# reached storage with its axes swapped is not equal to either of them. Neither is the place
# `a_geometry_set_claiming` carries when a caller says nothing: set to that one, an arranger that
# stopped forwarding `at` would leave the principal geometry case below green.
A_PLACE_IN_THE_FIELD = (-47.6, -15.9)
ANOTHER_PLACE_IN_THE_FIELD = (-47.5, -15.4)


def _an_element_layer_of(party: Party, *, layer_id: UUID, project_id: UUID | None = None) -> None:
    """One element layer of the point family, in a project of this party's tenant (M2).

    Element rather than served because a served layer's features never enter the operation queue at
    all, and point rather than polygon because a layer's declared family is a contract on its
    features; both refusals are MAP-66's, so an arrangement that ignored either would be arranging
    a batch this route refuses.
    """
    with tenant_scope(party.tenant_id):
        create_layer(
            layer_id=layer_id,
            tenant_id=party.tenant_id,
            project_id=project_id or party.project_id,
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
    operation_id: UUID | None = None,
    from_installation: UUID | None = None,
    mutation_number: int = 0,
) -> JsonObject:
    """The catalog's create, addressed at one layer and one feature of this party's project.

    A thin forward to the shared arranger rather than a second spelling of the envelope document,
    which is the rule `conftest.a_feature_create_claiming` states for itself: the fields a suite has
    to name are its arguments, and everything else has one home. The installation and the mutation
    number carry the shared defaults, so a case posting one operation says nothing about the axes it
    is not about and a case posting several says both (M4, C12).
    """
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
    operation_id: UUID | None = None,
    from_installation: UUID | None = None,
    mutation_number: int = 0,
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


def _a_geometry_set_stating_there_is_none(
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    from_installation: UUID,
    mutation_number: int,
) -> JsonObject:
    """The catalog's geometry set stating that this feature holds no geometry (M9).

    A payload carrying null rather than a payload carrying nothing: the two are different
    statements and only this one reaches the stored column (ADR-0012 decision 3's addition of
    2026-09-09). The place the shared arranger builds is replaced whole rather than made optional
    there, because `at=None` in that file's own vocabulary reads as a caller with no interest in
    the field, which is the opposite of what this operation says.
    """
    return {
        **_a_geometry_set(
            party,
            layer_id=layer_id,
            feature_id=feature_id,
            at=A_PLACE_IN_THE_FIELD,
            from_installation=from_installation,
            mutation_number=mutation_number,
        ),
        "payload": {"geometry": None},
    }


def _drawing_a_feature_at(
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    at: tuple[float, float],
    from_installation: UUID,
    created: UUID | None = None,
    placed: UUID | None = None,
) -> tuple[JsonObject, JsonObject]:
    """The pair one drawing produces: the create, then the geometry that follows it (M9, C12).

    Numbered from the start of this installation's stream, because a case about what the projection
    ends up holding is not a case about the numbering, while the place stays in the caller's hands
    because that is what every case here differs on.
    """
    return (
        _a_feature_create(
            party,
            layer_id=layer_id,
            feature_id=feature_id,
            operation_id=created,
            from_installation=from_installation,
            mutation_number=0,
        ),
        _a_geometry_set(
            party,
            layer_id=layer_id,
            feature_id=feature_id,
            at=at,
            operation_id=placed,
            from_installation=from_installation,
            mutation_number=1,
        ),
    )


def _as_the_storage_frame_holds_it(place: tuple[float, float]) -> Point:
    """A place as a geometry in the one frame storage declares (M5 rule 1)."""
    return Point(place[0], place[1], srid=STORAGE_FRAME_SRID)


def _a_wire_geometry_in_the_storage_frame(geometry: JsonObject) -> GEOSGeometry:
    """A wire geometry as the frame it was declared in holds it (M5 rule 1).

    The frame is assigned after parsing rather than passed to the constructor, and what Django
    measurement forces that order has one home, the comment on `_as_the_storage_column_takes_it`,
    which writes the same two lines. What is this reading's own is why the assignment is not
    optional here: dropped, it leaves a value that compares unequal to the same coordinates in the
    storage frame, because GEOS equality compares the frame as well as the coordinates, so every
    geometry assertion below would be comparing two frames rather than two places.
    """
    read = GEOSGeometry(json.dumps(geometry))
    read.srid = STORAGE_FRAME_SRID
    return read


def _the_features_the_projection_holds(party: Party) -> set[UUID]:
    """Every feature the current-state table holds for a tenant (M15, ADR-0012 decision 1)."""
    with tenant_scope(party.tenant_id):
        return set(Feature.objects.values_list("id", flat=True))


def _the_geometry_the_projection_holds(party: Party, feature_id: UUID) -> GEOSGeometry | None:
    """The current geometry of one feature, which is the state the application reads (M15)."""
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).geometry


@dataclass(frozen=True, slots=True)
class AProjectedFeature:
    """One projected row in the four columns a write reaching it could move it through.

    Three of them are the update set of ADR-0012 decision 3 and the fourth is what the wall reads
    on (ADR-0005 section 3), so a row compared whole here is a row nothing touched.
    """

    tenant_id: UUID
    project_id: UUID
    layer_id: UUID
    geometry: GEOSGeometry | None


def _the_feature_the_projection_holds(party: Party, feature_id: UUID) -> AProjectedFeature:
    """One projected feature, read whole rather than column by column (M15, C4)."""
    with tenant_scope(party.tenant_id):
        held = Feature.objects.get(pk=feature_id)
        return AProjectedFeature(
            tenant_id=held.tenant_id,
            project_id=held.project_id,
            layer_id=held.layer_id,
            geometry=held.geometry,
        )


def _the_layer_the_projection_files(party: Party, feature_id: UUID) -> UUID:
    """The layer one projected feature belongs to (M2, M9)."""
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).layer_id


def _the_operations_the_log_holds(party: Party) -> set[UUID]:
    """Every operation the append-only log holds for a tenant (M15)."""
    with tenant_scope(party.tenant_id):
        return set(OperationLogEntry.objects.values_list("operation_id", flat=True))


def _the_chain_the_log_holds_for(party: Party, feature_id: UUID) -> list[JsonObject]:
    """One feature's operations as the client authored them, in the order the server recorded.

    Ordered by the per-project version, which is the axis the server allocates inside the flush
    transaction and therefore the only one that is server order rather than a client's claim
    (M10, ADR-0004 decision 2).
    """
    with tenant_scope(party.tenant_id):
        return [
            entry.client_half
            for entry in OperationLogEntry.objects.filter(
                client_half__target__feature_id=str(feature_id)
            ).order_by("project_version")
        ]


def _the_chain_the_reproducibility_clause_replays(
    party: Party, feature_id: UUID
) -> list[JsonObject]:
    """One feature's **applied** operations, in the order the server recorded (M15's Shape).

    Narrower than the reader above by exactly the sentence added 2026-09-17: the log holds a refused
    operation as well, and that operation is not part of the projection **nor of the replay the
    reproducibility clause runs**. The reader above consults no verdict, because what it answers is
    what the log holds, which is the retention half of the same sentence; a replay fed from it walks
    a geometry the server told the client it would not apply.
    """
    with tenant_scope(party.tenant_id):
        return [
            entry.client_half
            for entry in OperationLogEntry.objects.filter(
                client_half__target__feature_id=str(feature_id), **{THE_VERDICT: APPLIED}
            ).order_by("project_version")
        ]


def _the_identifiers_along(chain: Sequence[JsonObject]) -> list[UUID]:
    """One chain's operations by identifier, in the order the chain carries them (C12, M15)."""
    return [UUID(entry["operation_id"]) for entry in chain]


def _the_geometry_a_chain_replays_to(chain: Sequence[JsonObject]) -> GEOSGeometry | None:
    """The geometry an ordered chain of one feature's operations reproduces (M15).

    The last whole geometry the chain carries, rather than a fold over deltas: M9 forbids a vertex
    delta and makes a geometry operation carry the whole geometry, which is what makes a replay a
    latest-row-per-target-path read (ADR-0012 decision 1).

    A chain whose last geometry operation carried **null** replays to no geometry, which is a
    statement that chain makes rather than an absence in the reading of it (ADR-0012 decision 3's
    addition of 2026-09-09). The two are told apart by the index below, which raises on a chain
    that came back empty instead of answering the same nothing.
    """
    setting_a_geometry = [
        entry for entry in chain if entry["operation_type"] == THE_OPERATION_THAT_SETS_A_GEOMETRY
    ]
    spoken = setting_a_geometry[-1]["payload"]["geometry"]
    if spoken is None:
        return None
    return _a_wire_geometry_in_the_storage_frame(spoken)


def test_a_flush_lands_the_feature_its_operation_created_under_the_identifier_the_client_minted(
    alice: Party,
) -> None:
    """M15 with M3: the state the application reads is a projection of the log, so an operation
    that created a feature leaves that feature behind it rather than only a log row nobody can
    query. The identifier is the client's, minted offline before this flush existed, and the server
    neither allocates one nor rewrites the one it received.

    This is also the negative control every refusal below depends on: a route that refused every
    operation satisfies each of those and fails here."""
    layer_id, feature_id = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(_a_feature_create(alice, layer_id=layer_id, feature_id=feature_id)),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_features_the_projection_holds(alice) == {feature_id}


def test_a_projected_feature_is_filed_under_the_layer_its_target_named(alice: Party) -> None:
    """M9 with M2: a target carries its ancestors, so the layer a feature is filed under is the one
    the operation addressed and never one the server resolved for itself.

    **Two layers rather than one, and both in the project the batch addresses.** The composite
    reference only requires the layer to exist inside this tenant and this project, so with a single
    layer present an implementation filing every feature under whichever layer it found first is
    indistinguishable from one that read the target."""
    the_layer_addressed, another_layer_of_the_same_project = uuid4(), uuid4()
    feature_id = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=another_layer_of_the_same_project)
    _an_element_layer_of(alice, layer_id=the_layer_addressed)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(_a_feature_create(alice, layer_id=the_layer_addressed, feature_id=feature_id)),
        JSON,
    )

    assert _the_layer_the_projection_files(alice, feature_id) == the_layer_addressed


def test_a_batch_that_creates_a_feature_and_sets_its_geometry_leaves_that_geometry_in_the_state(
    alice: Party,
) -> None:
    """M15 with M9 and M5 rule 1: the ordinary shape of a flush is more than one operation reaching
    one feature, and what the projection holds afterwards is the geometry the batch set, in the
    frame storage declares.

    **The row is per feature while the target path is finer**, so this batch is exactly the shape
    ADR-0012 decision 4 hands over as measured: one statement affecting a row twice raises an
    `ON CONFLICT DO UPDATE` cardinality violation, folding by target path does not avoid it, and
    folding by feature is what the statement needs. An implementation that folds by the wrong key
    does not answer with a wrong geometry here, it fails to answer at all.

    The frame is asserted by comparing whole geometries, because GEOS equality compares the frame
    beside the coordinates: a geometry stored in the frame GeoJSON is read in is not equal to the
    same place in EPSG:4674."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    response = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )

    assert response.status_code == HTTPStatus.OK
    assert _the_geometry_the_projection_holds(alice, feature_id) == _as_the_storage_frame_holds_it(
        A_PLACE_IN_THE_FIELD
    )


def test_the_projection_holds_the_last_geometry_a_batch_set_rather_than_the_first(
    alice: Party,
) -> None:
    """M15: the projection is the **current** state and never the history, and the order that
    decides which of a batch's writes is current is the one the server recorded, which is the list
    order a flush stamps its per-project versions in (M10, ADR-0004 decision 2).

    Distinct from the case above rather than a longer arrangement of it: an implementation that
    folds a batch by feature and keeps whichever row the fold met first passes that one and leaves
    this feature at the place it was moved away from, which for a legal-weight boundary is the whole
    of what M15 exists to make impossible."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            ),
            _a_geometry_set(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == _as_the_storage_frame_holds_it(
        ANOTHER_PLACE_IN_THE_FIELD
    )


def test_a_later_flush_replaces_the_geometry_an_earlier_flush_left(alice: Party) -> None:
    """M15: the projection carries the current state across flushes and not only within one, so the
    second flush moves the feature rather than being dropped for arriving second.

    The third mechanism of the three geometry cases, and the one the other two are blind to: an
    upsert that inserts and does nothing on conflict folds a single batch correctly and then never
    moves a feature again, which is a projection that silently stops tracking the log the moment a
    feature is edited twice."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )
    browser.post(
        OPERATIONS_PATH,
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
        JSON,
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == _as_the_storage_frame_holds_it(
        ANOTHER_PLACE_IN_THE_FIELD
    )


def test_a_create_for_a_feature_that_already_exists_leaves_the_stored_geometry_it_says_nothing_of(
    alice: Party,
) -> None:
    """ADR-0012 decision 3's addition of 2026-09-09, on the arm that was found as a defect: a
    create's payload carries nothing beyond the address it creates (M9), so it makes no statement
    about the geometry at all, and a write that carried that silence into its update set cleared a
    surveyed point while answering the client that the flush was applied.

    **Across two flushes rather than inside one**, which is why the defect survived a green suite:
    a create following a geometry set within one batch is folded per feature and already leaves the
    geometry alone, so the only reachable loss is a projection row an earlier flush left behind.

    **The shape is one the canon requires the route to accept rather than one this case invents.**
    PRD T2.3's acceptance, addition of 2026-08-11, has an operation the server already holds,
    resent above the cursor, answered as applied rather than refused; whether a re-create is
    legitimate at all is MAP-68's and is not decided here."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )
    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == _as_the_storage_frame_holds_it(
        A_PLACE_IN_THE_FIELD
    )


def test_a_create_for_a_feature_that_already_exists_files_it_under_the_layer_it_names(
    alice: Party,
) -> None:
    """ADR-0012 decision 3's addition of 2026-09-09, on the opposite mistake in the same place: a
    column an operation **did** speak of moves, and a write that left the container of a conflicting
    row as it found it logged the new layer while the projection went on filing the feature under
    the old one (M2, M9).

    **Two layers of one project**, because the composite reference only asks that the layer exist
    in the project the batch addresses, so a feature that never moves is indistinguishable from one
    refiled correctly where there is a single layer to name."""
    the_layer_it_was_drawn_in, the_layer_it_is_moved_to = uuid4(), uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=the_layer_it_was_drawn_in)
    _an_element_layer_of(alice, layer_id=the_layer_it_is_moved_to)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=the_layer_it_was_drawn_in,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )
    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_is_moved_to,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert _the_layer_the_projection_files(alice, feature_id) == the_layer_it_is_moved_to


def test_a_resent_batch_the_cursor_had_already_seen_does_not_move_the_geometry_back(
    alice: Party,
) -> None:
    """C12 with T2.3, met on the state rather than on the log: a resend is what the idempotency
    contract exists to make safe, so an operation at or below this installation's cursor is
    deduplicated and the projection is not written from it.

    **The direction is what makes this observable at all.** A resend of the same operations is
    indistinguishable from applying them twice while the state they produce is the same, so the
    queue resent here is the older one, whose geometry the later flush has already moved away from.
    An implementation that projects the batch it received rather than the operations above the
    cursor answers this flush correctly, appends nothing, and quietly returns the feature to where
    it was before the last edit.

    **The chain is asserted beside the geometry because it is the control the geometry needs.** A
    projection left where it already was is what a working dedup produces and also what a resend
    the server never reached produces, so the log naming its three operations once each, in the
    order the server recorded, is what says the resend arrived and was deduplicated rather than
    refused or lost."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    created, geometry_first_set, moved_away = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)
    the_queue_that_was_applied = _a_queue_of(
        *_drawing_a_feature_at(
            alice,
            layer_id=layer_id,
            feature_id=feature_id,
            at=A_PLACE_IN_THE_FIELD,
            from_installation=installation,
            created=created,
            placed=geometry_first_set,
        )
    )

    browser.post(OPERATIONS_PATH, the_queue_that_was_applied, JSON)
    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                operation_id=moved_away,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )
    resent = browser.post(OPERATIONS_PATH, the_queue_that_was_applied, JSON)

    assert resent.status_code == HTTPStatus.OK
    assert _the_identifiers_along(_the_chain_the_log_holds_for(alice, feature_id)) == [
        created,
        geometry_first_set,
        moved_away,
    ]
    assert _the_geometry_the_projection_holds(alice, feature_id) == _as_the_storage_frame_holds_it(
        ANOTHER_PLACE_IN_THE_FIELD
    )


def test_an_operation_addressing_a_layer_this_project_lacks_is_refused_by_a_typed_verdict(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-08, which is where this refusal is created and the
    only place it exists: nothing in the PRD carries it, because nothing in the PRD anticipated a
    constraint that only becomes reachable once the projection is written.

    **Typed or a crash, with no third state, and that is the subject this case keeps.** The
    composite reference `feature_layer_within_the_same_tenant_and_project` is consulted the moment a
    projection row is written, so an unknown layer raises, and an `IntegrityError` escaping as a
    `500` is a decision nobody took, which N9 and N12 both refuse.

    **What moved is where the typed answer lands, and the name says so.** This refusal was a
    whole-batch `409` until ADR-0014 decision 2, which takes it out of that set because it fails the
    criterion of decision 1 in every clause: the stream is contiguous, the cursor is intact, and
    resending reproduces it forever, so the client's next act does not exist on the wire. It is a
    verdict on the operation now, carried in a `200` body.

    The whole body is compared rather than one key of it, because ADR-0010 decision 6 closes this
    object exactly as it closed the one this case used to read. The echo counts what the server
    **decided**, so it names this operation even though nothing was applied (ADR-0014 decision 5,
    foundation v0.19)."""
    browser = a_browser(authenticated_as=alice.user_id)

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(_a_feature_create(alice, layer_id=uuid4(), feature_id=uuid4())),
        JSON,
    )

    assert refused.status_code == HTTPStatus.OK
    assert refused.json() == {
        THE_ECHO: 0,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        ],
    }


def test_a_layer_of_another_project_is_refused_exactly_as_one_that_never_existed(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-08, on the clause that fixes the container the
    reason names: the spelling names tenant and project together because that is what the
    constraint spans, so a layer this tenant holds in a **different** project is as absent here as
    one that exists nowhere.

    A layer of another tenant is not the third arm of this case: inside the wall it is invisible by
    construction, which is the same silence the project claim's refusal already relies on. What can
    tempt an implementation into a second answer is the layer it **can** see, and that is the one
    arranged here.

    **The refusal list is the positive control, and it replaces the status because the status
    stopped being one.** While this refusal was a `409` (ADR-0010 decision 6's addition of
    2026-09-08), a route that consulted no layer answered `200` to both requests and the comparison
    alone was green against it; now that the verdict rides in a `200` body (ADR-0014 decision 2) the
    status no longer tells the two apart at all, and what does is that the first request was
    actually refused for the reason this case is about.

    Each request is its own installation's first operation, which the shared arranger's default
    mints, so the second is not deduplicated against a cursor the first one moved (M10,
    ADR-0014 decision 5)."""
    a_layer_of_another_project = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(
        alice, layer_id=a_layer_of_another_project, project_id=second_project_of(alice)
    )

    on_a_layer_of_another_project = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(alice, layer_id=a_layer_of_another_project, feature_id=uuid4())
        ),
        JSON,
    )
    on_a_layer_that_never_existed = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(_a_feature_create(alice, layer_id=uuid4(), feature_id=uuid4())),
        JSON,
    )

    assert on_a_layer_of_another_project.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: NO_LAYER_IN_THIS_PROJECT}
    ]
    assert (on_a_layer_of_another_project.status_code, on_a_layer_of_another_project.content) == (
        on_a_layer_that_never_existed.status_code,
        on_a_layer_that_never_existed.content,
    )


def test_the_operation_naming_an_absent_layer_first_is_refused_though_the_fold_loses_that_layer(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 on the **guard** rather than on the write: the set a verdict is decided
    over is the operations, never the state they fold to. That fold is one row per feature and is
    lawfully lossy, keeping the last address each feature was given, so a check fed from its output
    inherits every loss as a blind spot, which is why `the_layers_this_batch_addresses` reads the
    operations and says so in its own docstring.

    **One feature and two operations, the absent layer named first**, which is the only shape that
    tells the two readings apart: the refusal cases beside this one each give the absent layer a
    feature of its own, where it survives any fold and the guard answers alike either way. Here the
    second operation replaces the address the fold keeps, so a guard reading the folded state never
    sees the absent layer at all, nothing is refused, and the row lands under the layer this project
    does hold with no `IntegrityError` to raise the alarm (M2, M9).

    **The second operation is a create rather than the geometry set this case carried while the
    refusal was whole-batch**, and that is forced rather than preferred. Once the first operation
    earns a verdict of its own (ADR-0014 decision 1) the batch around it applies, so a geometry set
    here would be one for a feature no applied operation ever created: the shape this module's own
    docstring says nothing arranges, and the one ADR-0014 decision 7 explicitly declines to decide.
    A create keeps the fold identical, the absent layer first and the held one last, while leaving
    every operation of the batch decidable.

    **The whole body is compared**, which the retired form could not do: it asserted that a refusal
    was reached at all, since a status alone would not say which of three mechanisms refused, and
    the list now names the refused operation by its own mutation number and says in the same breath
    that the one behind it was not refused (ADR-0014 decisions 6 and 7)."""
    a_layer_that_never_existed, the_layer_its_feature_ends_under = uuid4(), uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=the_layer_its_feature_ends_under)

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_that_never_existed,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_feature_create(
                alice,
                layer_id=the_layer_its_feature_ends_under,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 1,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        ],
    }


def test_a_batch_carrying_an_unknown_layer_keeps_both_its_operations_on_the_log(
    alice: Party,
) -> None:
    """**This case says the opposite of what it said, and the name is where a reader is told so.**
    Its subject is unchanged, what the log holds after a batch one of whose operations the server
    will not apply, and the answer inverted at ADR-0014 decision 3: the refused operation is
    *retained*, on the same append-only log, written exactly as an applied one is with the client
    half verbatim (M8). Until that decision the whole batch was refused and the log held nothing.

    **The retention is the departure the product exists to make** and it is what T5.2 and M9 mean by
    flagged, not applied, not dropped: the geometry was drawn in the field, and every system this
    decision was researched against keeps an error message and discards the work (C7).

    **The batch carries a good operation beside the refused one**, so what is asserted is that both
    halves of a mixed batch reach the log, rather than a refusal that took the batch down with it or
    an application that kept only what it applied.

    **What the accepted flush before it buys changed with the answer, so it is restated rather than
    carried over.** It used to be the control that told an empty log apart from a refused one; the
    assertion is a presence now, so an absent write is red on its own. What it buys instead is the
    property one batch cannot show: an operation an earlier flush applied is still on the log after
    a later batch was partly refused, so a refusal truncates nothing behind it (M15, C7)."""
    layer_id, installation = uuid4(), uuid4()
    accepted, alongside_the_unknown_layer, addressing_the_unknown_layer = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                operation_id=accepted,
                from_installation=installation,
                mutation_number=0,
            )
        ),
        JSON,
    )
    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                operation_id=alongside_the_unknown_layer,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=uuid4(),
                feature_id=uuid4(),
                operation_id=addressing_the_unknown_layer,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert _the_operations_the_log_holds(alice) == {
        accepted,
        alongside_the_unknown_layer,
        addressing_the_unknown_layer,
    }


def test_only_the_features_of_the_operations_a_flush_applied_reach_the_projection(
    alice: Party,
) -> None:
    """**This case says the opposite of what it said, and the name is where a reader is told so.**
    Its subject is unchanged, what the projection holds after a batch one of whose operations the
    server will not apply, and the answer inverted at ADR-0014 decision 1: the operation beside the
    refused one is applied and its feature is current state. Until that decision the batch was
    refused whole and the projection held nothing of it.

    **What did not invert is the half this case now carries alone**, and it is ADR-0012 decision 3
    as narrowed the same day: the fold walks the operations the flush **applied**, so a refused
    operation's feature never reaches the current state at all. The set is compared whole, so this
    is one read answering both halves rather than two assertions.

    **What the accepted flush before it buys changed with the answer, so it is restated rather than
    carried over.** It used to be what made an empty projection mean anything; the assertion names
    two features now, so a fold that never ran is red on its own. What it buys instead is the
    property one batch cannot show: a feature an earlier flush projected survives a later batch the
    server partly refused, so a refusal unwinds nothing behind it (M15, C7)."""
    layer_id, installation = uuid4(), uuid4()
    accepted, alongside_the_unknown_layer = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=accepted,
                from_installation=installation,
                mutation_number=0,
            )
        ),
        JSON,
    )
    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=alongside_the_unknown_layer,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=uuid4(),
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert _the_features_the_projection_holds(alice) == {accepted, alongside_the_unknown_layer}


def test_replaying_a_features_chain_in_server_order_reproduces_the_geometry_the_projection_holds(
    alice: Party,
) -> None:
    """M15's reproducibility clause, at the **mechanism** its two other qualifiers have no runtime
    for: the clause is about a **legal-weight** feature's **attributed** chain, and neither model
    carries a legal-weight marker (M7 puts it on the layer, and its content is OQ-8) while the log
    carries neither the authoritative applied-at (MAP-53) nor the normalized author (MAP-37). What
    is proven here is that replaying one feature's ordered chain from the log reproduces the
    geometry the projection holds, which is the half that has a runtime today.

    **The replay is asserted against a literal first, and that assertion is not decoration.** A
    chain read back empty replays to nothing and a projection nobody wrote holds nothing, and
    nothing equals nothing: without the literal this case is green against a server that neither
    appends nor projects. The literal also carries the order, because the place asserted is the one
    the **second** flush set.

    Two flushes rather than one, so the chain crosses two allocations of the per-project version and
    the order asserted is the server's rather than one batch's list."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )
    browser.post(
        OPERATIONS_PATH,
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
        JSON,
    )

    replayed = _the_geometry_a_chain_replays_to(_the_chain_the_log_holds_for(alice, feature_id))

    assert replayed == _as_the_storage_frame_holds_it(ANOTHER_PLACE_IN_THE_FIELD)
    assert _the_geometry_the_projection_holds(alice, feature_id) == replayed


def test_the_projection_a_geometry_set_carrying_none_leaves_is_what_that_chain_replays_to(
    alice: Party,
) -> None:
    """M15's reproducibility mechanism at the statement the case above cannot make: a
    `feature.geometry.set` whose payload carries **null** states that this feature has no geometry,
    which ADR-0012 decision 3's addition of 2026-09-09 distinguishes from a create saying nothing at
    all, and only one of those two reaches the stored column.

    **The place set before it is what makes the emptying observable.** A column that was already
    null is left null both by an implementation that reads the statement and by one that ignores it,
    so the feature is surveyed first and emptied second, and the projection's answer then tells the
    two apart.

    **Neither side of the comparison may reach nothing by absence.** The row is read by identifier,
    so a projection that dropped the feature raises rather than answering the emptiness this case is
    about; and the replay indexes the chain's last geometry operation, so a chain read back empty
    raises rather than agreeing."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )
    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set_stating_there_is_none(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    replayed = _the_geometry_a_chain_replays_to(_the_chain_the_log_holds_for(alice, feature_id))

    assert replayed is None
    assert _the_geometry_the_projection_holds(alice, feature_id) == replayed


def test_the_replay_a_refused_geometry_is_left_out_of_still_reproduces_what_the_projection_holds(
    alice: Party,
) -> None:
    """M15's Shape as added 2026-09-17, at the half its own sentence puts **beside** the projection:
    a refused operation is a log entry as well, and it is not part of the projection *nor of the
    replay the reproducibility clause runs*.

    **The second half is reachable on its own, which is why it needs a case rather than a reading.**
    Retention and exclusion are one sentence in the document and two behaviours in the code: the
    server can keep the refused operation exactly as ADR-0014 decision 3 requires, withhold it from
    the fold exactly as ADR-0012 decision 3's narrowing requires, and still leave the chain that
    replays it indistinguishable from the chain that was applied. M15's reproducibility clause is
    then false of every feature a refusal ever touched, and the log stops being the evidence the
    whole requirement exists to make it.

    **The refused geometry moves the feature somewhere else**, because a refusal replaying to the
    place it was refused from is an arrangement that cannot fail: the two places have to differ for
    the replay and the projection to be able to disagree at all.

    **The refusal list is asserted first and it is the control rather than a second subject.** A
    route that stopped refusing this operation applies it, and then the replay and the projection
    agree on the wrong place instead of disagreeing, which is a red this case should reach by saying
    what happened rather than by a geometry comparison a reader has to reconstruct.

    The literal is asserted before the projection on this module's own ground: a chain read back
    empty replays to nothing and a projection nobody wrote holds nothing, and nothing equals
    nothing."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_of(alice, layer_id=layer_id)
    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
            )
        ),
        JSON,
    )

    moved_on_a_layer_this_project_lacks = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set(
                alice,
                layer_id=a_layer_this_project_lacks(),
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    replayed = _the_geometry_a_chain_replays_to(
        _the_chain_the_reproducibility_clause_replays(alice, feature_id)
    )

    assert moved_on_a_layer_this_project_lacks.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 2, THE_REASON: NO_LAYER_IN_THIS_PROJECT}
    ]
    assert replayed == _as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD)
    assert _the_geometry_the_projection_holds(alice, feature_id) == replayed


def test_a_feature_identifier_another_tenant_holds_is_answered_exactly_as_a_fresh_one(
    alice: Party, bob: Party
) -> None:
    """T6.5's cross-tenant half, on the one column of this table that is a **global** key: the
    feature identifier is minted by the client that draws the feature offline (M3, ADR-0006), so two
    tenants can mint the same one, and the second must not learn from its answer that the first
    exists.

    **The comparison is over the status and the body together**, which is the testable form
    ADR-0010 decision 6's addition of 2026-08-07 fixes for this question: a body naming the reason
    leaks the row while the status line still reads like every other applied flush.

    **The flush on a fresh identifier is the positive control and it is load-bearing.** A route that
    refused both requests answers them alike, so without an accepted flush beside it the comparison
    is green against a server that stopped applying anything at all.

    **Two installations rather than one stream of two**, so both requests are the same shape: one
    operation opening a stream against no cursor, whose acknowledgement carries the same number, and
    a difference between the bodies is then the leak rather than the axis (M4, C12)."""
    the_identifier_alice_holds = uuid4()
    alices_layer, bobs_layer = uuid4(), uuid4()
    _an_element_layer_of(alice, layer_id=alices_layer)
    _an_element_layer_of(bob, layer_id=bobs_layer)
    a_browser(authenticated_as=alice.user_id).post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(alice, layer_id=alices_layer, feature_id=the_identifier_alice_holds)
        ),
        JSON,
    )

    bobs_browser = a_browser(authenticated_as=bob.user_id)
    on_the_identifier_alice_holds = bobs_browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                bob,
                layer_id=bobs_layer,
                feature_id=the_identifier_alice_holds,
                from_installation=uuid4(),
            )
        ),
        JSON,
    )
    on_an_identifier_nobody_holds = bobs_browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                bob, layer_id=bobs_layer, feature_id=uuid4(), from_installation=uuid4()
            )
        ),
        JSON,
    )

    assert on_an_identifier_nobody_holds.status_code == HTTPStatus.OK
    assert (on_the_identifier_alice_holds.status_code, on_the_identifier_alice_holds.content) == (
        on_an_identifier_nobody_holds.status_code,
        on_an_identifier_nobody_holds.content,
    )


def test_the_feature_a_colliding_identifier_reaches_is_left_to_the_tenant_that_holds_it(
    alice: Party, bob: Party
) -> None:
    """C4 with T6.5: the answer above is indistinguishable, and this is the half of that sentence
    the answer cannot show. A write that moved Alice's feature into Bob's project, refiled it under
    Bob's layer or cleared the point she surveyed answers Bob exactly as a fresh identifier does, so
    the case above passes over a row that was overwritten.

    **All four columns rather than the geometry alone**, because three of them are the update set of
    ADR-0012 decision 3 and the fourth is what the wall reads on (ADR-0005 section 3), so a row
    compared whole is a row nothing reached.

    **Bob draws rather than only creates, and that is what puts the geometry at risk.** A create
    makes no statement about the geometry (that decision's addition of 2026-09-09), so a write that
    overwrote everything else would still leave Alice's point where it was and the column would be
    green for a reason this case is not about. He surveys the other place, so all four columns of
    his row differ from all four of hers."""
    the_identifier_both_tenants_mint = uuid4()
    alices_layer, bobs_layer = uuid4(), uuid4()
    _an_element_layer_of(alice, layer_id=alices_layer)
    _an_element_layer_of(bob, layer_id=bobs_layer)
    a_browser(authenticated_as=alice.user_id).post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                alice,
                layer_id=alices_layer,
                feature_id=the_identifier_both_tenants_mint,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=uuid4(),
            )
        ),
        JSON,
    )

    a_browser(authenticated_as=bob.user_id).post(
        OPERATIONS_PATH,
        _a_queue_of(
            *_drawing_a_feature_at(
                bob,
                layer_id=bobs_layer,
                feature_id=the_identifier_both_tenants_mint,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=uuid4(),
            )
        ),
        JSON,
    )

    assert _the_feature_the_projection_holds(
        alice, the_identifier_both_tenants_mint
    ) == AProjectedFeature(
        tenant_id=alice.tenant_id,
        project_id=alice.project_id,
        layer_id=alices_layer,
        geometry=_as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD),
    )


def test_the_log_keeps_the_operation_whose_feature_the_projection_could_not_take(
    alice: Party, bob: Party
) -> None:
    """M15 at the one place the log and its projection are allowed to disagree, and the disagreement
    sits inside Bob's own tenant rather than across the wall: the operation he authored is his and
    is appended, while the row it would have produced carries an identifier another tenant already
    holds and is left to that tenant (T6.5, C4).

    **The operation beside it is what makes both halves say anything.** A projection holding one
    feature rather than none says this flush was applied rather than refused, and a log holding two
    operations rather than one says the colliding operation was appended rather than dropped."""
    the_identifier_alice_holds, bobs_own_feature = uuid4(), uuid4()
    alices_layer, bobs_layer, installation = uuid4(), uuid4(), uuid4()
    drawn_by_bob, colliding_with_alice = uuid4(), uuid4()
    _an_element_layer_of(alice, layer_id=alices_layer)
    _an_element_layer_of(bob, layer_id=bobs_layer)
    a_browser(authenticated_as=alice.user_id).post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(alice, layer_id=alices_layer, feature_id=the_identifier_alice_holds)
        ),
        JSON,
    )

    a_browser(authenticated_as=bob.user_id).post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                bob,
                layer_id=bobs_layer,
                feature_id=bobs_own_feature,
                operation_id=drawn_by_bob,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_feature_create(
                bob,
                layer_id=bobs_layer,
                feature_id=the_identifier_alice_holds,
                operation_id=colliding_with_alice,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert _the_operations_the_log_holds(bob) == {drawn_by_bob, colliding_with_alice}
    assert _the_features_the_projection_holds(bob) == {bobs_own_feature}
