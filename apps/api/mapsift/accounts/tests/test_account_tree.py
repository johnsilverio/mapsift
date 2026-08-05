"""The five entities of the account tree, and the rules that hold them together.

Trace: M1 (the tree and the tenant identifier), M3 (identity of every created object); C4;
ADR-0005 section 7 (which tables are inside the wall), ADR-0006 (the identifier variant).
"""

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import Error, connection

from conftest import Party
from mapsift.accounts.models import Membership, Project, Tenant, Workspace
from mapsift.accounts.services import create_organization_account, create_personal_account
from mapsift.common.binding import tenant_scope

pytestmark = pytest.mark.django_db(transaction=True)

ACCOUNT_TREE_APP = "accounts"


def test_creating_a_personal_account_creates_a_tenant_of_kind_personal() -> None:
    """M1: the organization is a tenant kind rather than a sixth entity, so a freelancer and a
    company take the same isolation path."""
    membership = create_personal_account(email="ana@example.com")

    with tenant_scope(membership.tenant_id):
        assert Tenant.objects.get(pk=membership.tenant_id).kind == Tenant.Kind.PERSONAL


def test_creating_a_personal_account_creates_exactly_one_owner_membership() -> None:
    """M1."""
    membership = create_personal_account(email="ana@example.com")

    with tenant_scope(membership.tenant_id):
        roles = list(Membership.objects.values_list("role", flat=True))

    assert roles == [Membership.Role.OWNER]


def test_a_user_in_two_tenants_is_one_identity_with_a_membership_in_each() -> None:
    """M1: the user is the global durable identity and belongs to several tenants."""
    personal = create_personal_account(email="ana@example.com")
    organization = create_organization_account(name="Acme Ambiental", owner=personal.user)

    assert organization.user_id == personal.user_id
    assert organization.tenant_id != personal.tenant_id
    for tenant_id in (personal.tenant_id, organization.tenant_id):
        with tenant_scope(tenant_id):
            assert Membership.objects.filter(user_id=personal.user_id).count() == 1


def test_an_ordinary_update_cannot_move_a_workspace_to_another_tenant(
    alice: Party, bob: Party
) -> None:
    """M1: a workspace resolves to exactly one tenant, immutable in the ordinary write path."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        workspace = Workspace.objects.get(pk=alice.workspace_id)
        workspace.tenant_id = bob.tenant_id
        workspace.save()


def test_an_ordinary_update_cannot_move_a_project_to_another_tenant(
    alice: Party, bob: Party
) -> None:
    """M1: a project resolves to exactly one tenant, immutable in the ordinary write path."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        project = Project.objects.get(pk=alice.project_id)
        project.tenant_id = bob.tenant_id
        project.save()


def test_every_row_that_belongs_to_a_tenant_carries_the_tenant_identifier(
    tenant_owned_tables: frozenset[str],
) -> None:
    """M1, N2: read from the app's own models, so one added later without the identifier fails
    here rather than being reviewed for it."""
    tables = {model._meta.db_table for model in apps.get_app_config(ACCOUNT_TREE_APP).get_models()}

    assert tables - {get_user_model()._meta.db_table} - tenant_owned_tables == set()


def test_the_user_identity_is_deliberately_outside_the_wall(
    tenant_owned_tables: frozenset[str],
) -> None:
    """M1, ADR-0005 section 7: a user spans tenants by design, so its confidentiality is the
    permission layer's job rather than a second SQL wall."""
    assert get_user_model()._meta.db_table not in tenant_owned_tables


def test_every_identifier_is_stored_as_the_native_uuid_type(
    tenant_owned_tables: frozenset[str],
) -> None:
    """M3, ADR-0006 sections 1 and 4: one canonical textual form across four languages, sixteen
    bytes in PostgreSQL, never text."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, a.attname, format_type(a.atttypid, a.atttypmod)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_index x ON x.indrelid = c.oid AND x.indisprimary
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
            WHERE n.nspname = 'public'
              AND c.relname = ANY(%s)
              AND (a.attnum = x.indkey[0] OR a.attname = 'tenant_id')
              AND format_type(a.atttypid, a.atttypmod) <> 'uuid'
            """,
            [sorted(tenant_owned_tables)],
        )

        assert cursor.fetchall() == []


def test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier(
    tenant_owned_tables: frozenset[str],
) -> None:
    """M3, ADR-0006 section 3: a default there quietly makes the server the allocator the moment a
    code path forgets to send one."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, a.attname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_index x ON x.indrelid = c.oid AND x.indisprimary
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = x.indkey[0]
            WHERE n.nspname = 'public' AND c.relname = ANY(%s) AND a.atthasdef
            """,
            [sorted(tenant_owned_tables)],
        )

        assert cursor.fetchall() == []


def test_the_server_never_allocates_an_identifier_for_an_object_a_client_creates(
    alice: Party,
) -> None:
    """M3, ADR-0006 section 3: the same rule one level up from the column default, because a
    generator on the model is the server allocating just as much as one in the database is."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        Workspace.objects.create(tenant_id=alice.tenant_id, name="unnamed")
