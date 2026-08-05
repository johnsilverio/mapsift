"""The layer and the feature as persisted shapes, inside the same wall as everything else.

Trace: M2, M3, M5 rule 1, N2; C4; ADR-0005 sections 5 and 7, ADR-0006 section 3.

The wall's own properties are deliberately absent here: the MAP-3 suites enumerate them from the
catalogue, so the first two tests below are the whole hook those enumerations hang from.
"""

from uuid import uuid4

import pytest
from django.contrib.gis.geos import Polygon
from django.db import connection

from conftest import (
    FOREIGN_KEY_VIOLATION,
    INVALID_PARAMETER_VALUE,
    NOT_NULL_VIOLATION,
    POLICY_VIOLATION,
    Party,
    refused_with,
    second_project_of,
)
from mapsift.common.binding import tenant_scope
from mapsift.common.geometry import ForeignFrame
from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import GeometryKind, StorageClass

pytestmark = pytest.mark.django_db(transaction=True)

# M5 rule 1: SIRGAS 2000, the one frame stored geometry is in.
STORAGE_FRAME_SRID = 4674

# SIRGAS 2000 / UTM zone 23S, which is how Brazilian cadastral data arrives.
A_CADASTRAL_FRAME_SRID = 31983
A_PARCEL_IN_THAT_FRAME = Polygon(
    ((330000.0, 7390000.0), (330100.0, 7390000.0), (330100.0, 7390100.0), (330000.0, 7390000.0)),
    srid=A_CADASTRAL_FRAME_SRID,
)


def _a_layer(party: Party, *, name: str = "cover") -> Layer:
    return Layer.objects.create(
        id=uuid4(),
        tenant_id=party.tenant_id,
        project_id=party.project_id,
        name=name,
        geometry_kind=GeometryKind.POLYGON,
        storage_class=StorageClass.ELEMENT,
    )


def _a_feature(party: Party, layer: Layer) -> Feature:
    return Feature.objects.create(
        id=uuid4(),
        tenant_id=party.tenant_id,
        project_id=party.project_id,
        layer_id=layer.pk,
        geometry=None,
    )


def test_the_layer_table_is_inside_the_isolation_wall(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, C4, ADR-0005 sections 3 and 7: carrying the tenant identifier is what puts a table
    inside the wall and into every catalogue-driven test."""
    assert Layer._meta.db_table in tenant_owned_tables


def test_the_feature_table_is_inside_the_isolation_wall(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, C4, ADR-0005 sections 3 and 7."""
    assert Feature._meta.db_table in tenant_owned_tables


def test_the_geometry_column_declares_the_one_storage_frame() -> None:
    """M5 rule 1, read from the catalogue rather than reviewed: one storage frame, SIRGAS 2000."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT srid
            FROM geometry_columns
            WHERE f_table_schema = 'public' AND f_table_name = %s
            """,
            [Feature._meta.db_table],
        )

        assert cursor.fetchall() == [(STORAGE_FRAME_SRID,)]


def test_a_writer_outside_the_orm_cannot_store_geometry_in_another_frame(alice: Party) -> None:
    """M5 rule 1, and it is I4's reasoning applied to the frame. The column's own type modifier is
    what refuses this, which is why no separate constraint exists."""
    with tenant_scope(alice.tenant_id):
        layer = _a_layer(alice)

    with (
        refused_with(INVALID_PARAMETER_VALUE),
        tenant_scope(alice.tenant_id),
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """
            INSERT INTO layers_feature (id, tenant_id, project_id, layer_id, geometry)
            VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, %s))
            """,
            [
                uuid4(),
                alice.tenant_id,
                alice.project_id,
                layer.pk,
                A_PARCEL_IN_THAT_FRAME.wkt,
                A_CADASTRAL_FRAME_SRID,
            ],
        )


def test_a_geometry_in_another_frame_is_refused_rather_than_converted(alice: Party) -> None:
    """M5 rules 1 and 3: the source frame is never discarded and a datum transformation is an
    explicit recorded decision, so the write path refuses rather than converting."""
    with tenant_scope(alice.tenant_id):
        layer = _a_layer(alice)

        with pytest.raises(ForeignFrame):
            Feature.objects.create(
                id=uuid4(),
                tenant_id=alice.tenant_id,
                project_id=alice.project_id,
                layer_id=layer.pk,
                geometry=A_PARCEL_IN_THAT_FRAME,
            )


def test_a_read_bound_to_one_tenant_does_not_see_another_tenants_layer(
    alice: Party, bob: Party
) -> None:
    """C4, N2, T6.1."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_layer(bob)

    with tenant_scope(alice.tenant_id):
        mine = _a_layer(alice)

        assert Layer.objects.filter(pk=mine.pk).exists()
        assert not Layer.objects.filter(pk=theirs.pk).exists()


def test_a_read_bound_to_one_tenant_does_not_see_another_tenants_feature(
    alice: Party, bob: Party
) -> None:
    """C4, N2, T6.1."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_feature(bob, _a_layer(bob))

    with tenant_scope(alice.tenant_id):
        mine = _a_feature(alice, _a_layer(alice))

        assert Feature.objects.filter(pk=mine.pk).exists()
        assert not Feature.objects.filter(pk=theirs.pk).exists()


def test_an_update_bound_to_one_tenant_does_not_reach_another_tenants_layer(
    alice: Party, bob: Party
) -> None:
    """C4, N2."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_layer(bob)

    with tenant_scope(alice.tenant_id):
        reached = Layer.objects.filter(pk=theirs.pk).update(name="taken")

    assert reached == 0
    with tenant_scope(bob.tenant_id):
        assert Layer.objects.get(pk=theirs.pk).name != "taken"


def test_a_delete_bound_to_one_tenant_does_not_reach_another_tenants_feature(
    alice: Party, bob: Party
) -> None:
    """C4, N2, C7: the destructive verb is exercised on the feature, because that is the row a
    legal-weight geometry lives in."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_feature(bob, _a_layer(bob))

    with tenant_scope(alice.tenant_id):
        reached, _ = Feature.objects.filter(pk=theirs.pk).delete()

    assert reached == 0
    with tenant_scope(bob.tenant_id):
        assert Feature.objects.filter(pk=theirs.pk).exists()


def test_an_insert_cannot_smuggle_a_layer_into_another_tenant(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 3 (probe F): WITH CHECK makes the write path as closed as the read
    path, and naming the SQLSTATE is what proves it was the policy that refused."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        Layer.objects.create(
            id=uuid4(),
            tenant_id=bob.tenant_id,
            project_id=bob.project_id,
            name="smuggled",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_an_insert_cannot_smuggle_a_feature_into_another_tenant(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 3 (probe F). The reference is to the layer that owns the row, so
    the key is satisfied and only the policy is left to refuse it."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_layer(bob)

    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        Feature.objects.create(
            id=uuid4(),
            tenant_id=bob.tenant_id,
            project_id=bob.project_id,
            layer_id=theirs.pk,
            geometry=None,
        )


def test_a_layer_cannot_reference_a_project_of_another_tenant(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 5 (probes H and N), and the case that proves the project carries
    the uniqueness the reference points at. The row is the writer's own tenant, so the policy admits
    it and only the key can refuse."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        Layer.objects.create(
            id=uuid4(),
            tenant_id=alice.tenant_id,
            project_id=bob.project_id,
            name="borrowed",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_a_feature_cannot_reference_a_layer_of_another_tenant(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 5 (probes H and N): the same channel one level down, where it is
    actually exercised, since a feature is the row a client mints offline."""
    with tenant_scope(bob.tenant_id):
        theirs = _a_layer(bob)

    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        Feature.objects.create(
            id=uuid4(),
            tenant_id=alice.tenant_id,
            project_id=alice.project_id,
            layer_id=theirs.pk,
            geometry=None,
        )


def test_a_feature_cannot_be_filed_under_a_project_its_layer_does_not_belong_to(
    alice: Party,
) -> None:
    """M2, ADR-0005 section 5: a feature filed under one project while its layer lives in another
    resolves to two projects. Both rows are the writer's own tenant, so the third column of the
    reference is the only thing left that can refuse it."""
    elsewhere = second_project_of(alice)

    with tenant_scope(alice.tenant_id):
        layer = _a_layer(alice)

    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        Feature.objects.create(
            id=uuid4(),
            tenant_id=alice.tenant_id,
            project_id=elsewhere,
            layer_id=layer.pk,
            geometry=None,
        )


def test_two_tenants_can_each_hold_a_layer_of_the_same_name(alice: Party, bob: Party) -> None:
    """N2, ADR-0005 section 5 (probe I): a natural key is unique per tenant and never globally,
    because a global unique index answers across the wall."""
    with tenant_scope(alice.tenant_id):
        _a_layer(alice, name="vegetation cover")

    with tenant_scope(bob.tenant_id):
        assert _a_layer(bob, name="vegetation cover").pk


def test_an_ordinary_update_cannot_move_a_layer_to_another_tenant(alice: Party, bob: Party) -> None:
    """M2, M1: a layer resolves to exactly one tenant, immutable in the ordinary write path."""
    with tenant_scope(alice.tenant_id):
        layer = _a_layer(alice)

    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        layer.tenant_id = bob.tenant_id
        layer.save()


def test_an_ordinary_update_cannot_move_a_feature_to_another_tenant(
    alice: Party, bob: Party
) -> None:
    """M2, M1: a feature resolves to exactly one tenant, immutable in the ordinary write path."""
    with tenant_scope(alice.tenant_id):
        feature = _a_feature(alice, _a_layer(alice))

    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        feature.tenant_id = bob.tenant_id
        feature.save()


def test_the_server_never_allocates_an_identifier_for_a_layer(alice: Party) -> None:
    """M3, ADR-0006 section 3: one level up from the column default, because a generator on the
    model is the server allocating just as much as one in the database is."""
    with refused_with(NOT_NULL_VIOLATION), tenant_scope(alice.tenant_id):
        Layer.objects.create(
            tenant_id=alice.tenant_id,
            project_id=alice.project_id,
            name="unnamed",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_the_server_never_allocates_an_identifier_for_a_feature(alice: Party) -> None:
    """M3, ADR-0006 section 3: the feature is the row this rule exists for, minted offline by the
    client that draws it."""
    with tenant_scope(alice.tenant_id):
        layer = _a_layer(alice)

    with refused_with(NOT_NULL_VIOLATION), tenant_scope(alice.tenant_id):
        Feature.objects.create(
            tenant_id=alice.tenant_id,
            project_id=alice.project_id,
            layer_id=layer.pk,
            geometry=None,
        )


def test_a_feature_carries_no_storage_class_of_its_own() -> None:
    """M2: the class is the layer's, so there is no per-feature class to change and the frontier
    cannot become per-row."""
    with pytest.raises(TypeError):
        # The call is a static error on purpose: django-stubs builds __init__ from the
        # fields, so the checker refuses the very argument this test exists to prove is
        # refused at runtime. Removing the ignore removes the test's subject.
        Feature(storage_class=StorageClass.ELEMENT)  # type: ignore[misc]


def test_a_feature_exists_before_its_geometry_does(alice: Party) -> None:
    """M2, foundation OQ-4: this slice's catalog is create a feature and then set its geometry, so
    a geometry required at creation makes the first of the two unrepresentable."""
    boundary = Polygon(((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (0.0, 0.0)), srid=STORAGE_FRAME_SRID)

    with tenant_scope(alice.tenant_id):
        feature = _a_feature(alice, _a_layer(alice))
        assert Feature.objects.get(pk=feature.pk).geometry is None

        feature.geometry = boundary
        feature.save()

        assert Feature.objects.get(pk=feature.pk).geometry is not None
