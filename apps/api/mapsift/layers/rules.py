"""The two decisions a layer's declarations make about its features (M2), and the shape one
feature's current state crosses into this package in (M15)."""

from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never
from uuid import UUID


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


@dataclass(frozen=True, slots=True)
class TheCurrentStateOfAFeature:
    """One feature as the operations addressing it leave it, in plain data (M15, M9).

    Its geometry is the wire structure an operation carried and not a stored geometry: the frame
    is applied where it is written (M5 rule 1). A batch that spoke of the geometry says so
    separately from what it said, because saying nothing and saying null are different statements
    and only one of them touches the stored column (ADR-0012 decision 3's addition of 2026-09-09).
    """

    tenant_id: UUID
    project_id: UUID
    layer_id: UUID
    feature_id: UUID
    geometry: object | None
    the_batch_spoke_of_its_geometry: bool
