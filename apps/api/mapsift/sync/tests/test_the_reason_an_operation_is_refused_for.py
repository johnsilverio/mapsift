"""Which reason an operation is refused for, if any, decided over plain data.

Trace: **ADR-0010 decision 6's addition of 2026-09-23** for the order that picks one reason and for
the scope of the family check, and **its addition of 2026-09-24** for the two reasons about the
feature an operation names, the place they take in that order, and what the operations before one
in the same batch contribute to what the tenant holds; PRD **M2** (the storage class and the
geometry family are the layer's declarations, and an operation is judged against the layer it
addresses); **M9**'s final acceptance clause for the refusal the family check makes, and the clause
it gained on 2026-09-24 for the refusals about the feature; **ADR-0014 decisions 1 and 7**, with
decision 7's addition of 2026-09-24, for the verdict being one operation's, a pure decision taken
before anything is written, and each operation being judged against what the **applied**
operations before it leave. I2, I3; C7.

**Pure because the decision is pure, and here for what the route cannot carry or cannot see.** A
payload this rule reads no family out of answers `500` at the writer, which is MAP-70's to change,
so a route case over one pins what that issue owns; which declarations the rule reads is invisible
at the route while its one caller hands it exactly the layers the batch names; and the order among
five reasons, with what a batch contributes to what the tenant holds, is a decision over plain data
whose every arm a route case would reach through a database arrangement it adds nothing to. Every
case the route carries for the layer's declarations is in
`tests/test_the_layer_declaration_refusals.py`, and every one for the feature an operation names is
in `tests/test_the_feature_an_operation_names.py`.

**What the tenant holds is handed to the rule rather than read by it**, and a case below that hands
it nothing is saying the tenant holds no feature at all, which is the state every batch in this
module starts from unless it says otherwise.

The reasons are spelled as literals rather than read off `WhyAnOperationWasRefused`, on this suite's
rule for a wire value: a case comparing an enum against itself cannot notice a member being renamed.
"""

from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from conftest import JsonObject, a_feature_create_claiming, a_geometry_set_claiming
from mapsift.layers.rules import (
    GeometryKind,
    StorageClass,
    TheDeclarationsOfALayer,
    WhereAFeatureIsFiled,
)
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import TheRefusalOfAnOperation, the_refusals_this_batch_earns

NO_LAYER_IN_THIS_PROJECT = "no_layer_in_this_project"
SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
FEATURE_ALREADY_CREATED = "feature_already_created"
NO_FEATURE_AT_THIS_ADDRESS = "no_feature_at_this_address"
GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY = "geometry_outside_the_layers_family"

AN_ELEMENT_POINT_LAYER = TheDeclarationsOfALayer(
    storage_class=StorageClass.ELEMENT, geometry_kind=GeometryKind.POINT
)
AN_ELEMENT_POLYGON_LAYER = TheDeclarationsOfALayer(
    storage_class=StorageClass.ELEMENT, geometry_kind=GeometryKind.POLYGON
)
A_SERVED_POINT_LAYER = TheDeclarationsOfALayer(
    storage_class=StorageClass.SERVED, geometry_kind=GeometryKind.POINT
)

A_POINT_SURVEYED_IN_THE_FIELD: JsonObject = {"type": "Point", "coordinates": [-47.6, -15.9]}
A_PARCEL: JsonObject = {
    "type": "Polygon",
    "coordinates": [
        [[-47.6, -15.9], [-47.5, -15.9], [-47.5, -15.8], [-47.6, -15.8], [-47.6, -15.9]]
    ],
}

# One installation's stream in one project of one tenant, which is all a batch reaching this rule
# can be: the composition rules refuse anything else before it (ADR-0010 decision 6).
A_TENANT, A_PROJECT, AN_INSTALLATION = uuid4(), uuid4(), uuid4()


def _as_authored(*operations: JsonObject) -> list[ClientHalf]:
    """The batch as the generated reader sees it, which is what the rule decides over (M8)."""
    return [ClientHalf.model_validate(operation) for operation in operations]


def _a_create_on(layer_id: UUID, *, feature_id: UUID, mutation_number: int) -> JsonObject:
    """The catalog's create, addressed at one layer, which carries no geometry at all (M9)."""
    return a_feature_create_claiming(
        A_TENANT,
        client_id=AN_INSTALLATION,
        mutation_number=mutation_number,
        project_id=A_PROJECT,
        layer_id=layer_id,
        feature_id=feature_id,
    )


def _a_geometry_set_on(
    layer_id: UUID, *, carrying: object, feature_id: UUID, mutation_number: int
) -> JsonObject:
    """The catalog's geometry set, its payload replaced whole by whatever a case is about (M9).

    `object` rather than a mapping, because one payload below is not a mapping at all, which a
    mapping type would refuse to state, and the envelope declares the field opaque.
    """
    return {
        **a_geometry_set_claiming(
            A_TENANT,
            client_id=AN_INSTALLATION,
            mutation_number=mutation_number,
            project_id=A_PROJECT,
            layer_id=layer_id,
            feature_id=feature_id,
        ),
        "payload": {"geometry": carrying},
    }


def _the_reasons_given(refusals: Sequence[TheRefusalOfAnOperation]) -> list[tuple[int, str]]:
    """Each refusal as the mutation number it names and the reason it gives, in the order given.

    The pair the wire carries per refused operation (ADR-0010 decision 6's addition of 2026-09-17),
    with the reason read as its value so the literal it is compared against is the wire's.
    """
    return [(refusal.mutation_number, str(refusal.reason)) for refusal in refusals]


def test_a_served_layer_carrying_a_geometry_of_another_family_is_refused_for_its_class() -> None:
    """ADR-0010 decision 6's addition of 2026-09-23, on the one position in its order it calls a
    choice rather than forced: a served layer takes no operations at all (M2), so whether a
    geometry fits its family is a question never reached, and the one reason carried is the class.

    **The feature is one the tenant does not hold, and since 2026-09-24 that is a third reason this
    operation earns.** The addition of that date puts the class ahead of both reasons about the
    feature, walking M9's target path from the layer to the feature, so the one reason carried is
    still the class, and this is where that position is pinned. A feature the tenant **does** hold
    at a served layer, which an import rather than an operation puts there (ADR-0012 decision 6),
    fails the class alone, and the case after this one is that arm."""
    a_served_point_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_served_point_layer, carrying=A_PARCEL, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_served_point_layer: A_SERVED_POINT_LAYER},
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [(0, SERVED_LAYER_TAKES_NO_OPERATIONS)]


def test_a_geometry_set_on_a_feature_held_at_a_served_layer_is_refused_for_its_class() -> None:
    """M2's served-versus-element clause on the arm where the class is the **only** rule an
    operation fails: `layers_feature` holds import-derived features of a served layer beside the
    log-derived ones (ADR-0012 decision 6 and its Consequences), and that table is where what a
    tenant holds is read from (ADR-0010 decision 6's addition of 2026-09-24), so a geometry set can
    name a feature the tenant holds at exactly the served layer it names.

    **Held at that address, the feature reasons admit it**, so only the class stands between this
    operation and a served feature entering the operation queue. A rule that asks the layer's class
    only of an operation whose feature it does not already hold at its address, on the reading that
    a held feature was created through the queue and its layer must be an element layer, admits it
    here, and the case above cannot see that rule, its feature being held nowhere."""
    a_served_point_layer, imported_feature = uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_served_point_layer,
                carrying=A_POINT_SURVEYED_IN_THE_FIELD,
                feature_id=imported_feature,
                mutation_number=0,
            )
        ),
        layers_the_project_holds={a_served_point_layer: A_SERVED_POINT_LAYER},
        features_the_tenant_holds={
            imported_feature: WhereAFeatureIsFiled(
                project_id=A_PROJECT, layer_id=a_served_point_layer
            )
        },
    )

    assert _the_reasons_given(refusals) == [(0, SERVED_LAYER_TAKES_NO_OPERATIONS)]


def test_an_operation_is_judged_by_the_declarations_of_its_own_layer_and_no_other() -> None:
    """M2: the class and the family are properties of **the** layer, so an operation is measured
    against the one it names. The quiet side, and one MAP-66's task spec hands over under its
    Evidence as found unwitnessed at review: a served-layer check that walked every layer it was
    handed, correct only because its one caller handed it exactly the layers the batch named.

    **The rule is handed more than the batch addresses, and that is the whole arrangement.** A
    polygon layer and a served layer sit ahead of the point layer both operations address, so a rule
    reading any declaration but the addressed layer's refuses one of them."""
    a_polygon_layer, a_served_layer, the_point_layer_addressed = uuid4(), uuid4(), uuid4()
    feature_id = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(the_point_layer_addressed, feature_id=feature_id, mutation_number=0),
            _a_geometry_set_on(
                the_point_layer_addressed,
                carrying=A_POINT_SURVEYED_IN_THE_FIELD,
                feature_id=feature_id,
                mutation_number=1,
            ),
        ),
        layers_the_project_holds={
            a_polygon_layer: AN_ELEMENT_POLYGON_LAYER,
            a_served_layer: A_SERVED_POINT_LAYER,
            the_point_layer_addressed: AN_ELEMENT_POINT_LAYER,
        },
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == []


@pytest.mark.parametrize(
    "unreadable",
    [
        pytest.param("POINT (-47.6 -15.9)", id="not-a-mapping"),
        pytest.param({"coordinates": [-47.6, -15.9]}, id="no-type"),
        pytest.param({"type": 7, "coordinates": [-47.6, -15.9]}, id="a-type-that-is-not-a-string"),
    ],
)
def test_a_geometry_whose_family_cannot_be_read_off_it_is_not_checked_for_one(
    unreadable: object,
) -> None:
    """ADR-0010 decision 6's addition of 2026-09-23 on the scope it calls contract rather than
    detail: a payload the rule cannot read a family out of is not checked for family at all, since
    what those payloads do is MAP-70's and a refusal firing on what it cannot read decides a
    question that issue owns. MAP-66's task spec hands over, under its Evidence, that these three
    shapes were once skipped with no case pinning them.

    **On a polygon layer, where each of them would be outside the family if it were read as a
    point**, so a rule that indexes into the payload raises here and one that reads an absent or
    unreadable type as foreign refuses.

    **The feature is one the tenant holds at that layer**, re-arranged at MAP-68: a set naming a
    feature nobody holds earns `no_feature_at_this_address`, which the order of ADR-0010 decision
    6's addition of 2026-09-24 puts ahead of the family, so without the holding this case would be
    answered by the address and would stop asking the question it is about."""
    a_polygon_layer, feature_id = uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_polygon_layer, carrying=unreadable, feature_id=feature_id, mutation_number=0
            )
        ),
        layers_the_project_holds={a_polygon_layer: AN_ELEMENT_POLYGON_LAYER},
        features_the_tenant_holds={
            feature_id: WhereAFeatureIsFiled(project_id=A_PROJECT, layer_id=a_polygon_layer)
        },
    )

    assert _the_reasons_given(refusals) == []


def test_a_geometry_declaring_a_type_of_its_layers_family_is_admitted_on_that_alone() -> None:
    """ADR-0010 decision 6's addition of 2026-09-23: the family is read from the payload's own
    declared `type`, **without parsing the geometry**. The quiet side of that clause.

    **The payload declares a point and carries no coordinates**, which no geometry library parses,
    so a rule that reads the family by parsing raises here or refuses what it could not read, and
    only a rule reading the declared type alone answers that a point is inside the point family.

    **The feature is one the tenant holds at that layer**, for the reason the case above gives: held
    nowhere, it would be refused for its address before its family was asked about."""
    a_point_layer, feature_id = uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_point_layer, carrying={"type": "Point"}, feature_id=feature_id, mutation_number=0
            )
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={
            feature_id: WhereAFeatureIsFiled(project_id=A_PROJECT, layer_id=a_point_layer)
        },
    )

    assert _the_reasons_given(refusals) == []


def test_a_geometry_declaring_a_type_outside_its_layers_family_is_refused_on_that_alone() -> None:
    """The same clause's other side: a declared type outside the family is refused on the type,
    whatever else the payload carries or lacks (M2, M9).

    **A declared polygon with no coordinates, on a point layer**, so a rule that skips whatever it
    cannot parse lets it through, and the sibling above cannot tell that rule apart from this.

    **The feature is one the tenant holds at that layer**, for the reason the cases above give, and
    here it is what keeps the reason the family's: held nowhere, this operation is refused for its
    address instead."""
    a_point_layer, feature_id = uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_point_layer,
                carrying={"type": "Polygon"},
                feature_id=feature_id,
                mutation_number=0,
            )
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={
            feature_id: WhereAFeatureIsFiled(project_id=A_PROJECT, layer_id=a_point_layer)
        },
    )

    assert _the_reasons_given(refusals) == [(0, GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY)]


def test_a_create_naming_a_held_feature_on_a_layer_the_project_lacks_is_refused_for_the_layer() -> (
    None
):
    """ADR-0010 decision 6's addition of 2026-09-24, on the first position of the order it fixes:
    `no_layer_in_this_project`, then the class, then `feature_already_created`. The position is
    forced rather than chosen, because M9's target path is walked from its coarsest segment, and a
    layer the project does not hold is decided before anything about the feature filed under it.

    **The feature is one the tenant holds, so this create fails two rules**, and a rule that asks
    about the feature before the layer answers `feature_already_created` here."""
    a_layer_the_project_lacks, the_layer_it_is_filed_under, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(a_layer_the_project_lacks, feature_id=feature_id, mutation_number=0)
        ),
        layers_the_project_holds={the_layer_it_is_filed_under: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={
            feature_id: WhereAFeatureIsFiled(
                project_id=A_PROJECT, layer_id=the_layer_it_is_filed_under
            )
        },
    )

    assert _the_reasons_given(refusals) == [(0, NO_LAYER_IN_THIS_PROJECT)]


def test_a_create_naming_a_held_feature_on_a_served_layer_is_refused_for_its_class() -> None:
    """ADR-0010 decision 6's addition of 2026-09-24, on the second position: the storage class is
    the layer's, so it is decided before the feature the operation names, and a served layer takes
    no operations at all (M2) whatever the tenant already holds.

    **The feature is one the tenant holds elsewhere, so this create fails two rules**, and a rule
    that asks about the feature before the class answers `feature_already_created` here."""
    a_served_layer, the_layer_it_is_filed_under, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(_a_create_on(a_served_layer, feature_id=feature_id, mutation_number=0)),
        layers_the_project_holds={
            a_served_layer: A_SERVED_POINT_LAYER,
            the_layer_it_is_filed_under: AN_ELEMENT_POINT_LAYER,
        },
        features_the_tenant_holds={
            feature_id: WhereAFeatureIsFiled(
                project_id=A_PROJECT, layer_id=the_layer_it_is_filed_under
            )
        },
    )

    assert _the_reasons_given(refusals) == [(0, SERVED_LAYER_TAKES_NO_OPERATIONS)]


def test_a_geometry_set_naming_no_held_feature_is_refused_for_its_address_before_its_family() -> (
    None
):
    """ADR-0010 decision 6's addition of 2026-09-24, on the last two positions: the feature before
    the property whose payload the family check reads, so `no_feature_at_this_address` comes ahead
    of `geometry_outside_the_layers_family`.

    **A parcel on a point layer, for a feature nobody holds**, so the operation fails both rules and
    a rule that reads the payload before the address answers with the family."""
    a_point_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_point_layer, carrying=A_PARCEL, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [(0, NO_FEATURE_AT_THIS_ADDRESS)]


def test_a_second_create_of_a_feature_the_batch_already_created_is_refused_as_already_created() -> (
    None
):
    """ADR-0014 decision 7 with ADR-0010 decision 6's addition of 2026-09-24: what the tenant holds
    includes what the operations before one in the same batch leave, so a create applied earlier in
    the batch makes a second create of that feature `feature_already_created`, under whatever layer
    it names.

    **The tenant holds nothing when the batch starts**, so a rule reading only what it was handed
    admits both creates, and the first create being admitted is the quiet side beside it."""
    the_layer_it_is_created_in, a_second_layer, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(the_layer_it_is_created_in, feature_id=feature_id, mutation_number=0),
            _a_create_on(a_second_layer, feature_id=feature_id, mutation_number=1),
        ),
        layers_the_project_holds={
            the_layer_it_is_created_in: AN_ELEMENT_POINT_LAYER,
            a_second_layer: AN_ELEMENT_POINT_LAYER,
        },
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [(1, FEATURE_ALREADY_CREATED)]


def test_an_operation_naming_a_feature_the_batch_filed_under_another_layer_is_refused() -> None:
    """ADR-0010 decision 6's addition of 2026-09-24: a create applied earlier in the batch makes a
    later operation naming that feature at the same address admissible, **while one naming it at
    another layer is `no_feature_at_this_address`**, because the create filed it under exactly one
    layer (M2) and the batch's contribution is that filing, not the bare identifier.

    The quiet side, the same address admitted, is
    `test_an_operation_is_judged_by_the_declarations_of_its_own_layer_and_no_other` above, whose
    geometry set follows its feature's create in one batch with the tenant holding nothing."""
    the_layer_it_is_created_in, another_layer, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(the_layer_it_is_created_in, feature_id=feature_id, mutation_number=0),
            _a_geometry_set_on(
                another_layer,
                carrying=A_POINT_SURVEYED_IN_THE_FIELD,
                feature_id=feature_id,
                mutation_number=1,
            ),
        ),
        layers_the_project_holds={
            the_layer_it_is_created_in: AN_ELEMENT_POINT_LAYER,
            another_layer: AN_ELEMENT_POINT_LAYER,
        },
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [(1, NO_FEATURE_AT_THIS_ADDRESS)]


def test_an_operation_after_a_refused_create_is_refused_for_its_own_address_not_by_cascade() -> (
    None
):
    """ADR-0014 decision 7's addition of 2026-09-24 with ADR-0010 decision 6's of the same date: a
    create refused earlier in the batch leaves nothing held, so an operation other than a create
    after it on that feature is `no_feature_at_this_address` **in its own right rather than by
    cascade**, and nothing is refused for being downstream of a refusal.

    **The geometry set names a layer the project holds**, so its only fault is the feature the
    refused create never filed, and a rule that cascades gives it the create's reason instead.

    What a refused create leaves for a second create of the same feature is the case after this
    one."""
    a_layer_the_project_lacks, a_point_layer, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(a_layer_the_project_lacks, feature_id=feature_id, mutation_number=0),
            _a_geometry_set_on(
                a_point_layer,
                carrying=A_POINT_SURVEYED_IN_THE_FIELD,
                feature_id=feature_id,
                mutation_number=1,
            ),
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [
        (0, NO_LAYER_IN_THIS_PROJECT),
        (1, NO_FEATURE_AT_THIS_ADDRESS),
    ]


def test_a_create_after_a_refused_create_of_the_same_feature_is_admitted() -> None:
    """ADR-0010 decision 6's addition of 2026-09-24 as sharpened at that day's pre-dispatch read,
    with ADR-0014 decision 7's addition: a create refused earlier in the batch leaves nothing held,
    so a second create of that feature is judged like any create and, nothing being held, is
    admitted rather than refused `feature_already_created`.

    **The first create names a layer the project lacks and the second one it holds**, so the second
    has nothing wrong with it but what a rule counting a refused create as a filing would invent,
    and that rule answers two refusals where the batch earns one."""
    a_layer_the_project_lacks, a_point_layer, feature_id = uuid4(), uuid4(), uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_create_on(a_layer_the_project_lacks, feature_id=feature_id, mutation_number=0),
            _a_create_on(a_point_layer, feature_id=feature_id, mutation_number=1),
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
        features_the_tenant_holds={},
    )

    assert _the_reasons_given(refusals) == [(0, NO_LAYER_IN_THIS_PROJECT)]
