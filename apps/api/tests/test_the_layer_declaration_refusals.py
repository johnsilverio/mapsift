"""A layer's own declarations refuse two kinds of operation, and the flush path is where they do it.

Trace: PRD **M2** and PRD **M9**, for the halves of their Acceptance clauses that the Acceptance
block of `specs/tasks/MAP-66-layer-declaration-refusals.md` assigns this task, which is where each
split is recorded; **ADR-0010 decision 6's addition of 2026-09-15** for the two
reason values, the `refused_operation_id` key and the rule that populates it, and that decision's
addition of 2026-09-08 for the member these two follow; **ADR-0012 decision 3** for the write these
refusals stand in front of; ADR-0005 sections 3 and 4 for the binding every read and write here
happens inside. Invariants I1 and I9; constraints C1 and C7.

**Here rather than under either package, on the gate ADR-0007 section 6 keeps this directory for.**
The subject spans two packages: what a layer declares is `layers`' and the flush that consults it is
`sync`', and the cases that prove a refused batch left nothing behind read both tables. A module
under `mapsift/sync/tests/` may not read `mapsift.layers.models` and one under
`mapsift/layers/tests/` may not read `mapsift.sync.models`; both are `protected` contracts in
`pyproject.toml` that `just lint` enforces.

**Its own module rather than beside the unknown-layer sibling in
`tests/test_the_projection_at_the_flush.py`**, which is where that refusal's cases sit: this one has
a subject of its own, the declarations a layer carries, and every case here varies a declaration
while that module deliberately holds both still and says so.

**Everything goes through the route and never through the writer**, on the ground the flush modules
already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only transaction
is its own context manager is green against an implementation that has none, and what a refused
batch leaves behind is exactly what that would hide.

**Every read of either table forces its rows inside the binding that authorised it**, because a
queryset evaluated after `tenant_scope` closes is answered by the policy with zero rows and no
exception, so nothing below answers with a queryset.

What is deliberately not here, each with the issue that owns it: the **element budget** and the
**import classification**, M2's other Acceptance clauses, which no code reaches; a **feature
changing path**, whose promotion half is OQ-6 and whose layer-changing-class half needs a layer to
change class, which nothing does; a **server-side flag** on the refused operation (T5.2; **MAP-72**
per ADR-0010 decision 6's correction of 2026-09-16); **what a valid geometry payload is on the
wire** (MAP-70 for the shapes that answer `500`, MAP-69 for the frame a payload declares, MAP-33
for the encoding), so every payload below is one the parser and the column already take and no
case here asks what happens to one they do not; a **create addressing a feature that already
exists** (MAP-68); and the **per-feature version** (MAP-38).

**One shape nothing here arranges, on the convention the projection module states:** a
`feature.geometry.set` for a feature no operation ever created. Every geometry below follows a
create for its own feature in the same batch.
"""

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import GEOSGeometry, MultiPoint, Point, Polygon

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    a_geometry_set_claiming,
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

# The closed object this route's second answer carries, the two members a layer's declarations add
# to its reason set (ADR-0010 decision 6's addition of 2026-09-15) and the member they follow (its
# addition of 2026-09-08). Spelled as literals rather than read off `WhyAStreamCannotBeContinued`,
# because these are the wire values that decision fixes and a case comparing the enum against
# itself cannot notice a member being renamed.
THE_REASON = "reason"
THE_RESTART_POINT = "resend_from_mutation_number"
THE_REFUSED_OPERATION = "refused_operation_id"
NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"
SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY = "geometry_outside_the_layers_family"

# Two places a field client surveys, far enough apart in both coordinates that a geometry stored
# with its axes swapped is equal to neither.
A_PLACE_IN_THE_FIELD = (-47.6, -15.9)
ANOTHER_PLACE_IN_THE_FIELD = (-47.5, -15.4)

# A parcel's boundary counterclockwise and an enclave inside it clockwise, which is the winding
# GeoJSON states for an exterior ring and its hole. The two are written out as wire coordinates and
# again as the geometry a case expects storage to hold, rather than one being computed from the
# other, so the expectation comes from the literal and never from the reading under test.
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

A_POINT_SURVEYED_IN_THE_FIELD: JsonObject = {
    "type": "Point",
    "coordinates": [-47.6, -15.9],
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

    Neither declaration carries a default, unlike the arrangers in the sibling suites: this module
    is about what a layer declares, so a case that did not say both would be arranging the thing it
    is about somewhere a reader cannot see it.
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
    operation_id: UUID | None = None,
    from_installation: UUID | None = None,
    mutation_number: int = 0,
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


def _a_geometry_set_carrying(
    party: Party,
    *,
    layer_id: UUID,
    feature_id: UUID,
    geometry: JsonObject,
    operation_id: UUID | None = None,
    from_installation: UUID | None = None,
    mutation_number: int = 0,
) -> JsonObject:
    """The catalog's geometry set, carrying whichever whole geometry a case is about (M9).

    The payload is replaced whole rather than made a parameter of the shared arranger, which is the
    shape `tests/test_the_projection_at_the_flush.py` already uses for the payload it has to state
    outright: the shared one carries a point on purpose, and every case here that varies the family
    is varying exactly what that default holds still.
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


def _the_operations_the_log_holds(party: Party) -> set[UUID]:
    """Every operation the append-only log holds for a tenant (M15).

    The server side of the operation queue M2 says a served layer's features never enter, so this
    is where that clause is read rather than inferred.
    """
    with tenant_scope(party.tenant_id):
        return set(OperationLogEntry.objects.values_list("operation_id", flat=True))


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


def test_an_operation_naming_a_served_layer_is_refused_as_a_typed_conflict(alice: Party) -> None:
    """M2's first Acceptance clause with ADR-0010 decision 6's addition of 2026-09-15: the storage
    class is a property of the layer and it decides which path the layer's features take, so an
    operation naming a served layer is refused before it becomes state rather than queued as though
    the frontier did not exist.

    **The whole body is compared rather than one key of it**, because that addition closes this
    object exactly as the additions before it closed the acknowledgement's and the refusal's.
    `refused_operation_id` is null here and the null is the decision rather than an omission, on
    the populate-or-not rule that same addition fixes; the restart point is null for the reason it
    gives the layer refusal beside this one."""
    a_served_layer = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(_a_feature_create(alice, layer_id=a_served_layer, feature_id=uuid4())),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {
        THE_REASON: SERVED_LAYER_TAKES_NO_OPERATIONS,
        THE_RESTART_POINT: None,
        THE_REFUSED_OPERATION: None,
    }


def test_a_batch_naming_a_served_layer_first_is_refused_though_its_feature_ends_under_another(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 on the **guard** rather than on the write, which is the trap the unknown
    layer's own refusal was shipped with and corrected for: the set a refusal is decided over is the
    operations, never the state they fold to. That fold keeps one row per feature and the last
    address each feature was given, so a guard fed from its output never sees a layer an earlier
    operation named.

    **One feature and two operations, the served layer named first**, which is the only shape that
    tells the two readings apart: give the served layer a feature of its own and it survives any
    fold, so the guard answers alike either way. Here the second operation replaces the address the
    fold keeps, and a guard reading the folded state applies a batch whose first operation filed a
    feature under a layer whose features never enter the queue at all (M2).

    **The reason is named beside the status rather than the whole body compared**, because what this
    case adds is that the refusal is reached and not what its object carries: every other reason in
    its set answers `409` too, so a status alone would not say which mechanism refused."""
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

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=an_element_layer,
                feature_id=feature_id,
                geometry=A_POINT_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REASON] == SERVED_LAYER_TAKES_NO_OPERATIONS


def test_a_served_layers_feature_never_reaches_the_operation_queue_while_an_element_layers_does(
    alice: Party,
) -> None:
    """M2's first Acceptance clause read on both of its arms, which is the only reading that says
    anything: a served layer's features never appear in the operation queue **and an element
    layer's do**, so an implementation that refused every flush satisfies the first half and fails
    the second.

    The log is where that clause is observable, being the server side of the queue, and M10's
    applies-nothing-at-all is what makes the refused batch's own element-layer operation absent from
    it too: the batch is refused whole, and what the client keeps is its own queue (M9).

    **The accepted flush before it is the control and it closes this suite's own trap:** the log is
    read under Alice's binding, which is exactly where a rogue row would have landed, and the wall
    answers a bound read with nothing as readily as an empty table does."""
    an_element_layer, a_served_layer, installation = uuid4(), uuid4(), uuid4()
    accepted, alongside_the_served_layer, naming_the_served_layer = uuid4(), uuid4(), uuid4()
    accepted_feature = uuid4()
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

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=an_element_layer,
                feature_id=accepted_feature,
                operation_id=accepted,
                from_installation=installation,
                mutation_number=0,
            )
        ),
        JSON,
    )
    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=an_element_layer,
                feature_id=uuid4(),
                operation_id=alongside_the_served_layer,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=a_served_layer,
                feature_id=uuid4(),
                operation_id=naming_the_served_layer,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert _the_operations_the_log_holds(alice) == {accepted}
    assert _the_features_the_projection_holds(alice) == {accepted_feature}


def test_a_geometry_outside_the_family_its_layer_declares_is_refused_as_a_typed_conflict(
    alice: Party,
) -> None:
    """M2's geometry-family clause with M9's refusal: the declared kind is a contract on the layer's
    features rather than a label on the layer, so a geometry of another family is refused rather
    than stored, and M9 makes that refusal a typed error whose operation is flagged and retained for
    inspection rather than discarded.

    **The whole body is compared**, and the key that separates this refusal from every other reason
    in its set is `refused_operation_id`, carried here and null for each of them. Why M9 forces that
    key, and why the restart point is null, are ADR-0010 decision 6's addition of 2026-09-15."""
    a_point_layer = uuid4()
    feature_id, installation = uuid4(), uuid4()
    carrying_a_parcel = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    refused = browser.post(
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
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                geometry=A_PARCEL,
                operation_id=carrying_a_parcel,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json() == {
        THE_REASON: GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY,
        THE_RESTART_POINT: None,
        THE_REFUSED_OPERATION: str(carrying_a_parcel),
    }


def test_the_refusal_names_the_one_operation_whose_geometry_left_the_family(alice: Party) -> None:
    """ADR-0010 decision 6's addition of 2026-09-15 on the half it calls load-bearing, serving
    M9's flag-and-retain clause: `geometry_outside_the_layers_family` names the operation it
    refused.

    **Three drawings, and the parcel is neither the first geometry-bearing operation of the batch
    nor the last**, which is what makes the assertion say something. A point surveyed before the
    mistake and another after it rule out every implementation that names an operation by its
    position rather than by the check that failed: the first or the last operation of the batch,
    the first or the last operation carrying a geometry, or whichever one it happened to be
    holding. Each of those names some other operation, and only the check that failed names the
    parcel.

    The status is the positive control rather than a second subject, on this suite's rule that no
    assertion about one key of a body stands alone: a response that never carried a refusal has no
    such key either, and the two have to be told apart."""
    a_point_layer = uuid4()
    the_point_surveyed_before_it, the_parcel_drawn_by_mistake = uuid4(), uuid4()
    the_point_surveyed_after_it = uuid4()
    carrying_a_parcel, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=the_point_surveyed_before_it,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_point_layer,
                feature_id=the_point_surveyed_before_it,
                geometry=A_POINT_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=the_parcel_drawn_by_mistake,
                from_installation=installation,
                mutation_number=2,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_point_layer,
                feature_id=the_parcel_drawn_by_mistake,
                geometry=A_PARCEL,
                operation_id=carrying_a_parcel,
                from_installation=installation,
                mutation_number=3,
            ),
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=the_point_surveyed_after_it,
                from_installation=installation,
                mutation_number=4,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_point_layer,
                feature_id=the_point_surveyed_after_it,
                geometry=A_POINT_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=5,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REFUSED_OPERATION] == str(carrying_a_parcel)


def test_a_batch_whose_first_geometry_left_the_family_is_refused_though_its_feature_ends_inside_it(
    alice: Party,
) -> None:
    """ADR-0012 decision 3 on the guard, on the axis the unknown layer's correction did not cover:
    the fold keeps the last geometry each feature was given as well as the last address, so a guard
    fed from it never sees a geometry an earlier operation carried.

    **One feature and two geometries, the parcel drawn first and the point surveyed after it**,
    which is the shape the two readings answer differently: the fold keeps the point, a guard fed
    from it finds a point on a point layer and applies the batch, and the operation carrying the
    parcel reaches the log with nobody having looked at it (M2, M9)."""
    a_point_layer = uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    refused = browser.post(
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
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                geometry=A_PARCEL,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                geometry=A_POINT_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REASON] == GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY


def test_a_batch_refused_for_a_geometry_outside_the_family_applies_nothing_at_all(
    alice: Party,
) -> None:
    """M10's applies-nothing-at-all with M9's flag-and-retain, which is the pair an implementation
    is most tempted to break here: M9 says the operation is retained rather than discarded and
    `refused_operation_id` names exactly one operation, so dropping only that one and applying the
    rest reads like the requirement being honoured. It is the opposite. The batch is refused whole
    and rolled back, which is what leaves the client holding every operation it authored.

    **The create beside the refused geometry is what makes the assertion say something**: it is an
    operation this route would apply on its own, so what is asserted is a batch that applied nothing
    rather than a refusal that lost only the operation it named. **The accepted flush before it is
    the control**, since an empty log and an empty projection satisfy *nothing was written* whether
    the refusal held or nothing was ever applied at all."""
    a_point_layer, installation = uuid4(), uuid4()
    accepted, accepted_feature = uuid4(), uuid4()
    the_feature_drawn_beside_it = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=accepted_feature,
                operation_id=accepted,
                from_installation=installation,
                mutation_number=0,
            )
        ),
        JSON,
    )
    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_point_layer,
                feature_id=the_feature_drawn_beside_it,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_point_layer,
                feature_id=the_feature_drawn_beside_it,
                geometry=A_PARCEL,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert _the_operations_the_log_holds(alice) == {accepted}
    assert _the_features_the_projection_holds(alice) == {accepted_feature}


def test_a_served_layer_carrying_a_geometry_of_another_family_is_refused_for_its_storage_class(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-15 on the one order between these two refusals
    that it calls a choice rather than forced: the storage class is taken first, so a batch both
    refusals answer is refused for its layer's class and never for its geometry.

    Both refusals apply to this batch, so the reason is what this case is about and the status is
    only its positive control: an implementation that took them in the other order answers `409`
    here too, and one that refuses nothing carries no reason key at all."""
    a_served_point_layer = uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_served_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.SERVED,
    )

    refused = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_served_point_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_served_point_layer,
                feature_id=feature_id,
                geometry=A_PARCEL,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REASON] == SERVED_LAYER_TAKES_NO_OPERATIONS


def test_a_batch_naming_a_layer_this_project_lacks_is_refused_for_it_ahead_of_any_declaration(
    alice: Party,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-15 on the order it calls forced rather than chosen:
    a layer's declarations cannot be read until the layer is known to exist, so
    `no_layer_in_this_project` is taken ahead of both refusals a layer's declarations make.

    **A served layer this project holds, then a geometry filed under a layer it lacks**, because
    each is what one wrong order answers for instead. Taking the storage class first refuses the
    batch for the served layer. Taking the family first asks the family of a layer that does not
    exist, and the batch answers the untyped `500` the addition of 2026-09-08 exists to forbid
    rather than any refusal at all. The served layer is named first, so an order decided operation
    by operation meets it ahead of the absent one as well.

    **The reason is named beside the status rather than the whole body compared**, as in the case
    above: which refusal is reached is what this case adds, and the whole body this reason carries
    is compared where that refusal is witnessed on its own, in
    `tests/test_the_projection_at_the_flush.py`."""
    a_served_layer, a_layer_this_project_lacks = uuid4(), uuid4()
    feature_under_the_served_layer, feature_under_the_absent_layer = uuid4(), uuid4()
    installation = uuid4()
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
                feature_id=feature_under_the_served_layer,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_feature_create(
                alice,
                layer_id=a_layer_this_project_lacks,
                feature_id=feature_under_the_absent_layer,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_geometry_set_carrying(
                alice,
                layer_id=a_layer_this_project_lacks,
                feature_id=feature_under_the_absent_layer,
                geometry=A_POINT_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert refused.status_code == HTTPStatus.CONFLICT
    assert refused.json()[THE_REASON] == NO_LAYER_IN_THIS_PROJECT


def test_a_multipart_geometry_is_stored_in_the_layer_whose_family_declares_its_type(
    alice: Party,
) -> None:
    """M2's geometry-family clause with D3, on the arm that keeps the refusal from firing on the
    work it exists to protect: the declared kind is a **family** and not a concrete type, so a
    multipart geometry belongs inside it, and a legal reserve is frequently multi-part.

    **This is the quiet side of a conditional rule and it has no other witness.** Every accepted
    flush in this repository carries a simple point to a point layer, so an implementation
    comparing the declared kind against the payload's type by identity accepts all of them and
    refuses this one, and nothing outside this case would go red."""
    a_point_layer = uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_point_layer,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )

    applied = browser.post(
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
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                geometry=TWO_POINTS_SURVEYED_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert applied.status_code == HTTPStatus.OK
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
    same `Polygon` type**: a family rule that reads inside the geometry and puts this ring outside
    the family, or a write that stores it without its enclave or with that enclave's vertex order
    changed, and not a rule matching the declared kind against the type by identity, since an
    identity match and a family match agree on `Polygon`.

    **The quiet side of the rule again, and green before the refusal exists**, which is why the
    stored geometry is asserted and not the status alone: a route that stored nothing answers `200`
    just as readily."""
    a_polygon_layer = uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _a_layer_of(
        alice,
        layer_id=a_polygon_layer,
        geometry_kind=GeometryKind.POLYGON,
        storage_class=StorageClass.ELEMENT,
    )

    applied = browser.post(
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
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                geometry=A_PARCEL_WITH_AN_ENCLAVE,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert applied.status_code == HTTPStatus.OK
    assert _the_geometry_the_projection_holds(alice, feature_id) == Polygon(
        THE_PARCELS_BOUNDARY, THE_ENCLAVE_INSIDE_IT, srid=STORAGE_FRAME_SRID
    )
