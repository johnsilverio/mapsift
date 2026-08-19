"""The published path that creates a workspace and a project, inside the wall.

Trace: M1 (a workspace and a project each resolve to exactly one tenant, and a project holds its
place inside a workspace), M3 (the identifier is the creating client's, and the server neither
allocates nor rewrites one); C3, C4; ADR-0005 sections 3, 4 and 5 (the binding a writer requires
and does not open, the wall's silence beside the application's guard, the composite reference
between two tenant-owned tables); ADR-0006 section 3; ADR-0007 section 3.
"""

from uuid import uuid4

import pytest

from conftest import FOREIGN_KEY_VIOLATION, POLICY_VIOLATION, Party, refused_with
from mapsift.accounts.models import Project, Workspace
from mapsift.accounts.services import create_project, create_workspace
from mapsift.common.binding import TenantNotBound, tenant_scope

pytestmark = pytest.mark.django_db(transaction=True)


def test_a_workspace_is_stored_under_the_identifier_its_caller_minted(alice: Party) -> None:
    """M3, ADR-0006 section 3: the service stores the identifier it received rather than one of
    its own, which is the half of M3 that has a runtime on the server."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        created = create_workspace(workspace_id=minted, tenant_id=alice.tenant_id, name="Campo")

        assert created.pk == minted
        assert Workspace.objects.filter(pk=minted).exists()


def test_a_project_is_stored_under_the_identifier_its_caller_minted(alice: Party) -> None:
    """M3, ADR-0006 section 3."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        created = create_project(
            project_id=minted,
            tenant_id=alice.tenant_id,
            workspace_id=alice.workspace_id,
            name="Fazenda Boa Vista",
        )

        assert created.pk == minted
        assert Project.objects.filter(pk=minted).exists()


def test_a_workspace_is_stored_under_the_name_its_caller_gave(alice: Party) -> None:
    """M1: the name is part of a workspace's shape, so the row carries what the caller named it
    rather than the empty value a field with no default lands."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        create_workspace(workspace_id=minted, tenant_id=alice.tenant_id, name="Campo")

        assert Workspace.objects.get(pk=minted).name == "Campo"


def test_a_project_is_stored_under_the_name_its_caller_gave(alice: Party) -> None:
    """M1, for the reason and in the shape of the workspace case above."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        create_project(
            project_id=minted,
            tenant_id=alice.tenant_id,
            workspace_id=alice.workspace_id,
            name="Fazenda Boa Vista",
        )

        assert Project.objects.get(pk=minted).name == "Fazenda Boa Vista"


def test_a_workspace_belongs_to_exactly_the_tenant_it_was_created_under(
    alice: Party, bob: Party
) -> None:
    """M1, C4: one identifier answers with a row inside the tenant that created it and with
    nothing inside another. The pair is the assertion rather than the second half alone, because
    the wall denies by returning nothing (ADR-0005 section 4) and an absent row does too."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        create_workspace(workspace_id=minted, tenant_id=alice.tenant_id, name="Campo")
        assert Workspace.objects.filter(pk=minted).exists()

    with tenant_scope(bob.tenant_id):
        assert not Workspace.objects.filter(pk=minted).exists()


def test_a_project_belongs_to_exactly_the_tenant_it_was_created_under(
    alice: Party, bob: Party
) -> None:
    """M1, C4, for the reason and in the shape of the workspace case above."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        create_project(
            project_id=minted,
            tenant_id=alice.tenant_id,
            workspace_id=alice.workspace_id,
            name="Fazenda Boa Vista",
        )
        assert Project.objects.filter(pk=minted).exists()

    with tenant_scope(bob.tenant_id):
        assert not Project.objects.filter(pk=minted).exists()


def test_a_project_holds_the_workspace_it_was_created_in(alice: Party) -> None:
    """M1: a project is inside exactly one workspace, and the caller names which."""
    minted = uuid4()

    with tenant_scope(alice.tenant_id):
        create_project(
            project_id=minted,
            tenant_id=alice.tenant_id,
            workspace_id=alice.workspace_id,
            name="Fazenda Boa Vista",
        )

        assert Project.objects.get(pk=minted).workspace_id == alice.workspace_id


def test_a_project_cannot_be_created_under_a_workspace_that_does_not_exist(
    alice: Party,
) -> None:
    """M1: the parent is required rather than nullable, so a project naming a workspace that
    exists nowhere is refused by referential integrity, named by its SQLSTATE rather than by the
    exception. Which reference refused is outside what this case sees, because a single-column one
    would refuse this too."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        create_project(
            project_id=uuid4(),
            tenant_id=alice.tenant_id,
            workspace_id=uuid4(),
            name="orphan",
        )


def test_a_project_cannot_be_created_under_another_tenants_workspace(
    alice: Party, bob: Party
) -> None:
    """M1, C4, ADR-0005 section 5: the workspace named exists, so a single-column reference is
    satisfied and only the composite one over (tenant_id, workspace_id) can refuse. Referential
    integrity bypasses the policy by design, so the wall is not what answers here."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        create_project(
            project_id=uuid4(),
            tenant_id=alice.tenant_id,
            workspace_id=bob.workspace_id,
            name="borrowed",
        )


def test_creating_a_workspace_with_no_tenant_bound_is_refused_by_the_application_guard() -> None:
    """C4, ADR-0005 sections 3 and 4: the service requires a binding and opens none, so with
    none in force it refuses by name instead of writing a row the wall would have to police."""
    with pytest.raises(TenantNotBound):
        create_workspace(workspace_id=uuid4(), tenant_id=uuid4(), name="unbound")


def test_creating_a_project_with_no_tenant_bound_is_refused_by_the_application_guard() -> None:
    """C4, ADR-0005 sections 3 and 4."""
    with pytest.raises(TenantNotBound):
        create_project(
            project_id=uuid4(),
            tenant_id=uuid4(),
            workspace_id=uuid4(),
            name="unbound",
        )


def test_a_workspace_claiming_a_tenant_other_than_the_one_bound_is_refused_by_the_wall(
    alice: Party, bob: Party
) -> None:
    """C4, ADR-0005 section 3: the tenant argument is not a second authority beside the binding,
    so a claim that disagrees with what is in force is refused rather than stored."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        create_workspace(workspace_id=uuid4(), tenant_id=bob.tenant_id, name="smuggled")


def test_a_project_claiming_a_tenant_other_than_the_one_bound_is_refused_by_the_wall(
    alice: Party, bob: Party
) -> None:
    """C4, ADR-0005 section 3: the workspace named is the claimed tenant's own, so the composite
    reference is satisfiable and the policy is the only mechanism left to refuse."""
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        create_project(
            project_id=uuid4(),
            tenant_id=bob.tenant_id,
            workspace_id=bob.workspace_id,
            name="smuggled",
        )
