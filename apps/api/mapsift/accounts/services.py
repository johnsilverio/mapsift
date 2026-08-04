"""Creating an account, which is the one write that mints a tenant (M1)."""

from uuid import uuid4

from mapsift.accounts.models import Membership, Tenant, User
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
