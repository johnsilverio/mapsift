"""The writes `layers` publishes (ADR-0007 section 3)."""

from uuid import UUID

from mapsift.layers.models import Layer
from mapsift.layers.rules import GeometryKind, StorageClass


def create_layer(
    *,
    layer_id: UUID,
    tenant_id: UUID,
    project_id: UUID,
    name: str,
    geometry_kind: GeometryKind,
    storage_class: StorageClass,
) -> Layer:
    """Create a layer inside an existing project of the tenant in force (PRD C1, M2, M3).

    Requires a tenant binding and opens none; a `tenant_id` other than the bound one is refused by
    the policy rather than stored (ADR-0005 sections 3 and 4).
    """
    raise NotImplementedError
