"""The writes `layers` publishes (ADR-0007 section 3)."""

import json
from collections.abc import Sequence
from uuid import UUID

from django.contrib.gis.geos import GEOSGeometry
from django.db import connection

from mapsift.common.geometry import STORAGE_FRAME_SRID
from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import GeometryKind, StorageClass, TheCurrentStateOfAFeature

# Raw rather than `bulk_create`, whose Django 5.2.16 postgres backend emits a fixed
# `field = EXCLUDED.field` for every updated column and can express neither of the two clauses
# below. The cost is the manager's guard: an unbound write is refused by the policy rather than by
# TenantNotBound, measured as `new row violates row-level security policy` (ADR-0005 section 4).
#
# The CASE reads as a longer EXCLUDED and is not one: a batch that spoke no geometry for a feature
# must leave the stored one alone rather than write its silence over an edit (ADR-0012 decision 3's
# addition of 2026-09-09), and only a feature the batch did speak for is in the sixth array.
#
# The WHERE looks redundant under a wall that already refuses another tenant's row, and it is what
# stops that refusal being an untyped 500: `id` is a global key, so a conflict on a row behind the
# wall reaches DO UPDATE, which raises 42501 rather than skipping it (measured 2026-09-10 on this
# table, PostgreSQL 18.6), answering a colliding identifier differently from a fresh one (T6.5;
# ADR-0010 decision 6's additions of 2026-08-07 and 2026-09-08). Skipped instead, the row stays
# its own tenant's and the answer does not move.
PROJECT_THE_CURRENT_STATE = f"""
    INSERT INTO {Feature._meta.db_table} AS projected
        (id, tenant_id, project_id, layer_id, geometry)
    SELECT id, tenant_id, project_id, layer_id, geometry::geometry
    FROM unnest(%s::uuid[], %s::uuid[], %s::uuid[], %s::uuid[], %s::text[])
        AS incoming (id, tenant_id, project_id, layer_id, geometry)
    ON CONFLICT (id) DO UPDATE SET
        project_id = EXCLUDED.project_id,
        layer_id = EXCLUDED.layer_id,
        geometry = CASE
            WHEN projected.id = ANY(%s::uuid[]) THEN EXCLUDED.geometry
            ELSE projected.geometry
        END
    WHERE projected.tenant_id = EXCLUDED.tenant_id
"""


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
    return Layer.objects.create(
        id=layer_id,
        tenant_id=tenant_id,
        project_id=project_id,
        name=name,
        geometry_kind=geometry_kind,
        storage_class=storage_class,
    )


def project_the_current_state(states: Sequence[TheCurrentStateOfAFeature]) -> None:
    """Leave the current state a batch of operations produces in the feature table (M15).

    Requires a tenant binding and opens none, and requires every layer named to be one its own
    project holds, which the composite reference refuses rather than stores (ADR-0005 section 5).
    One statement over the rows sorted by feature identifier, which is what makes the row locks
    deterministic (ADR-0012 decisions 1 and 3). A column the batch said nothing about is left as
    this write found it (that decision's addition of 2026-09-09), and a row belonging to another
    tenant is left to that tenant rather than refused loudly enough to be an answer (T6.5).
    """
    in_lock_order = sorted(states, key=lambda state: state.feature_id)

    with connection.cursor() as cursor:
        cursor.execute(
            PROJECT_THE_CURRENT_STATE,
            [
                [state.feature_id for state in in_lock_order],
                [state.tenant_id for state in in_lock_order],
                [state.project_id for state in in_lock_order],
                [state.layer_id for state in in_lock_order],
                [_as_the_storage_column_takes_it(state.geometry) for state in in_lock_order],
                [
                    state.feature_id
                    for state in in_lock_order
                    if state.the_batch_spoke_of_its_geometry
                ],
            ],
        )


def _as_the_storage_column_takes_it(geometry: object | None) -> str | None:
    if geometry is None:
        return None

    # Assigned after parsing and not passed to the constructor, both halves measured on Django
    # 5.2.16 (2026-09-08): GeoJSON declares no frame, so this constructor answers EPSG:4326 of its
    # own accord, and `srid=` beside a GeoJSON input raises rather than overriding it (M5 rule 1).
    read = GEOSGeometry(json.dumps(geometry))
    read.srid = STORAGE_FRAME_SRID
    return read.hexewkb.decode()
