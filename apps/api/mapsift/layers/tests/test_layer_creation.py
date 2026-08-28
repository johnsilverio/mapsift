"""The published path that creates a layer, inside the wall and inside one project.

Trace: PRD C1 (the structure a feature is drawn into, created before anything is drawn into it; its
attribute-schema half is M6 and is not this task's), M2's Shape (the project, the declared geometry
kind and the storage class as properties of the layer), M3 (the identifier is the creating
client's, and the server neither allocates nor rewrites one), M1 for its isolation clause alone;
C3, C4; ADR-0005 sections 3, 4 and 5, ADR-0006 section 3, ADR-0007 section 3.
"""

from uuid import UUID, uuid4

import pytest

from conftest import FOREIGN_KEY_VIOLATION, POLICY_VIOLATION, Party, refused_with
from mapsift.common.binding import TenantNotBound, tenant_scope
from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import GeometryKind, StorageClass
from mapsift.layers.services import create_layer

pytestmark = pytest.mark.django_db(transaction=True)


def _a_layer_created_by_the_service(
    party: Party,
    *,
    layer_id: UUID,
    name: str = "vegetation cover",
    geometry_kind: GeometryKind = GeometryKind.POLYGON,
    storage_class: StorageClass = StorageClass.ELEMENT,
) -> Layer:
    """The path under test, called with this party's own tenant and its own project.

    A case whose subject is a tenant or a project other than the party's calls the service
    directly, so the disagreement that case exists for stays visible in its own body.
    """
    return create_layer(
        layer_id=layer_id,
        tenant_id=party.tenant_id,
        project_id=party.project_id,
        name=name,
        geometry_kind=geometry_kind,
        storage_class=storage_class,
    )


def test_a_layer_is_stored_under_the_identifier_its_caller_minted(alice: Party) -> None:
    """M3, ADR-0006 section 3: the service stores the identifier it received rather than one of
    its own, which is the half of M3 that has a runtime on the server."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        created = _a_layer_created_by_the_service(alice, layer_id=minted)

        assert created.pk == minted
        assert Layer.objects.filter(pk=minted).exists()


def test_a_layer_is_stored_under_the_name_its_caller_gave(alice: Party) -> None:
    """PRD C1: the user names a layer, so the row carries what the caller named it rather than
    the empty value a CharField with no default lands when the argument is dropped."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(alice, layer_id=minted, name="Cobertura vegetal")

        assert Layer.objects.get(pk=minted).name == "Cobertura vegetal"


def test_each_layer_carries_the_geometry_kind_its_caller_declared(alice: Party) -> None:
    """PRD C1, M2's Shape: the declared kind is a property of the layer, so two layers of one
    project carry two different kinds. Two rather than one, because a single member cannot tell a
    stored declaration from a constant the service picked for itself."""
    a_line, a_polygon = uuid4(), uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(alice, layer_id=a_line, geometry_kind=GeometryKind.LINE)
        _a_layer_created_by_the_service(
            alice, layer_id=a_polygon, geometry_kind=GeometryKind.POLYGON
        )

        assert Layer.objects.get(pk=a_line).geometry_kind == GeometryKind.LINE
        assert Layer.objects.get(pk=a_polygon).geometry_kind == GeometryKind.POLYGON


def test_each_layer_carries_the_storage_class_its_caller_declared(alice: Party) -> None:
    """M2's Shape: the class is a property of the layer, so two layers of one project carry two
    different classes. Two for the reason the geometry-kind case above is two. What the class then
    decides about a feature's path is M2's own acceptance and is MAP-66's, never asserted here."""
    an_element, a_served = uuid4(), uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(
            alice, layer_id=an_element, storage_class=StorageClass.ELEMENT
        )
        _a_layer_created_by_the_service(alice, layer_id=a_served, storage_class=StorageClass.SERVED)

        assert Layer.objects.get(pk=an_element).storage_class == StorageClass.ELEMENT
        assert Layer.objects.get(pk=a_served).storage_class == StorageClass.SERVED


def test_a_feature_can_be_drawn_into_the_layer_this_path_created(alice: Party) -> None:
    """PRD C1: what is created is the structure a feature is drawn into, so the row this path lands
    is one a feature's composite reference resolves. Measured 2026-08-28 and carried in this task's
    spec: with no such layer row the identical insert is refused with a foreign-key violation, which
    is what makes this an assertion rather than a formality."""
    layer_id, feature_id = uuid4(), uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(alice, layer_id=layer_id)

        Feature.objects.create(
            id=feature_id,
            tenant_id=alice.tenant_id,
            project_id=alice.project_id,
            layer_id=layer_id,
            geometry=None,
        )

        assert Feature.objects.filter(pk=feature_id).exists()


def test_a_layer_holds_the_project_it_was_created_in(alice: Party) -> None:
    """M2's Shape: the project is part of the layer's persisted shape, so the row carries the one
    its caller named."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(alice, layer_id=minted)

        assert Layer.objects.get(pk=minted).project_id == alice.project_id


def test_a_layer_belongs_to_exactly_the_tenant_it_was_created_under(
    alice: Party, bob: Party
) -> None:
    """M1, C4: one identifier answers with a row inside the tenant that created it and with nothing
    inside another. The pair is the assertion rather than the second half alone, because the wall
    denies by returning nothing (ADR-0005 section 4) and a row that was never written does too. A
    tenant is bound in both halves and the first proves the row exists, so what the empty half
    measures is the isolation policy, neither the application guard nor an absence."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        _a_layer_created_by_the_service(alice, layer_id=minted)
        assert Layer.objects.filter(pk=minted).exists()

    with tenant_scope(bob.tenant_id):
        assert not Layer.objects.filter(pk=minted).exists()


def test_creating_a_layer_with_no_tenant_bound_is_refused_by_the_application_guard() -> None:
    """C4, ADR-0005 sections 3 and 4: the service requires a binding and opens none, so with none
    in force it refuses by name instead of writing a row the wall would have to police. The named
    refusal is the whole point, because the wall's own answer to an unbound write is silence."""
    with pytest.raises(TenantNotBound):
        create_layer(
            layer_id=uuid4(),
            tenant_id=uuid4(),
            project_id=uuid4(),
            name="unbound",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_a_layer_claiming_a_tenant_other_than_the_one_bound_is_refused_by_the_wall(
    alice: Party, bob: Party
) -> None:
    """C4, ADR-0005 section 3: the tenant argument is not a second authority beside the binding, so
    a claim that disagrees with what is in force is refused rather than stored. The project named is
    the claimed tenant's own, so the composite reference is satisfiable and the policy is the only
    mechanism left to refuse, which is what naming the SQLSTATE proves."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        create_layer(
            layer_id=uuid4(),
            tenant_id=bob.tenant_id,
            project_id=bob.project_id,
            name="smuggled",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_a_layer_cannot_be_created_in_another_tenants_project(alice: Party, bob: Party) -> None:
    """M1, C4, ADR-0005 section 5: the project named exists and so does the tenant, and what the
    composite reference over (tenant_id, project_id) refuses is the pair. The row carries the
    writer's own tenant, so the policy admits it and the wall is not what answers here."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        create_layer(
            layer_id=uuid4(),
            tenant_id=alice.tenant_id,
            project_id=bob.project_id,
            name="borrowed",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )


def test_a_layer_cannot_be_created_in_a_project_that_does_not_exist(alice: Party) -> None:
    """M1: the project is required rather than nullable, so a layer naming a project that exists
    nowhere is refused by referential integrity, named by its SQLSTATE rather than by the exception.
    Measured 2026-08-28: the composite reference is the only one covering the project, so it is what
    refuses here too, and this case pins a second sentence rather than a second mechanism."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        create_layer(
            layer_id=uuid4(),
            tenant_id=alice.tenant_id,
            project_id=uuid4(),
            name="orphan",
            geometry_kind=GeometryKind.POLYGON,
            storage_class=StorageClass.ELEMENT,
        )
