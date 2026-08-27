"""The reads `layers` publishes (ADR-0007 section 3).

Every spatial read here takes its container as a required argument, which is the first of the
three mechanisms ADR-0013 decision 4 weighs and is the only claim this module can make on its own.
"""

from uuid import UUID

from django.contrib.gis.geos import Polygon
from django.db.models import QuerySet

from mapsift.layers.models import Feature


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
