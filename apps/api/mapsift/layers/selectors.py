"""The reads `layers` publishes (ADR-0007 section 3).

Every spatial read here takes its container as a required argument, which is the first of the
three mechanisms ADR-0013 decision 4 weighs and is the only claim this module can make on its own.
"""

from collections.abc import Collection
from uuid import UUID

from django.contrib.gis.geos import Polygon
from django.db.models import QuerySet

from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import GeometryKind, StorageClass, WhatALayerDeclares


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


def what_the_layers_a_project_holds_declare(
    project_id: UUID, layer_ids: Collection[UUID]
) -> dict[UUID, WhatALayerDeclares]:
    """What each of the given layers this project of the tenant in force holds declares (M2).

    A layer the project does not hold is absent from the mapping, so its keys are also the answer
    to which of them exist at all. Requires a tenant binding and opens none (ADR-0005 sections 3
    and 4). It answers a mapping rather than a queryset, so its rows are read inside the binding
    that authorised them.
    """
    return {
        layer_id: WhatALayerDeclares(
            geometry_kind=GeometryKind(geometry_kind), storage_class=StorageClass(storage_class)
        )
        for layer_id, geometry_kind, storage_class in Layer.objects.filter(
            project_id=project_id, id__in=layer_ids
        ).values_list("id", "geometry_kind", "storage_class")
    }
