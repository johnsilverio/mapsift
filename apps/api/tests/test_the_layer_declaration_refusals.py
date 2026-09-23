"""An operation its layer's declarations reject is refused on its own, kept, and passed.

Trace: PRD **M2**, the server's half of its served-versus-element clause and of its geometry-family
clause, split as the Acceptance block of `specs/tasks/MAP-66-layer-declaration-refusals.md` records;
PRD **M9**'s final acceptance clause, whole, whose *flagged* is the verdict `refused` (ADR-0014
decision 4); **ADR-0010 decision 6's addition of 2026-09-23** for the two reason values; **ADR-0014
decisions 1, 3, 5, 6 and 7** for the verdict each reason joins; **ADR-0012 decision 3** as narrowed
2026-09-17 for the projection a refusal stands in front of; ADR-0005 sections 3 and 4 for the
binding every read and write here happens inside. I1, I2, I9; C1, C7, C12.

**Here rather than under either package, on the gate ADR-0007 section 6 keeps this directory for.**
What a layer declares is `layers`' and the verdict is written on `sync`'s log, and the cases that
prove a refusal withheld its operation from the current state read both. The order that picks one
reason and the scope of the family check are decisions over plain data, and the cases the route
cannot carry for them are in `mapsift/sync/tests/test_the_reason_an_operation_is_refused_for.py`.

**Everything goes through the route and never through the writer**, on the ground the flush modules
already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only transaction
is its own context manager is green against an implementation that has none. **Every read forces
its rows inside the binding that authorised it**, because a queryset evaluated after the block
closes is answered by the policy with zero rows and no exception.

What is deliberately not here, each with the issue that owns it: the client's queue and its
optimistic preview of a refused operation (**MAP-15**, **MAP-16**); the element budget and the
import classification (M2's other clauses, which nothing reaches); a feature changing path (OQ-6
and M2's fourth clause); every geometry payload the writer cannot take (**MAP-70**, **MAP-69**,
**MAP-33**), so each payload below is one GEOS and the column already take; a create addressing a
feature that already exists (**MAP-68**); and the record each refusal leaves in the decision trail,
which is `mapsift/sync/tests/test_the_flush_decision_trail.py`'s. **One shape nothing here
arranges**, on the convention the projection module states: a geometry set for a feature no applied
operation created, which ADR-0014 decision 7 leaves open, so every geometry follows a create for its
own feature that the flush applies.
"""

from dataclasses import dataclass
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import GEOSGeometry, LineString, MultiPoint, Point, Polygon
from django.test import Client

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
    an_operation_on_a_layer_this_project_lacks,
)
from mapsift.common.binding import tenant_scope
from mapsift.layers.models import Feature
from mapsift.layers.rules import GeometryKind, StorageClass
from mapsift.layers.services import create_layer
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# M5 rule 1: SIRGAS 2000, the one frame stored geometry is in.
STORAGE_FRAME_SRID = 4674

# The success body as ADR-0010 decision 6's addition of 2026-09-17 closes it, and the three members
# of its refusal set this module reads, the two it adds and the one they are ordered behind (its
# addition of 2026-09-23). Literals rather than reads off the enums that carry them, because a case
# comparing an enum against itself cannot notice a member being renamed.
THE_ECHO = "last_decided_mutation_number"
THE_REFUSALS = "refused"
THE_MUTATION_NUMBER_REFUSED = "mutation_number"
THE_REASON = "reason"
NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"
SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY = "geometry_outside_the_layers_family"

# The member of the envelope's closed verdict set a refusal is stored under (ADR-0014 decisions 3
# and 4), spelled as the module that owns that contract spells it.
REFUSED = "refused"

# Two places a field client surveys, far enough apart in both coordinates that a geometry stored
# with its axes swapped is equal to neither.
A_PLACE_IN_THE_FIELD = (-47.6, -15.9)
ANOTHER_PLACE_IN_THE_FIELD = (-47.5, -15.4)

# A parcel's boundary counterclockwise and an enclave inside it clockwise, which is the winding
# GeoJSON states for an exterior ring and its hole. Written out as wire coordinates and again as the
# geometry a case expects storage to hold, rather than one computed from the other, so the
# expectation comes from the literal and never from the reading under test.
THE_PARCELS_BOUNDARY = (
    (-47.6, -15.9),
    (-47.5, -15.9),
    (-47.5, -15.8),
    (-47.6, -15.8),
    (-47.6, -15.9),
)
THE_ENCLAVE_INSIDE_IT = (
    (-47.58, -15.88),
    (-47.58, -15.86),
    (-47.56, -15.86),
    (-47.56, -15.88),
    (-47.58, -15.88),
)

A_POINT_SURVEYED_IN_THE_FIELD: JsonObject = {"type": "Point", "coordinates": [-47.6, -15.9]}
A_LINE_SURVEYED_IN_THE_FIELD: JsonObject = {
    "type": "LineString",
    "coordinates": [[-47.6, -15.9], [-47.5, -15.4]],
}
TWO_POINTS_SURVEYED_IN_THE_FIELD: JsonObject = {
    "type": "MultiPoint",
    "coordinates": [[-47.6, -15.9], [-47.5, -15.4]],
}
A_PARCEL: JsonObject = {
    "type": "Polygon",
    "coordinates": [
        [[-47.6, -15.9], [-47.5, -15.9], [-47.5, -15.8], [-47.6, -15.8], [-47.6, -15.9]]
    ],
}
A_PARCEL_WITH_AN_ENCLAVE: JsonObject = {
    "type": "Polygon",
    "coordinates": [
        [[-47.6, -15.9], [-47.5, -15.9], [-47.5, -15.8], [-47.6, -15.8], [-47.6, -15.9]],
        [[-47.58, -15.88], [-47.58, -15.86], [-47.56, -15.86], [-47.56, -15.88], [-47.58, -15.88]],
    ],
}


def _a_layer_of(
    party: Party,
    *,
    layer_id: UUID,
    geometry_kind: GeometryKind,
    storage_class: StorageClass,
) -> None:
    """One layer in this party's project, declaring the family and the class a case varies (M2).

    Neither declaration carries a default: this module is about what a layer declares, so a case
    that did not state both would be arranging its subject where a reader cannot see it.
    """
    with tenant_scope(party.tenant_id):
        create_layer(
            layer_id=layer_id,
            tenant_id=party.tenant_id,
            project_id=party.project_id,
            name="vegetation cover",
            geometry_kind=geometry_kind,
            storage_class=storage_class,
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
    """The catalog's create, addressed at one layer and one feature of this party's project.

    The installation and the mutation number carry no default, because every verdict here is read
    off a stream a case numbers itself, and a minted installation per operation is a batch the
    composition rules refuse before any layer is read (ADR-0010 decision 6).
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


def _a_geometry_set_carrying(
    geometry: JsonObject | None,
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    from_installation: UUID,
    mutation_number: int,
    operation_id: UUID | None = None,
) -> JsonObject:
    """The catalog's geometry set, carrying whichever whole geometry a case is about (M9).

    The payload is replaced whole rather than made a parameter of the shared arranger, the shape the
    projection module uses for the payload it states outright: the shared one carries a point on
    purpose, and every case here that varies the family varies what that default holds still.
    """
    return {
        **a_geometry_set_claiming(
            party.tenant_id,
            operation_id=operation_id,
            client_id=from_installation,
            mutation_number=mutation_number,
            project_id=party.project_id,
            layer_id=layer_id,
            feature_id=feature_id,
        ),
        "payload": {"geometry": geometry},
    }


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The reason the flush modules give: an arrange step that quietly starts being refused leaves the
    assertions standing and the case vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _the_features_the_projection_holds(party: Party) -> set[UUID]:
    """Every feature the current-state table holds for a tenant (M15, ADR-0012 decision 1)."""
    with tenant_scope(party.tenant_id):
        return set(Feature.objects.values_list("id", flat=True))


def _the_geometry_the_projection_holds(party: Party, feature_id: UUID) -> GEOSGeometry | None:
    """The current geometry of one feature, which is the state the application reads (M15).

    Read by identifier, so a projection that never wrote the row raises rather than answering the
    same nothing a stored null would.
    """
    with tenant_scope(party.tenant_id):
        return Feature.objects.get(pk=feature_id).geometry


@dataclass(frozen=True, slots=True)
class WhatTheLogKeeps:
    """One log entry as M9's *flagged and retained* reads it: the server's decision beside the
    operation exactly as its client authored it (ADR-0014 decision 3, M8)."""

    verdict: str
    refusal_reason: str | None
    client_half: ClientHalf


def _what_the_log_keeps_of(party: Party, operation_id: UUID) -> WhatTheLogKeeps:
    """The one entry the log holds for an operation, read whole (M15, ADR-0014 decision 3).

    `get` rather than the first of however many there are, so an operation appended twice raises
    here instead of answering with whichever row came back first, and so does one never appended.
    The client half comes back through the generated reader, because a comparison field by field
    pins the fields somebody remembered.
    """
    with tenant_scope(party.tenant_id):
        entry = OperationLogEntry.objects.get(operation_id=operation_id)
        return WhatTheLogKeeps(
            verdict=entry.verdict,
            refusal_reason=entry.refusal_reason,
            client_half=ClientHalf.model_validate(entry.client_half),
        )


def test_an_operation_naming_a_served_layer_is_refused_by_a_typed_verdict(alice: Party) -> None:
    """M2's served-versus-element clause, the server's half: the storage class is a property of the
    layer and it decides the path the layer's features take, so an operation naming a served layer
    is refused rather than applied as though the frontier did not exist. ADR-0010 decision 6's
    addition of 2026-09-23 names the reason and ADR-0014 decision 2 makes it an operation verdict.

    **The whole body is compared**, because ADR-0010 decision 6 closes this object, and the echo
    counts what the server **decided**, so it names this operation though nothing was applied
    (ADR-0014 decision 5). MAP-66's task spec records that this refusal was first built as a
    whole-batch `409`, the shape ADR-0014 decision 1 retires."""
    a_served_layer, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=0,
            )
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.OK
    assert refused.json() == {
        THE_ECHO: 0,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: SERVED_LAYER_TAKES_NO_OPERATIONS}
        ],
    }


def test_a_served_layers_feature_never_becomes_current_state_while_an_element_layers_beside_it_does(
    alice: Party,
) -> None:
    """M2's served-versus-element clause on both of its arms, which is the only reading that says
    anything: an implementation refusing every operation satisfies the first and fails the second.

    **The server's half of that clause is the current state, not the log**, which is the reading
    MAP-66's task spec settles in its Acceptance block: *never appears in the operation queue* read
    as *the log never holds it* is retired there, because ADR-0014 decision 3 keeps every refused
    operation on that log. The queue itself is the client's (PRD T1.2) and has no runtime here.

    **One element-layer feature on each side of the served one**, so a flush refused from the
    first bad operation onward, which leaves the earlier feature standing, is as red as one refused
    whole (ADR-0014 decisions 1 and 7)."""
    an_element_layer, a_served_layer, installation = uuid4(), uuid4(), uuid4()
    drawn_before, on_the_served_layer, drawn_after = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=an_element_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=an_element_layer,
                feature_id=drawn_before,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=on_the_served_layer,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=an_element_layer,
                feature_id=drawn_after,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert _the_features_the_projection_holds(alice) == {drawn_before, drawn_after}


def test_the_operation_naming_a_served_layer_first_is_refused_though_the_fold_loses_that_layer(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 on the **guard** rather than on the write, the MAP-65 trap carried to the
    storage class: a verdict is decided over the operations and never over the state they fold to,
    because that fold keeps one row per feature and the last address each feature was given.

    **One feature and two creates, the served layer named first**, which is the only shape that
    tells the two readings apart: the fold files the feature under the element layer, so a guard
    reading it never sees the served one and refuses nothing. Two creates rather than a create and a
    geometry set, because once the first operation earns its own verdict the batch around it
    applies, and a geometry set there would address a feature no applied operation created
    (ADR-0014 decision 7)."""
    a_served_layer, an_element_layer = uuid4(), uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )
    _a_layer_of(
        alice,
        layer_id=an_element_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_feature_create(
                alice,
                layer_id=an_element_layer,
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
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: SERVED_LAYER_TAKES_NO_OPERATIONS}
        ],
    }


def test_an_operation_naming_a_served_layer_reaches_the_log_refused_rather_than_never_reaching_it(
    alice: Party,
) -> None:
    """**This inverts the reading of M2 that MAP-66's task spec retires in its Acceptance block,
    and the name is where a reader is told so.** That reading made the clause's server half *the
    server's log never holds an operation naming a served layer*; ADR-0014 decision 3 keeps every
    refused operation on the append-only log with its verdict and its reason, and M15's Shape
    (added 2026-09-17) says so of any refused operation.

    **The entry is read whole**, the verdict and the reason beside the operation as its client
    authored it, because an implementation that took the retired reading literally keeps the served
    operation off the log and still answers the client correctly, which is the one place that
    reading survives unseen."""
    a_served_layer, naming_the_served_layer, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )
    authored = _a_feature_create(
        alice,
        layer_id=a_served_layer,
        feature_id=uuid4(),
        operation_id=naming_the_served_layer,
        from_installation=installation,
        mutation_number=0,
    )

    _the_server_took(browser, _a_queue_of(authored))

    assert _what_the_log_keeps_of(alice, naming_the_served_layer) == WhatTheLogKeeps(
        verdict=REFUSED,
        refusal_reason=SERVED_LAYER_TAKES_NO_OPERATIONS,
        client_half=ClientHalf.model_validate(authored),
    )


def test_an_operation_on_a_layer_this_project_lacks_is_refused_for_that_beside_a_served_one(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-23 on the position it calls forced: a layer's
    declarations cannot be read for a layer the project does not hold, so `no_layer_in_this_project`
    comes first. Under ADR-0014 decision 1 that order is **per operation**, so each operation is
    refused for its own layer rather than the batch taking one reason for all of it.

    **A served layer the project holds, then a layer it lacks**, because each is what a wrong
    reading answers for instead: a reason decided once for the batch, or a served layer anywhere in
    it refusing every operation for its class, names the served reason twice."""
    a_served_layer, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=0,
            ),
            an_operation_on_a_layer_this_project_lacks(
                alice, from_installation=installation, mutation_number=1
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 1,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: SERVED_LAYER_TAKES_NO_OPERATIONS},
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_LAYER_IN_THIS_PROJECT},
        ],
    }


def test_a_geometry_outside_the_family_its_layer_declares_is_refused_by_a_verdict_naming_it(
    alice: Party,
) -> None:
    """M2's geometry-family clause with M9's final one: the declared kind is a contract on the
    layer's features rather than a label on the layer, so a geometry of another family is refused
    with a typed error, and the refusal falls on that operation alone (ADR-0014 decision 1).

    **Three drawings, and the parcel is neither the first geometry-bearing operation of the batch
    nor the last.** A point surveyed before the mistake and another after it rule out every
    implementation that names an operation by position rather than by the check that failed: the
    first or last of the batch, or the first or last carrying a geometry. The whole body is
    compared because ADR-0010 decision 6 closes it, so a list naming anything beside the parcel is
    red too."""
    a_point_layer, installation = uuid4(), uuid4()
    surveyed_before, drawn_by_mistake, surveyed_after = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed_before,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_POINT_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed_before,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=drawn_by_mistake,
                from_installation=installation,
                mutation_number=2,
            ),
            _a_geometry_set_carrying(
                A_PARCEL,
                alice,
                layer_id=a_point_layer,
                feature_id=drawn_by_mistake,
                from_installation=installation,
                mutation_number=3,
            ),
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed_after,
                from_installation=installation,
                mutation_number=4,
            ),
            _a_geometry_set_carrying(
                A_POINT_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed_after,
                from_installation=installation,
                mutation_number=5,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 5,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 3, THE_REASON: GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY}
        ],
    }


def test_the_geometry_that_left_the_family_first_is_refused_though_the_fold_keeps_one_inside_it(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 on the guard, on the axis the unknown layer's correction did not cover:
    the fold keeps the last geometry each feature was given as well as its last address, so a guard
    fed from it never sees a geometry an earlier operation carried.

    **One feature and two geometries, the parcel drawn first and the point surveyed after it**,
    which is the shape the two readings answer differently: the fold keeps the point, a guard fed
    from it finds a point on a point layer, and the operation carrying the parcel is applied with
    nobody having looked at it (M2, M9)."""
    a_point_layer, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_PARCEL,
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_geometry_set_carrying(
                A_POINT_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 2,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY}
        ],
    }


def test_a_geometry_outside_the_family_never_reaches_the_current_state_the_application_reads(
    alice: Party,
) -> None:
    """M2's *refused rather than stored*, with ADR-0012 decision 3 as narrowed 2026-09-17: the fold
    walks what the flush **applied**, or a refusal would leave exactly the state it exists to
    withhold.

    **The feature is surveyed first and redrawn as a parcel second**, which is what makes the
    withholding observable: a column nobody wrote and a refusal that wrote nothing both hold
    nothing, and only a column already holding the surveyed point can show a refused parcel landing
    over it, or a refusal that clears what it was told not to touch.

    The status is the positive control, and it separates this from the shape ADR-0014 retired: a
    whole-batch `409` leaves the surveyed point alone too."""
    a_point_layer, surveyed, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_POINT_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    redrawn_as_a_parcel = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set_carrying(
                A_PARCEL,
                alice,
                layer_id=a_point_layer,
                feature_id=surveyed,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert redrawn_as_a_parcel.status_code == HTTPStatus.OK
    assert _the_geometry_the_projection_holds(alice, surveyed) == Point(
        *A_PLACE_IN_THE_FIELD, srid=STORAGE_FRAME_SRID
    )


def test_a_flush_carrying_a_geometry_outside_the_family_still_applies_the_operations_beside_it(
    alice: Party,
) -> None:
    """**This inverts the cases ADR-0014's Consequences name as needing rework, and the name is
    where a reader is told so.** Those cases asserted that a refused batch applies nothing at all,
    and ADR-0014 decision 1 takes this refusal out of that shape: it judges what the client authored
    against server state it could not have known, the queue is append-only, and a batch refused
    whole stalls the stream permanently against I2. M9's final clause now says it in its own words,
    the refusal falling on that operation alone.

    **The create for the parcel's own feature is applied and so is a feature drawn after it**, so
    what is asserted is neither a refusal that took the batch down with it nor one that stopped the
    batch at the first bad operation (ADR-0014 decision 7).

    **The whole body is the control that the parcel was refused at all**, because the two features
    are what the projection holds whether or not anything looked at the parcel: a flush with no
    family check applies all three operations and leaves exactly this state."""
    a_point_layer, drawn_as_a_parcel, drawn_after, installation = uuid4(), uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=drawn_as_a_parcel,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_PARCEL,
                alice,
                layer_id=a_point_layer,
                feature_id=drawn_as_a_parcel,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=drawn_after,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 2,
        THE_REFUSALS: [
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY}
        ],
    }
    assert _the_features_the_projection_holds(alice) == {drawn_as_a_parcel, drawn_after}


def test_a_geometry_outside_the_family_is_kept_on_the_log_as_drawn_with_its_verdict_and_reason(
    alice: Party,
) -> None:
    """M9's final clause on the half that decides whether it protects field work or destroys it:
    the operation is **flagged and retained for inspection, never discarded**, and ADR-0014 decision
    3 makes the log that retention, the verdict and the reason as columns beside the client half.

    **The entry is read whole, and the refused geometry is inside it.** What preserve-not-discard
    protects is the parcel that was drawn, not the record of a failure, so an implementation that
    keeps the identifier, the verdict and the reason while rewriting or dropping the payload is the
    preserve-not-discard sin wearing a validation costume (C7, M9's own words)."""
    a_point_layer, feature_id, carrying_a_parcel, installation = uuid4(), uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )
    drawn_in_the_field = _a_geometry_set_carrying(
        A_PARCEL,
        alice,
        layer_id=a_point_layer,
        feature_id=feature_id,
        operation_id=carrying_a_parcel,
        from_installation=installation,
        mutation_number=1,
    )

    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            drawn_in_the_field,
        ),
    )

    assert _what_the_log_keeps_of(alice, carrying_a_parcel) == WhatTheLogKeeps(
        verdict=REFUSED,
        refusal_reason=GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY,
        client_half=ClientHalf.model_validate(drawn_in_the_field),
    )


def test_a_geometry_set_stating_there_is_none_is_applied_rather_than_refused_for_its_family(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-23 on the scope of the family check: a geometry set
    whose payload carries null is not a geometry of the wrong family, it states that the feature
    has none (ADR-0012 decision 3's addition of 2026-09-09), and it is applied rather than refused.

    **On a polygon layer rather than the point layer the shared arrangers address**, so the case
    does not rest on the family they hold still. The whole body is compared because the refusal
    list is where a wrong reading of null shows."""
    a_polygon_layer, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_polygon_layer,
        geometry_kind=GeometryKind.POLYGON,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                None,
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {THE_ECHO: 1, THE_REFUSALS: []}


def test_a_multipart_geometry_is_stored_in_the_layer_whose_family_declares_its_type(
    alice: Party,
) -> None:
    """M2's geometry-family clause with D3, on the arm that keeps the refusal from firing on the
    work it exists to protect: the declared kind is a **family** and not a concrete type, so a
    multipart geometry belongs inside it, and a legal reserve is frequently multi-part.

    **The quiet side of a conditional rule, and it has no other witness through the route.** Every
    other geometry this module expects stored is of a single-part type, a point, a line or a ring
    with an enclave, so a rule comparing the declared kind against one concrete type per family
    accepts all of them and refuses this one. The stored geometry is asserted rather than the
    status, because the refusal answers `200` as well."""
    a_point_layer, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                TWO_POINTS_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == MultiPoint(
        Point(*A_PLACE_IN_THE_FIELD),
        Point(*ANOTHER_PLACE_IN_THE_FIELD),
        srid=STORAGE_FRAME_SRID,
    )


def test_a_ring_carrying_an_enclave_is_stored_in_the_polygon_layer_whose_family_declares_it(
    alice: Party,
) -> None:
    """M2's geometry-family clause with D3, on the second case both name: a ring carrying an enclave
    is inside the polygon family rather than outside it, which is what a preservation area with a
    clearing inside it actually is.

    **What it catches is whatever treats the enclave differently from a simple parcel declaring the
    same `Polygon` type**: a family rule reading inside the geometry and putting this ring outside
    the family, or a write storing it without its enclave or with the enclave's vertex order
    changed. Not a rule matching the declared kind against the type by identity, since an identity
    match and a family match agree on `Polygon`."""
    a_polygon_layer, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_polygon_layer,
        geometry_kind=GeometryKind.POLYGON,
        storage_class=StorageClass.ELEMENT,
    )

    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_PARCEL_WITH_AN_ENCLAVE,
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == Polygon(
        THE_PARCELS_BOUNDARY, THE_ENCLAVE_INSIDE_IT, srid=STORAGE_FRAME_SRID
    )


def test_a_line_is_stored_in_the_line_layer_whose_family_declares_it(alice: Party) -> None:
    """M2's geometry-family clause on the family no other case reaches through the refusal: the
    kind a layer declares is read off **that** layer, so each kind is a branch of its own and the
    point and polygon cases above cannot stand in for this one.

    **The quiet side.** A rule that reads the line family wrong, down to admitting only a point on
    a line layer, is green against every point and polygon layer here and refuses this line. The
    stored geometry is asserted rather than the status, because the refusal answers `200` as well,
    and it comes from the literal places rather than from the wire payload under test."""
    a_line_layer, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_line_layer,
        geometry_kind=GeometryKind.LINE,
        storage_class=StorageClass.ELEMENT,
    )

    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_line_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                A_LINE_SURVEYED_IN_THE_FIELD,
                alice,
                layer_id=a_line_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    assert _the_geometry_the_projection_holds(alice, feature_id) == LineString(
        A_PLACE_IN_THE_FIELD, ANOTHER_PLACE_IN_THE_FIELD, srid=STORAGE_FRAME_SRID
    )


@pytest.mark.parametrize(
    ("family", "of_another_family"),
    [
        pytest.param(
            GeometryKind.LINE, A_POINT_SURVEYED_IN_THE_FIELD, id="a-point-on-a-line-layer"
        ),
        pytest.param(
            GeometryKind.POLYGON, A_LINE_SURVEYED_IN_THE_FIELD, id="a-line-on-a-polygon-layer"
        ),
    ],
)
def test_a_line_or_polygon_layer_refuses_a_geometry_outside_the_family_it_declares(
    alice: Party, family: GeometryKind, of_another_family: JsonObject
) -> None:
    """The same clause's firing side, with M9's final one, on the two kinds whose refusal no other
    case arranges: every geometry refused elsewhere here is refused by a point layer, so a rule
    that admits anything on a line or a polygon layer is green against all of them.

    **A point on a line layer is the other half of the line case above**: a rule admitting only
    points on a line layer refuses that line and admits this point, so each case is red for one of
    the two ways it is wrong. The whole body is compared because ADR-0010 decision 6 closes it."""
    a_layer_of_that_family, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_layer_of_that_family,
        geometry_kind=family,
        storage_class=StorageClass.ELEMENT,
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_of_that_family,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                of_another_family,
                alice,
                layer_id=a_layer_of_that_family,
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
            {THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY}
        ],
    }
