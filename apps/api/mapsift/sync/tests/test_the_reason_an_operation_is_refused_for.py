"""Which reason a layer's declarations refuse an operation for, if any, decided over plain data.

Trace: **ADR-0010 decision 6's addition of 2026-09-23** for the order that picks one reason and for
the scope of the family check; PRD **M2** (the storage class and the geometry family are the
layer's declarations, and an operation is judged against the layer it addresses); **M9**'s final
acceptance clause for the refusal the family check makes; **ADR-0014 decisions 1 and 7** for the
verdict being one operation's and a pure decision taken before anything is written. I2; C7.

**Pure because the decision is pure, and here because the route cannot carry these cases inside
this task's scope.** A payload this rule reads no family out of answers `500` at the writer, which
is MAP-70's to change, so a route case over one pins what that issue owns; a geometry set on a
served layer reaches the route either for a feature no applied operation created, the shape
ADR-0014 decision 7 leaves open, or addressed at a layer other than the one its feature is filed
under, a feature changing path, which M2's fourth acceptance clause governs and MAP-66's task spec
keeps out of scope; and which declarations the rule reads is invisible at the route while its one
caller hands it exactly the layers the batch names. Every case the route carries inside that scope
is in `tests/test_the_layer_declaration_refusals.py`.

The reasons are spelled as literals rather than read off `WhyAnOperationWasRefused`, on this suite's
rule for a wire value: a case comparing an enum against itself cannot notice a member being renamed.
"""

from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from conftest import JsonObject, a_feature_create_claiming, a_geometry_set_claiming
from mapsift.layers.rules import GeometryKind, StorageClass, TheDeclarationsOfALayer
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import TheRefusalOfAnOperation, the_refusals_this_batch_earns

SERVED_LAYER_TAKES_NO_OPERATIONS = "served_layer_takes_no_operations"
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

    Here rather than through the route because each route arrangement of it rests on a shape this
    task does not own: a geometry set for a feature no applied operation created, which ADR-0014
    decision 7 declines to decide, or one addressed at a layer other than the one its feature is
    filed under, a feature changing path (M2's fourth acceptance clause) that MAP-66's task spec
    keeps out of scope."""
    a_served_point_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_served_point_layer, carrying=A_PARCEL, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_served_point_layer: A_SERVED_POINT_LAYER},
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
    unreadable type as foreign refuses."""
    a_polygon_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_polygon_layer, carrying=unreadable, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_polygon_layer: AN_ELEMENT_POLYGON_LAYER},
    )

    assert _the_reasons_given(refusals) == []


def test_a_geometry_declaring_a_type_of_its_layers_family_is_admitted_on_that_alone() -> None:
    """ADR-0010 decision 6's addition of 2026-09-23: the family is read from the payload's own
    declared `type`, **without parsing the geometry**. The quiet side of that clause.

    **The payload declares a point and carries no coordinates**, which no geometry library parses,
    so a rule that reads the family by parsing raises here or refuses what it could not read, and
    only a rule reading the declared type alone answers that a point is inside the point family."""
    a_point_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_point_layer, carrying={"type": "Point"}, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
    )

    assert _the_reasons_given(refusals) == []


def test_a_geometry_declaring_a_type_outside_its_layers_family_is_refused_on_that_alone() -> None:
    """The same clause's other side: a declared type outside the family is refused on the type,
    whatever else the payload carries or lacks (M2, M9).

    **A declared polygon with no coordinates, on a point layer**, so a rule that skips whatever it
    cannot parse lets it through, and the sibling above cannot tell that rule apart from this."""
    a_point_layer = uuid4()

    refusals = the_refusals_this_batch_earns(
        _as_authored(
            _a_geometry_set_on(
                a_point_layer, carrying={"type": "Polygon"}, feature_id=uuid4(), mutation_number=0
            )
        ),
        layers_the_project_holds={a_point_layer: AN_ELEMENT_POINT_LAYER},
    )

    assert _the_reasons_given(refusals) == [(0, GEOMETRY_OUTSIDE_THE_LAYERS_FAMILY)]
