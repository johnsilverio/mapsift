"""The two decisions a layer's declarations make about its features.

The storage class deciding the path is M2's. The admissibility rule below carries **no requirement
of its own**: M2 gives a layer a geometry kind and never says a feature disagreeing with it is
refused, so whether Mapsift requires that at all is open, and is recorded with the two roads in
`specs/tasks/MAP-5-layers-and-features.md` section 2.1. What D3 does decide is the shape the rule
must take if it exists, and that half is closed here.

Pure over plain data, so neither one can reach the operation queue it answers for: the queue is an
effect and MAP-7 onwards owns it, while the rule underneath it is owed today (ADR-0007 section 3,
`specs/testing.md` section 3).
"""

from enum import StrEnum
from typing import assert_never


class StorageClass(StrEnum):
    """Which side of the elements-and-layers frontier a layer sits on (M2, foundation section 3)."""

    ELEMENT = "element"
    SERVED = "served"


class GeometryKind(StrEnum):
    """The one family of geometry a layer declares, and therefore the one its features carry (M2).

    A family rather than a concrete type, because multipart geometry and a ring with an enclave are
    a domain requirement rather than a luxury (D3).
    """

    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"


def enters_the_operation_queue(storage_class: StorageClass) -> bool:
    """Whether a feature of a layer of this class is carried by the operation queue (M2, C1)."""
    match storage_class:
        case StorageClass.ELEMENT:
            return True
        case StorageClass.SERVED:
            return False
    # A class added to the enumeration lands here, and the type checker refuses the build until
    # somebody decides its side of the frontier. A fallback return would answer for them.
    assert_never(storage_class)


def geometry_types_of(kind: GeometryKind) -> frozenset[str]:
    """The concrete geometry types that belong to a family, named as GEOS's `geom_type` names them.

    Multipart is inside the family (D3), and a ring with an enclave needs no member of its own
    because it is still a polygon.
    """
    match kind:
        case GeometryKind.POINT:
            return frozenset({"Point", "MultiPoint"})
        case GeometryKind.LINE:
            return frozenset({"LineString", "MultiLineString"})
        case GeometryKind.POLYGON:
            return frozenset({"Polygon", "MultiPolygon"})
    # A kind added to the enumeration lands here, and the type checker refuses the build until
    # somebody decides which concrete types belong to it. A fallback would answer for them.
    assert_never(kind)


def geometry_is_admissible(*, layer_kind: GeometryKind, geometry_type: str) -> bool:
    """Whether a geometry of this concrete type belongs to the family a layer declares.

    Comparing the declared kind against a concrete type by identity would refuse a legal reserve,
    which is frequently multi-part or carries an enclave (D3).
    """
    return geometry_type in geometry_types_of(layer_kind)
