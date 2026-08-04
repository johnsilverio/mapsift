"""The two decisions a layer's declarations make about its features (M2).

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
    """The one kind of geometry a layer declares, and therefore the one its features carry (M2)."""

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


def geometry_is_admissible(*, layer_kind: GeometryKind, feature_kind: GeometryKind) -> bool:
    """Whether geometry of this kind may be stored in a layer declaring that one (M2)."""
    return layer_kind is feature_kind
