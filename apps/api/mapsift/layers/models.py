"""The layer and the feature (M2), the two shapes every operation of milestones 2 and 3 addresses.

Both carry the tenant identifier, which is what puts them inside the wall and into the catalogue
the N2 suite enumerates (ADR-0005 sections 3 and 7). Neither carries an identifier default, because
the client that draws a feature offline is its allocator (ADR-0006 section 3).
"""

from enum import StrEnum
from typing import ClassVar

from django.contrib.gis.db import models

from mapsift.common.binding import TenantOwnedManager
from mapsift.layers.rules import GeometryKind, StorageClass

# M5 rule 1: SIRGAS 2000, the one frame geometry is stored and interchanged in.
STORAGE_FRAME_SRID = 4674


def _labelled(enumeration: type[StrEnum]) -> dict[str, str]:
    """Django's `choices` from a framework-free enumeration.

    The enumerations live in `rules.py`, which may not import Django (ADR-0007 section 3), so there
    is no `TextChoices` here to read a `.choices` off.
    """
    return {member.value: member.name.capitalize() for member in enumeration}


class Layer(models.Model):
    """The structure a feature hangs from, and the storage class that decides its path (M2)."""

    id = models.UUIDField(primary_key=True, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant", on_delete=models.CASCADE, related_name="layers", db_index=False
    )
    # The database gets a composite reference from the migration instead, because a single-column
    # one crosses tenants (ADR-0005 section 5, probes H and N).
    project = models.ForeignKey(
        "accounts.Project",
        on_delete=models.CASCADE,
        related_name="layers",
        db_constraint=False,
        db_index=False,
    )
    name = models.CharField(max_length=200)
    geometry_kind = models.CharField(max_length=32, choices=_labelled(GeometryKind))
    storage_class = models.CharField(max_length=32, choices=_labelled(StorageClass))

    objects = TenantOwnedManager["Layer"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            # Three columns rather than two: it is what the feature's reference points at, and a
            # two-column one would leave a feature resolving to its own project and its layer's
            # (ADR-0005 section 5). The tenant leads, and the leading columns serve every
            # tenant-scoped read of this table, so no further index is declared beside it.
            models.UniqueConstraint(
                fields=["tenant", "project", "id"],
                name="layer_identity_within_its_tenant_and_project",
            )
        ]


class Feature(models.Model):
    """One geometry in exactly one layer, one project and one tenant (M2).

    It declares no storage class of its own: the class is the layer's, so the path cannot drift
    feature by feature.
    """

    id = models.UUIDField(primary_key=True, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant", on_delete=models.CASCADE, related_name="features", db_index=False
    )
    project = models.ForeignKey(
        "accounts.Project",
        on_delete=models.CASCADE,
        related_name="features",
        db_constraint=False,
        db_index=False,
    )
    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="features",
        db_constraint=False,
        db_index=False,
    )
    # Nullable because this slice's operation catalog is create a feature and then set its geometry
    # (foundation OQ-4), so the interval between the two has to be representable. The spatial index
    # is a plain GiST rather than a composite led by the tenant, which is a decision and not the
    # default it looks like: the composite would need btree_gist and a query nobody has written.
    geometry = models.GeometryField(srid=STORAGE_FRAME_SRID, null=True, spatial_index=True)

    objects = TenantOwnedManager["Feature"]()

    class Meta:
        indexes: ClassVar[list[models.Index]] = [
            # The column order is not interchangeable: the tenant leads (ADR-0005 section 5).
            models.Index(fields=["tenant", "layer"], name="feature_layer_by_tenant")
        ]
