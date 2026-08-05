"""The one frame stored geometry is in, and the column that refuses to convert into it (M5 rule 1).

Tier 0 rather than the layers package's, because every geometry column this product ever adds owes
the same guarantee (ADR-0007 section 1).
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.geos import GEOSGeometry
from django.db.backends.base.base import BaseDatabaseWrapper

# M5 rule 1: SIRGAS 2000, the one frame geometry is stored and interchanged in.
STORAGE_FRAME_SRID = 4674

if TYPE_CHECKING:
    # A field is generic to the type checker and a plain class at runtime: django-stubs declares
    # the parameters in a stub and Django's own field cannot be subscripted, so writing the base
    # out once is what keeps the stored and returned types real rather than `Any` (C5). The
    # optional is the plugin's requirement for a column that may be null, which is every geometry
    # column this product has so far.
    _GeometryColumn = GeometryField[GEOSGeometry | None, GEOSGeometry | None]
else:
    _GeometryColumn = GeometryField


class ForeignFrame(Exception):
    """Raised instead of converting a geometry that arrived in some other frame."""


class StorageFrameGeometryField(_GeometryColumn):
    """A geometry column in the storage frame, which stores what it was given or refuses it.

    Guarantees that no write converts a coordinate on its way in (M5 rules 1 and 3). Measured on
    2026-08-04: the plain field wraps a value whose SRID differs in `ST_Transform`, so a parcel sent
    in EPSG:31983 lands as degrees with its source frame gone before anything could record it.

    The two `Any` below are the framework's own hook signatures rather than a choice: a field takes
    heterogeneous keyword arguments, and what reaches the save path may be a geometry or an
    expression standing in for one.
    """

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        kwargs["srid"] = STORAGE_FRAME_SRID
        super().__init__(**kwargs)

    def deconstruct(self) -> tuple[str, str, Sequence[Any], dict[str, Any]]:
        name, path, args, kwargs = super().deconstruct()
        # Dropped rather than emitted, so a migration cannot read as though the frame were a knob.
        kwargs.pop("srid", None)
        return name, path, args, kwargs

    def get_db_prep_save(self, value: Any, connection: BaseDatabaseWrapper) -> Any:  # noqa: ANN401
        frame = getattr(value, "srid", None)
        if frame is not None and frame != STORAGE_FRAME_SRID:
            raise ForeignFrame(
                f"A geometry declared in EPSG:{frame} reached storage, whose frame is "
                f"EPSG:{STORAGE_FRAME_SRID} (M5 rule 1). Transformation into the storage frame is "
                "an import-time decision that records the source frame (M5 rules 1 and 3), never "
                "something a save does on the way past."
            )
        return super().get_db_prep_save(value, connection)
