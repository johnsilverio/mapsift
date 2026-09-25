"""The reads `layers` publishes (ADR-0007 section 3).

Every spatial read here takes its container as a required argument, which is the first of the
three mechanisms ADR-0013 decision 4 weighs and is the only claim this module can make on its own.
"""

from collections.abc import Collection
from uuid import UUID

from django.contrib.gis.geos import Polygon
from django.db.models import QuerySet

from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import (
    GeometryKind,
    StorageClass,
    TheDeclarationsOfALayer,
    WhereAFeatureIsFiled,
)


def features_of_a_layer_intersecting(layer_id: UUID, box: Polygon) -> QuerySet[Feature]:
    """The features of one layer of the tenant in force whose geometry meets the given box (M2).

    Requires a tenant binding and opens none (ADR-0005 sections 3 and 4).
    """
    return Feature.objects.filter(layer_id=layer_id, geometry__intersects=box)


def features_of_a_project_intersecting(project_id: UUID, box: Polygon) -> QuerySet[Feature]:
    """The features of one project of the tenant in force whose geometry meets the given box (M2).

    Requires a tenant binding and opens none (ADR-0005 sections 3 and 4).
    """
    return Feature.objects.filter(project_id=project_id, geometry__intersects=box)


def the_declarations_of_the_layers_a_project_holds_among(
    project_id: UUID, layer_ids: Collection[UUID]
) -> dict[UUID, TheDeclarationsOfALayer]:
    """The declarations of the given layers this project of the tenant in force holds (M2).

    A given layer the project does not hold is absent from the mapping rather than refused.

    Requires a tenant binding and opens none (ADR-0005 sections 3 and 4). It answers a mapping
    rather than a queryset, so its rows are read inside the binding that authorised them.
    """
    held = Layer.objects.filter(project_id=project_id, id__in=layer_ids)
    return {
        layer_id: TheDeclarationsOfALayer(
            storage_class=StorageClass(storage_class), geometry_kind=GeometryKind(geometry_kind)
        )
        for layer_id, storage_class, geometry_kind in held.values_list(
            "id", "storage_class", "geometry_kind"
        )
    }


def where_the_features_the_tenant_holds_are_filed_among(
    feature_ids: Collection[UUID],
) -> dict[UUID, WhereAFeatureIsFiled]:
    """The project and layer each of the given features the tenant in force holds is filed under,
    in any of its projects (M2, M9).

    A given feature the tenant does not hold is absent from the mapping rather than refused, and so
    is one whose identifier another tenant holds, the exception PRD M9's Provenance accepts until
    MAP-75 reads what a tenant holds from its own log.

    Requires a tenant binding and opens none (ADR-0005 sections 3 and 4). It answers a mapping
    rather than a queryset, so its rows are read inside the binding that authorised them.
    """
    held = Feature.objects.filter(id__in=feature_ids)
    return {
        feature_id: WhereAFeatureIsFiled(project_id=project_id, layer_id=layer_id)
        for feature_id, project_id, layer_id in held.values_list("id", "project_id", "layer_id")
    }
