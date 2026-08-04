"""A feature's geometry answers to the kind its layer declares.

Trace: M2 (the layer declares the geometry kind its features carry).

PostgreSQL cannot express this as a check across two tables, so it is a decision over plain data
and it is tested as one (`specs/testing.md` section 3) rather than discovered later in a layer that
renders wrong.
"""

import pytest

from mapsift.layers.rules import GeometryKind, geometry_is_admissible

DISAGREEING_PAIRS = [
    (layer, feature) for layer in GeometryKind for feature in GeometryKind if layer is not feature
]


@pytest.mark.parametrize("kind", list(GeometryKind))
def test_a_geometry_of_the_kind_the_layer_declares_is_admissible(kind: GeometryKind) -> None:
    """M2: a layer declares one geometry kind and its features carry that kind."""
    assert geometry_is_admissible(layer_kind=kind, feature_kind=kind) is True


@pytest.mark.parametrize(("layer_kind", "feature_kind"), DISAGREEING_PAIRS)
def test_a_geometry_of_another_kind_is_refused_rather_than_stored(
    layer_kind: GeometryKind, feature_kind: GeometryKind
) -> None:
    """M2: every disagreeing pair is enumerated from the closed set rather than listed, so a kind
    added later is refused against every other kind without this test being edited."""
    assert geometry_is_admissible(layer_kind=layer_kind, feature_kind=feature_kind) is False
