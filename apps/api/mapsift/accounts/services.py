"""The writes on the account tree (M1): minting an account, and the containers below its tenant.

Creating an account is the one write here that binds a tenant itself, because it is the one that
mints it; the rest require a binding already in force (ADR-0005 sections 3 and 4).
"""

from uuid import UUID, uuid4

from mapsift.accounts.models import Membership, Project, Tenant, User, Workspace
from mapsift.common.binding import tenant_scope


def create_personal_account(*, email: str) -> Membership:
    """Create the user, their personal tenant, and the one owner membership joining them."""
    user = User.objects.create(email=email)
    return _create_tenant_owned_by(user, kind=Tenant.Kind.PERSONAL, name=email)


def create_organization_account(*, name: str, owner: User) -> Membership:
    """Create an organization tenant for a user who already has an identity."""
    return _create_tenant_owned_by(owner, kind=Tenant.Kind.ORGANIZATION, name=name)


def _create_tenant_owned_by(owner: User, *, kind: Tenant.Kind, name: str) -> Membership:
    tenant_id = uuid4()

    with tenant_scope(tenant_id):
        Tenant.objects.create(id=tenant_id, kind=kind, name=name)
        return Membership.objects.create(
            id=uuid4(),
            tenant_id=tenant_id,
            user=owner,
            role=Membership.Role.OWNER,
            # T6.3: an owner requires a full editing licence, so this is not a default to pick.
            licence=Membership.Licence.EDITOR,
        )


def create_workspace(*, workspace_id: UUID, tenant_id: UUID, name: str) -> Workspace:
    """Create a workspace in the tenant already in force, under the identifier handed in (M1, M3).

    Requires a tenant binding and opens none, and the tenant handed in is the row's own value
    rather than a second authority beside that binding (ADR-0005 sections 3 and 4).
    """
    return Workspace.objects.create(id=workspace_id, tenant_id=tenant_id, name=name)


def create_project(*, project_id: UUID, tenant_id: UUID, workspace_id: UUID, name: str) -> Project:
    """Create a project inside an existing workspace of the tenant in force (M1, M3).

    Requires a tenant binding and opens none, and the tenant handed in is the row's own value
    rather than a second authority beside that binding (ADR-0005 sections 3 and 4).
    """
    return Project.objects.create(
        id=project_id, tenant_id=tenant_id, workspace_id=workspace_id, name=name
    )
