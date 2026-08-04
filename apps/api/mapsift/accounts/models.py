"""The five entities of the account tree (M1), and which of them the wall applies to.

Four carry the tenant identifier and live inside it. The user is deliberately outside, which is a
decision rather than an omission (ADR-0005 section 7).
"""

from typing import ClassVar
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser
from django.db import models

from mapsift.common.binding import TenantOwnedManager


class User(AbstractBaseUser):
    """The global durable identity that holds the credential and may belong to several tenants."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"


class Tenant(models.Model):
    """The top container of an account, and the only isolation boundary there is (M1, C4)."""

    class Kind(models.TextChoices):
        PERSONAL = "personal", "Personal"
        ORGANIZATION = "organization", "Organization"

    # The column name is what puts a table inside the wall: the policies key on it and the N2 test
    # enumerates from it (ADR-0005 section 3). Renaming it to `id` for consistency with the models
    # below drops this table out of both, silently.
    id = models.UUIDField(primary_key=True, db_column="tenant_id", editable=False)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    name = models.CharField(max_length=200)

    objects = TenantOwnedManager["Tenant"]()


class Membership(models.Model):
    """One user's place in one tenant: their governance role and their licence there (M1, T6.2)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    class Licence(models.TextChoices):
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(primary_key=True, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships", db_index=False
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    licence = models.CharField(max_length=32, choices=Licence.choices)

    objects = TenantOwnedManager["Membership"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["tenant", "user"], name="one_membership_per_user_per_tenant"
            )
        ]


class Workspace(models.Model):
    """Groups projects inside one tenant, and is where sharing lives (M1)."""

    id = models.UUIDField(primary_key=True, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="workspaces")
    name = models.CharField(max_length=200)

    objects = TenantOwnedManager["Workspace"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            # Redundant against the primary key, and not removable: it is what Project's composite
            # reference points at (ADR-0005 section 5).
            models.UniqueConstraint(
                fields=["tenant", "id"], name="workspace_identity_within_its_tenant"
            )
        ]


class Project(models.Model):
    """Holds the elements and layers, in exactly one workspace and one tenant (M1)."""

    id = models.UUIDField(primary_key=True, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="projects")
    # The database gets a composite reference from the migration instead, because a single-column
    # one crosses tenants (ADR-0005 section 5, probes H and N). Dropping db_constraint=False adds
    # the open reference back beside the closed one.
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="projects",
        db_constraint=False,
        db_index=False,
    )
    name = models.CharField(max_length=200)

    objects = TenantOwnedManager["Project"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            # Redundant against the primary key, and not removable: it is what a layer's composite
            # reference points at, by the rule that already put the matching one on Workspace
            # (ADR-0005 section 5).
            models.UniqueConstraint(
                fields=["tenant", "id"], name="project_identity_within_its_tenant"
            )
        ]
        indexes: ClassVar[list[models.Index]] = [
            # The column order is not interchangeable: the tenant leads (ADR-0005 section 5).
            models.Index(fields=["tenant", "workspace"], name="project_workspace_by_tenant")
        ]
