"""The two decisions a layer's declarations make about its features, and both are M2's."""

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
    # A member added later lands here and fails the type check until somebody decides its side of
    # the frontier, which a fallback return would decide for them.
    assert_never(storage_class)


def geometry_types_of(kind: GeometryKind) -> frozenset[str]:
    """The concrete types belonging to a family, spelled as GEOS's `geom_type` spells them (D3)."""
    match kind:
        case GeometryKind.POINT:
            return frozenset({"Point", "MultiPoint"})
        case GeometryKind.LINE:
            return frozenset({"LineString", "MultiLineString"})
        case GeometryKind.POLYGON:
            return frozenset({"Polygon", "MultiPolygon"})
    # A member added later lands here and fails the type check until somebody decides its types,
    # which a fallback would decide for them.
    assert_never(kind)


def geometry_is_admissible(*, layer_kind: GeometryKind, geometry_type: str) -> bool:
    """Whether a geometry of this concrete type belongs to the family a layer declares (M2)."""
    # False is not a licence to drop the operation carrying it: M9 makes the refusal a typed error
    # that flags and retains, because that geometry was drawn offline in the field.
    return geometry_type in geometry_types_of(layer_kind)
