"""An operation is judged against the feature it names, so none re-files, re-creates or conjures.

Trace: PRD **M9**, the clause its Acceptance gained on 2026-09-24, whole: a `feature.create` naming
a feature the tenant already holds, under whatever layer or project, and any other operation naming
a feature the tenant does not hold at the layer and project it names, are each refused with a typed
error on that operation alone and retained, and a held feature stays where it was. **ADR-0010
decision 6's addition of 2026-09-24** is the contract for the two reason values; PRD **M2**'s
geometry-family clause for the half MAP-66 left, the stored row pairing a layer and a geometry no
single operation carried; **ADR-0014 decisions 1, 3 and 7** for the verdict, its retention on the
log and the batch it is judged in; ADR-0012 decision 3 as narrowed 2026-09-17 for the projection a
refusal stands in front of; PRD M3 for an identifier naming one object for its life; ADR-0005
sections 3 and 4 for the binding every read here happens inside. I2, I3; C3, C7.

**Here rather than under either package, on the gate ADR-0007 section 6 keeps this directory for.**
The verdict is written on `sync`'s log and what it protects is `layers`' current state, and the
cases proving a feature stayed where it was read both.

**Everything goes through the route and never through the writer**, on the ground the flush modules
already state: `tenant_scope` opens `transaction.atomic()` itself, so a case whose only transaction
is its own context manager is green against an implementation that has none. **Every read forces
its rows inside the binding that authorised it**, because a queryset evaluated after the block
closes is answered by the policy with zero rows and no exception.

**A case about where a feature stayed asserts the refusal list first, as its control.** A feature
left where it was is what this rule produces and also what a refusal for any other reason produces,
and the arrangements here name second layers and second projects, which is exactly where a missing
arrangement earns `no_layer_in_this_project` and leaves the state green for a reason the case is not
about.

What is deliberately not here, each with the issue that owns it: the **cross-tenant identifier
collision** M9's Provenance accepts as the one exception to T6.5, which is accepted rather than
witnessed and whose retirement is **MAP-75**, so no case here arranges an identifier another tenant
holds; **two flushes of one installation in flight at once** (**MAP-76**); **one operation
identifier twice inside one batch** (**MAP-73**); what a wire-legal geometry payload is (**MAP-70**,
**MAP-69**, **MAP-33**), so every payload below is one GEOS and the column already take;
**deletion**, which the catalog does not carry (`libs/core/src/catalog.rs`); the create naming a
held feature under **another layer of the same project**, M9's arm and M2's half across flushes,
which lives where it inverted,
`test_a_create_for_a_feature_that_already_exists_leaves_it_under_the_layer_it_was_drawn_in` in
`tests/test_the_projection_at_the_flush.py`; the order among the five reasons and what a batch
contributes to what the tenant holds, which are decisions over plain data and are
`mapsift/sync/tests/test_the_reason_an_operation_is_refused_for.py`'s; an operation the log already
holds, resent (**MAP-74**, `tests/test_an_operation_the_log_already_holds.py`); and the record each
refusal leaves, which is `mapsift/sync/tests/test_the_flush_decision_trail.py`'s.
"""

from dataclasses import dataclass
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

# The success body as ADR-0010 decision 6's addition of 2026-09-17 closes it, and the two members
# its addition of 2026-09-24 adds to the refusal set. Literals rather than reads off the enum that
# carries them, because a case comparing an enum against itself cannot notice a member renamed.
THE_ECHO = "last_decided_mutation_number"
THE_REFUSALS = "refused"
THE_MUTATION_NUMBER_REFUSED = "mutation_number"
THE_REASON = "reason"
FEATURE_ALREADY_CREATED = "feature_already_created"
NO_FEATURE_AT_THIS_ADDRESS = "no_feature_at_this_address"

# The member of the envelope's closed verdict set a refusal is stored under (ADR-0014 decisions 3
# and 4), spelled as the module that owns that contract spells it.
REFUSED = "refused"

# Two places a field client surveys, differing in both coordinates so a geometry stored with its
# axes swapped is equal to neither, and neither the place `a_geometry_set_claiming` carries by
# default, so an arranger that stopped forwarding `at` leaves a geometry assertion red.
A_PLACE_IN_THE_FIELD = (-47.6, -15.9)
ANOTHER_PLACE_IN_THE_FIELD = (-47.5, -15.4)


def _an_element_layer_declaring(
    party: Party,
    *,
    layer_id: UUID,
    geometry_kind: GeometryKind,
    in_project: UUID | None = None,
) -> None:
    """One element layer in a project of this party's tenant, of the family a case names (M2).

    Element rather than served, because a served layer's operations are refused for their class
    before the feature they name is asked about (ADR-0010 decision 6's addition of 2026-09-24).
    """
    with tenant_scope(party.tenant_id):
        create_layer(
            layer_id=layer_id,
            tenant_id=party.tenant_id,
            project_id=in_project or party.project_id,
            name="vegetation cover",
            geometry_kind=geometry_kind,
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
    in_project: UUID | None = None,
) -> JsonObject:
    """The catalog's create, addressed at one layer and one feature of a project of this party.

    The installation and the mutation number carry no default, because every verdict here is read
    off a stream a case numbers itself (M4, C12).
    """
    return a_feature_create_claiming(
        party.tenant_id,
        operation_id=operation_id,
        client_id=from_installation,
        mutation_number=mutation_number,
        project_id=in_project or party.project_id,
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
    in_project: UUID | None = None,
) -> JsonObject:
    """The catalog's geometry set, carrying the whole geometry rather than a delta (M9)."""
    return a_geometry_set_claiming(
        party.tenant_id,
        operation_id=operation_id,
        client_id=from_installation,
        mutation_number=mutation_number,
        project_id=in_project or party.project_id,
        layer_id=layer_id,
        feature_id=feature_id,
        at=at,
    )


def _the_server_took(browser: Client, batch: JsonObject) -> None:
    """Post a batch whose landing is arranged rather than asserted, and witness that it landed.

    The reason the flush modules give: an arrange step that quietly starts being refused leaves the
    assertions standing and the case vacuous rather than red.
    """
    assert browser.post(OPERATIONS_PATH, batch, JSON).status_code == HTTPStatus.OK


def _as_the_storage_frame_holds_it(place: tuple[float, float]) -> Point:
    """A place as a geometry in the one frame storage declares (M5 rule 1).

    GEOS equality compares the frame beside the coordinates, so a geometry compared without it is
    two frames being compared rather than two places.
    """
    return Point(place[0], place[1], srid=STORAGE_FRAME_SRID)


def _the_features_the_projection_holds(party: Party) -> set[UUID]:
    """Every feature the current-state table holds for a tenant (M15, ADR-0012 decision 1)."""
    with tenant_scope(party.tenant_id):
        return set(Feature.objects.values_list("id", flat=True))


@dataclass(frozen=True, slots=True)
class AProjectedFeature:
    """One projected row in the three columns a re-filing moves it through: the project, the layer
    and the geometry, so a row compared whole is a row nothing re-filed."""

    project_id: UUID
    layer_id: UUID
    geometry: GEOSGeometry | None


def _the_feature_the_projection_holds(party: Party, feature_id: UUID) -> AProjectedFeature:
    """One projected feature, read whole and by identifier, so a row nobody wrote raises rather
    than answering the same nothing a cleared column would (M15)."""
    with tenant_scope(party.tenant_id):
        held = Feature.objects.get(pk=feature_id)
        return AProjectedFeature(
            project_id=held.project_id,
            layer_id=held.layer_id,
            geometry=held.geometry,
        )


@dataclass(frozen=True, slots=True)
class WhatTheLogKeeps:
    """One log entry as M9's *retained the same way* reads it: the server's decision beside the
    operation exactly as its client authored it (ADR-0014 decision 3, M8)."""

    verdict: str
    refusal_reason: str | None
    client_half: ClientHalf


def _what_the_log_keeps_of(party: Party, operation_id: UUID) -> WhatTheLogKeeps:
    """The one entry the log holds for an operation, read whole (M15, ADR-0014 decision 3).

    `get` rather than the first of however many there are, so an operation appended twice raises
    here instead of answering with whichever row came back first, and so does one never appended.
    """
    with tenant_scope(party.tenant_id):
        entry = OperationLogEntry.objects.get(operation_id=operation_id)
        return WhatTheLogKeeps(
            verdict=entry.verdict,
            refusal_reason=entry.refusal_reason,
            client_half=ClientHalf.model_validate(entry.client_half),
        )


def test_a_create_naming_a_feature_the_tenant_already_holds_is_refused_as_already_created(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on its first half, at its narrowest: a `feature.create` naming a
    feature the tenant already holds is refused with a typed error, `feature_already_created`, on
    that operation alone. M3 keeps an identifier to one object for its life, so a second create of
    it names an object that already exists rather than a new one; measured at the pickup, the route
    answered this with nothing refused and logged the create applied.

    **The same layer the feature was created in**, so nothing about the address differs and the one
    thing wrong with the create is that its feature exists. **A create of another feature travels
    behind it** and is not refused, and the whole body is compared because ADR-0010 decision 6
    closes it: a refusal that took the rest of the batch with it, or named the wrong operation, is
    red, and the echo counts both as decided (ADR-0014 decision 5)."""
    layer_id, feature_id, installation = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=layer_id, geometry_kind=GeometryKind.POINT)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            )
        ),
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 2,
        THE_REFUSALS: [{THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: FEATURE_ALREADY_CREATED}],
    }


def test_a_create_naming_a_feature_held_in_another_project_leaves_it_where_it_was_filed(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24, *under whatever layer or project*, with its last words: **a held
    feature stays where it was**. Measured at the pickup, a create naming a feature filed in another
    project of the same tenant moved it there, geometry and all, and it was gone from the project it
    was surveyed in.

    **The flush comes from another installation, into another project**, because a flush addresses
    one project (ADR-0010 decision 6's addition of 2026-08-10) and the stream is per project (M10),
    so this is the only shape the re-filing ever took. What the tenant holds is the tenant's and
    not the project's (M9's Provenance), so the create is refused though its own project holds
    nothing.

    **The row is compared whole**, the project, the layer and the geometry being what a re-filing
    moves; the refusal list is the control this module's docstring gives."""
    the_layer_it_was_surveyed_in, feature_id = uuid4(), uuid4()
    the_other_project = second_project_of(alice)
    a_layer_of_the_other_project = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(
        alice, layer_id=the_layer_it_was_surveyed_in, geometry_kind=GeometryKind.POINT
    )
    _an_element_layer_declaring(
        alice,
        layer_id=a_layer_of_the_other_project,
        geometry_kind=GeometryKind.POINT,
        in_project=the_other_project,
    )
    surveyed_from = uuid4()
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_was_surveyed_in,
                feature_id=feature_id,
                from_installation=surveyed_from,
                mutation_number=0,
            ),
            _a_geometry_set(
                alice,
                layer_id=the_layer_it_was_surveyed_in,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=surveyed_from,
                mutation_number=1,
            ),
        ),
    )

    created_again_elsewhere = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_of_the_other_project,
                feature_id=feature_id,
                from_installation=uuid4(),
                mutation_number=0,
                in_project=the_other_project,
            )
        ),
        JSON,
    )

    assert created_again_elsewhere.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: FEATURE_ALREADY_CREATED}
    ]
    assert _the_feature_the_projection_holds(alice, feature_id) == AProjectedFeature(
        project_id=alice.project_id,
        layer_id=the_layer_it_was_surveyed_in,
        geometry=_as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD),
    )


def test_a_geometry_set_naming_a_feature_nothing_created_is_refused_as_no_feature_at_this_address(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on its second half: any operation other than a create naming a
    feature the tenant does not hold at the address it names is refused as
    `no_feature_at_this_address`, and the first way not to hold it is that **no applied operation
    ever created it**. M9 gives a geometry set no power to bring a feature into existence.

    **A create of another feature travels in front of it and is applied**, so the whole body says
    the refusal fell on the set alone, and the set is refused though its layer is one the project
    holds and its geometry is of that layer's family: its address is all that is wrong with it."""
    layer_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=layer_id, geometry_kind=GeometryKind.POINT)

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set(
                alice,
                layer_id=layer_id,
                feature_id=uuid4(),
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
        JSON,
    )

    assert answered.status_code == HTTPStatus.OK
    assert answered.json() == {
        THE_ECHO: 1,
        THE_REFUSALS: [{THE_MUTATION_NUMBER_REFUSED: 1, THE_REASON: NO_FEATURE_AT_THIS_ADDRESS}],
    }


def test_a_geometry_set_naming_a_feature_nothing_created_brings_no_feature_into_existence(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on the state rather than the answer: measured at the pickup, a
    geometry set naming a feature nothing created inserted a row for it, so a feature came into
    existence from an operation M9 does not give that power, and ADR-0012 decision 3 as narrowed
    2026-09-17 keeps a refused operation out of the fold that writes the current state.

    **The projection is compared whole, and the feature created beside the set is in it**, which is
    the positive control: a flush that projected nothing at all holds no conjured feature either."""
    layer_id, installation = uuid4(), uuid4()
    created, named_by_the_set_alone = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=layer_id, geometry_kind=GeometryKind.POINT)

    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=layer_id,
                feature_id=created,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set(
                alice,
                layer_id=layer_id,
                feature_id=named_by_the_set_alone,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    assert _the_features_the_projection_holds(alice) == {created}


def test_a_geometry_set_naming_a_feature_whose_only_create_was_refused_brings_no_feature_into_being(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on the word **applied**: an operation other than a create naming a
    feature the tenant does not hold is refused `no_feature_at_this_address` *whether no applied
    operation ever created it*, and a create the log keeps as refused created nothing (ADR-0014
    decision 3: a refused entry is not part of the current state). The cases above reach that
    clause only through an identifier nothing ever named, where a rule reading what the tenant holds
    off the log's entries of every verdict answers the same as one reading the current state.

    **The create is refused in an earlier flush and its reason is then taken away**: it named a
    layer the project lacked, and that layer is created before the next flush, so the geometry set
    names the very address the refused create named, on a layer the project now holds, with a
    geometry of its family. A rule counting the refused create as a filing admits it there and
    projects a feature that nothing applied ever created.

    **The refusal list is asserted first, as this module's control**, and a create of another
    feature travels beside the set, so the projection compared whole is a flush that projected
    something rather than nothing at all."""
    a_layer_created_too_late, feature_id, installation = (
        a_layer_this_project_lacks(),
        uuid4(),
        uuid4(),
    )
    drawn_beside_it = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            )
        ),
    )
    _an_element_layer_declaring(
        alice, layer_id=a_layer_created_too_late, geometry_kind=GeometryKind.POINT
    )

    answered = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=drawn_beside_it,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_geometry_set(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )

    assert answered.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 2, THE_REASON: NO_FEATURE_AT_THIS_ADDRESS}
    ]
    assert _the_features_the_projection_holds(alice) == {drawn_beside_it}


def test_a_create_naming_a_feature_whose_only_create_was_refused_is_admitted(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on the create's side of the same word: `feature_already_created`
    refuses a create naming a feature the tenant **holds**, and a feature whose only create the log
    keeps as refused is held nowhere (ADR-0014 decision 3), so a fresh create of it is admitted.
    This is the client's way back from that refusal: the layer it was missing now exists, and the
    feature is created again under a new operation, the refused one being answered from the log
    for as long as it is resent (T2.3 as sharpened that day).

    **The create is refused in an earlier flush**, which is what separates this from the in-batch
    rule `test_a_create_after_a_refused_create_of_the_same_feature_is_admitted` pins over plain
    data: the refused entry is on the log by the time this create is judged, so a rule reading what
    the tenant holds off the log's entries of every verdict refuses it here and nowhere else. The
    whole body is compared, because ADR-0010 decision 6 closes it."""
    a_layer_created_too_late, feature_id, installation = (
        a_layer_this_project_lacks(),
        uuid4(),
        uuid4(),
    )
    browser = a_browser(authenticated_as=alice.user_id)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            )
        ),
    )
    _an_element_layer_declaring(
        alice, layer_id=a_layer_created_too_late, geometry_kind=GeometryKind.POINT
    )

    created_again = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=a_layer_created_too_late,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=1,
            )
        ),
        JSON,
    )

    assert created_again.json() == {THE_ECHO: 1, THE_REFUSALS: []}


def test_a_geometry_set_naming_a_feature_filed_under_another_layer_leaves_it_where_it_was(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on the second way not to hold a feature at an address, **one
    filed elsewhere**, with its last words: a held feature stays where it was. Measured at the
    pickup, a set naming a feature under a second layer of the same project moved it there with the
    new geometry, so a feature filed under exactly one layer (M2) changed layer through an operation
    whose target path says it is already there.

    **The row is compared whole**, because what the re-filing moved was the layer and the geometry
    together, and a write that left the layer and took the geometry is as wrong as the one measured.
    The refusal list is the control this module's docstring gives."""
    the_layer_it_is_filed_under, another_layer = uuid4(), uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(
        alice, layer_id=the_layer_it_is_filed_under, geometry_kind=GeometryKind.POINT
    )
    _an_element_layer_declaring(alice, layer_id=another_layer, geometry_kind=GeometryKind.POINT)
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_is_filed_under,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=0,
            ),
            _a_geometry_set(
                alice,
                layer_id=the_layer_it_is_filed_under,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
        ),
    )

    set_under_another_layer = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set(
                alice,
                layer_id=another_layer,
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=2,
            )
        ),
        JSON,
    )

    assert set_under_another_layer.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 2, THE_REASON: NO_FEATURE_AT_THIS_ADDRESS}
    ]
    assert _the_feature_the_projection_holds(alice, feature_id) == AProjectedFeature(
        project_id=alice.project_id,
        layer_id=the_layer_it_is_filed_under,
        geometry=_as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD),
    )


def test_a_geometry_set_naming_a_feature_filed_in_another_project_leaves_it_where_it_was(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24 on the project axis of *filed elsewhere*: measured at the pickup, a
    geometry set naming a feature filed in another project of the same tenant moved it there with
    the new geometry and it was gone from the project it was surveyed in.

    **From another installation, into another project**, for the reason the create's sibling case
    gives: a flush addresses one project, so this is the only shape that move ever took. The row is
    compared whole and the refusal list is the control this module's docstring gives."""
    the_layer_it_was_surveyed_in, feature_id = uuid4(), uuid4()
    the_other_project = second_project_of(alice)
    a_layer_of_the_other_project = uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(
        alice, layer_id=the_layer_it_was_surveyed_in, geometry_kind=GeometryKind.POINT
    )
    _an_element_layer_declaring(
        alice,
        layer_id=a_layer_of_the_other_project,
        geometry_kind=GeometryKind.POINT,
        in_project=the_other_project,
    )
    surveyed_from = uuid4()
    _the_server_took(
        browser,
        _a_queue_of(
            _a_feature_create(
                alice,
                layer_id=the_layer_it_was_surveyed_in,
                feature_id=feature_id,
                from_installation=surveyed_from,
                mutation_number=0,
            ),
            _a_geometry_set(
                alice,
                layer_id=the_layer_it_was_surveyed_in,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=surveyed_from,
                mutation_number=1,
            ),
        ),
    )

    set_in_another_project = browser.post(
        OPERATIONS_PATH,
        _a_queue_of(
            _a_geometry_set(
                alice,
                layer_id=a_layer_of_the_other_project,
                feature_id=feature_id,
                at=ANOTHER_PLACE_IN_THE_FIELD,
                from_installation=uuid4(),
                mutation_number=0,
                in_project=the_other_project,
            )
        ),
        JSON,
    )

    assert set_in_another_project.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 0, THE_REASON: NO_FEATURE_AT_THIS_ADDRESS}
    ]
    assert _the_feature_the_projection_holds(alice, feature_id) == AProjectedFeature(
        project_id=alice.project_id,
        layer_id=the_layer_it_was_surveyed_in,
        geometry=_as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD),
    )


def test_a_second_create_in_one_batch_does_not_file_a_surveyed_point_under_a_polygon_layer(
    alice: Party,
) -> None:
    """M2's geometry-family clause, on the half MAP-66 left to this task **within one batch**: no
    stored row pairs a layer and a geometry that no single operation carried. The fold the
    projection writes from keeps the last address each feature was given (ADR-0012 decision 3), so a
    create naming a feature the batch already created, under a layer of another family, filed the
    surveyed point under a polygon layer, which neither the set nor the create had said.

    **The second create is `feature_already_created` by what the batch before it left** (ADR-0014
    decision 7, ADR-0010 decision 6's addition of 2026-09-24), with the tenant holding nothing when
    the flush began, and a refused operation reaches no fold. The refusal list is the control this
    module's docstring gives; the row is compared on the two columns the pairing is about, and it
    being there at all says the flush was applied rather than refused whole."""
    a_point_layer, a_polygon_layer = uuid4(), uuid4()
    feature_id, installation = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=a_point_layer, geometry_kind=GeometryKind.POINT)
    _an_element_layer_declaring(alice, layer_id=a_polygon_layer, geometry_kind=GeometryKind.POLYGON)

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
            _a_geometry_set(
                alice,
                layer_id=a_point_layer,
                feature_id=feature_id,
                at=A_PLACE_IN_THE_FIELD,
                from_installation=installation,
                mutation_number=1,
            ),
            _a_feature_create(
                alice,
                layer_id=a_polygon_layer,
                feature_id=feature_id,
                from_installation=installation,
                mutation_number=2,
            ),
        ),
        JSON,
    )
    held = _the_feature_the_projection_holds(alice, feature_id)

    assert answered.json()[THE_REFUSALS] == [
        {THE_MUTATION_NUMBER_REFUSED: 2, THE_REASON: FEATURE_ALREADY_CREATED}
    ]
    assert (held.layer_id, held.geometry) == (
        a_point_layer,
        _as_the_storage_frame_holds_it(A_PLACE_IN_THE_FIELD),
    )


def test_a_geometry_set_naming_a_feature_nothing_created_is_kept_on_the_log_as_drawn(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24, *retained the same way*: flagged and retained for inspection,
    never discarded, which ADR-0014 decision 3 makes the log, the verdict and the reason as columns
    beside the client half verbatim (M8).

    **The refused operation carries a geometry, and that is why this reason is the one read here.**
    What preserve-not-discard protects is the place surveyed, not the record of a failure (C7), so
    an implementation keeping the identifier, the verdict and the reason while dropping the payload
    is the sin M9's own words name."""
    layer_id, installation, carrying_a_place = uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=layer_id, geometry_kind=GeometryKind.POINT)
    surveyed_in_the_field = _a_geometry_set(
        alice,
        layer_id=layer_id,
        feature_id=uuid4(),
        at=A_PLACE_IN_THE_FIELD,
        operation_id=carrying_a_place,
        from_installation=installation,
        mutation_number=0,
    )

    _the_server_took(browser, _a_queue_of(surveyed_in_the_field))

    assert _what_the_log_keeps_of(alice, carrying_a_place) == WhatTheLogKeeps(
        verdict=REFUSED,
        refusal_reason=NO_FEATURE_AT_THIS_ADDRESS,
        client_half=ClientHalf.model_validate(surveyed_in_the_field),
    )


def test_a_create_naming_a_feature_the_tenant_already_holds_is_kept_on_the_log_with_its_verdict(
    alice: Party,
) -> None:
    """M9's clause of 2026-09-24, *each* refused and retained the same way: the other reason's
    entry, read whole, so a reason missing from what the log can store, or an entry written under
    the verdict it was never given, is red for this reason on its own (ADR-0014 decision 3)."""
    layer_id, feature_id, installation, created_again = uuid4(), uuid4(), uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)
    _an_element_layer_declaring(alice, layer_id=layer_id, geometry_kind=GeometryKind.POINT)
    naming_a_held_feature = _a_feature_create(
        alice,
        layer_id=layer_id,
        feature_id=feature_id,
        operation_id=created_again,
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
            )
        ),
    )

    _the_server_took(browser, _a_queue_of(naming_a_held_feature))

    assert _what_the_log_keeps_of(alice, created_again) == WhatTheLogKeeps(
        verdict=REFUSED,
        refusal_reason=FEATURE_ALREADY_CREATED,
        client_half=ClientHalf.model_validate(naming_a_held_feature),
    )
