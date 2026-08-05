"""A feature's geometry answers to the family its layer declares.

Trace: **D3**, which makes multipart geometry and a ring with an enclave a domain requirement
rather than a nicety, and therefore fixes the shape this rule must take. **The rule's own existence
traces to no requirement** and that half is not settled here: M2 gives a layer a geometry kind and
never says a disagreeing feature is refused. The two roads are written in
`specs/tasks/MAP-5-layers-and-features.md` section 2.1, per `specs/testing.md` section 6.

PostgreSQL cannot express the rule as a check across two tables, so it is a decision over plain
data and it is tested as one (`specs/testing.md` section 3).
"""

import pytest
from django.contrib.gis.geos import (
    GEOSGeometry,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from mapsift.layers.rules import GeometryKind, geometry_is_admissible, geometry_types_of

A_RING = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (0.0, 0.0))
ANOTHER_RING = ((5.0, 5.0), (5.0, 6.0), (6.0, 6.0), (5.0, 5.0))

SIMPLE_GEOMETRY_BY_KIND: dict[GeometryKind, GEOSGeometry] = {
    GeometryKind.POINT: Point(0.0, 0.0),
    GeometryKind.LINE: LineString((0.0, 0.0), (1.0, 1.0)),
    GeometryKind.POLYGON: Polygon(A_RING),
}

MULTIPART_GEOMETRY_BY_KIND: dict[GeometryKind, GEOSGeometry] = {
    GeometryKind.POINT: MultiPoint(Point(0.0, 0.0), Point(1.0, 1.0)),
    GeometryKind.LINE: MultiLineString(
        LineString((0.0, 0.0), (1.0, 1.0)), LineString((5.0, 5.0), (6.0, 6.0))
    ),
    GeometryKind.POLYGON: MultiPolygon(Polygon(A_RING), Polygon(ANOTHER_RING)),
}

TYPES_OF_ANOTHER_FAMILY = [
    (kind, geometry_type)
    for kind in GeometryKind
    for other in GeometryKind
    if other is not kind
    for geometry_type in geometry_types_of(other)
]


@pytest.mark.parametrize(("kind", "geometry"), list(SIMPLE_GEOMETRY_BY_KIND.items()))
def test_a_geometry_of_the_family_the_layer_declares_is_admissible(
    kind: GeometryKind, geometry: GEOSGeometry
) -> None:
    """D3: the type comes off a real geometry rather than a literal, because a rule speaking its
    own dialect of the type names would refuse everything a caller ever hands it."""
    assert geometry_is_admissible(layer_kind=kind, geometry_type=geometry.geom_type) is True


@pytest.mark.parametrize(("kind", "geometry"), list(MULTIPART_GEOMETRY_BY_KIND.items()))
def test_a_multipart_geometry_is_admissible_in_its_own_family(
    kind: GeometryKind, geometry: GEOSGeometry
) -> None:
    """D3: a legal reserve is frequently multi-part, so a rule comparing the declared kind against
    a concrete type by identity would refuse one, which is the whole point of the requirement."""
    assert geometry_is_admissible(layer_kind=kind, geometry_type=geometry.geom_type) is True


def test_a_polygon_with_an_enclave_is_admissible() -> None:
    """D3: the enclave is the second case the requirement names, and it needs no member of its own
    because a ring with a hole is still a polygon."""
    with_enclave = Polygon(
        ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0), (0.0, 0.0)),
        ((2.0, 2.0), (2.0, 3.0), (3.0, 3.0), (3.0, 2.0), (2.0, 2.0)),
    )

    assert geometry_is_admissible(
        layer_kind=GeometryKind.POLYGON, geometry_type=with_enclave.geom_type
    )


@pytest.mark.parametrize(("layer_kind", "geometry_type"), TYPES_OF_ANOTHER_FAMILY)
def test_a_geometry_of_another_family_is_not_admissible(
    layer_kind: GeometryKind, geometry_type: str
) -> None:
    """Every disagreeing pair is enumerated from the closed set rather than listed, so a kind added
    later is checked against every type of every other family without this test being edited."""
    assert geometry_is_admissible(layer_kind=layer_kind, geometry_type=geometry_type) is False


def test_every_geometry_kind_declares_the_types_of_its_family() -> None:
    """The set of kinds is closed and each member's types are decided, so one added to the
    enumeration later fails here rather than passing on an empty family that admits nothing."""
    families = {kind: geometry_types_of(kind) for kind in GeometryKind}

    assert all(families.values())
