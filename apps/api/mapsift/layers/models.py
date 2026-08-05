"""The layer and the feature (M2).

Neither carries an identifier default, unlike the user beside them, because the client that draws a
feature offline is its allocator (ADR-0006 section 3).
"""

from enum import StrEnum
from typing import ClassVar

from django.contrib.gis.db import models

from mapsift.common.binding import TenantOwnedManager
from mapsift.common.geometry import StorageFrameGeometryField
from mapsift.layers.rules import GeometryKind, StorageClass


def _labelled(enumeration: type[StrEnum]) -> dict[str, str]:
    """Django's `choices` from an enumeration that may not import it (ADR-0007 section 3)."""
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
            # Three columns rather than two, and nothing declared beside it: both are corrections
            # dated 2026-08-04 in this task's spec, section 3 (ADR-0005 section 5).
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
    # Null until the second operation of this slice's catalog sets it (foundation OQ-4). The index
    # is a plain GiST against the ADR-0005 section 5 rule that a tenant-scoped index leads with the
    # tenant, and the measured condition that flips it is in this task's spec, section 3.
    geometry = StorageFrameGeometryField(null=True, spatial_index=True)

    objects = TenantOwnedManager["Feature"]()

    class Meta:
        indexes: ClassVar[list[models.Index]] = [
            # The column order is not interchangeable: the tenant leads (ADR-0005 section 5).
            models.Index(fields=["tenant", "layer"], name="feature_layer_by_tenant")
        ]
