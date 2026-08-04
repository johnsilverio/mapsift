"""The isolation wall, proven where it lives: in the database.

Trace: C4, N2, T6.1; foundation I4; ADR-0005 (the roles, the binding, the composite keys). These
are invariant acceptance tests and they may never be weakened (specs/testing.md sections 4 and 9).
Every case here is one of ADR-0005's probes turned from a measurement into a gate.
"""

from uuid import uuid4

import pytest
from django.db import Error, connection

from accounts.binding import TenantNotBound, tenant_scope
from accounts.models import Project, Workspace
from conftest import Party

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0005 section 2. The owner is the migrate profile and owns the tables; the other three are
# what an application connects as.
CONNECTING_ROLES = ("mapsift_owner", "mapsift_app", "mapsift_tile", "mapsift_tokens")
RUNTIME_ROLES = ("mapsift_app", "mapsift_tile", "mapsift_tokens")


def test_the_suite_runs_as_a_role_the_wall_applies_to() -> None:
    """N2, ADR-0005 section 2 (probes J, K and L): tests and CI use the owner profile, which is
    safe only because of FORCE. A superuser or a BYPASSRLS role passes every case below without
    the wall existing at all, so this one runs first."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")

        assert cursor.fetchone() == (False, False)


def test_every_tenant_owned_table_has_row_level_security_enabled_and_forced(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, C4: enumerated from the catalogue, so a table added later without its policy fails here
    instead of quietly opening a hole."""
    assert tenant_owned_tables

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = ANY(%s)
              AND NOT (c.relrowsecurity AND c.relforcerowsecurity)
            """,
            [sorted(tenant_owned_tables)],
        )

        assert cursor.fetchall() == []


def test_no_role_this_system_connects_as_can_bypass_the_wall() -> None:
    """N2, ADR-0005 section 2 (probe L): a role holding BYPASSRLS reads every tenant after FORCE,
    so granting it is a defect rather than a shortcut."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = ANY(%s)",
            [list(CONNECTING_ROLES)],
        )
        roles = cursor.fetchall()

    assert {name for name, _, _ in roles} == set(CONNECTING_ROLES)
    assert [name for name, superuser, bypasses in roles if superuser or bypasses] == []


def test_no_runtime_role_owns_a_tenant_owned_table(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, ADR-0005 section 2 (probe J): ownership is a privilege, because an owner bypasses its
    own policies wherever FORCE is ever dropped."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, pg_get_userbyid(c.relowner)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = ANY(%s)
            """,
            [sorted(tenant_owned_tables)],
        )

        assert [table for table, owner in cursor.fetchall() if owner in RUNTIME_ROLES] == []


def test_no_unique_key_on_a_tenant_owned_table_answers_across_the_wall(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, ADR-0005 section 5 (probe I): a uniqueness check bypasses the policy by design, so a
    globally unique natural key reports the existence of a row the writer cannot see. Scoping it
    per tenant is what closes that; the primary key stays global under ADR-0006."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, i.relname
            FROM pg_index x
            JOIN pg_class c ON c.oid = x.indrelid
            JOIN pg_class i ON i.oid = x.indexrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = x.indkey[0]
            WHERE n.nspname = 'public'
              AND c.relname = ANY(%s)
              AND x.indisunique
              AND NOT x.indisprimary
              AND a.attname <> %s
            """,
            [sorted(tenant_owned_tables), "tenant_id"],
        )

        assert cursor.fetchall() == []


def test_a_tenant_scoped_query_with_no_binding_in_force_returns_nothing(alice: Party) -> None:
    """N2, ADR-0005 section 4: the wall denies by returning nothing, which is exactly why the
    application guard exists beside it."""
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {Workspace._meta.db_table}")

        assert cursor.fetchone() == (0,)


def test_a_tenant_scoped_query_with_no_binding_in_force_raises_in_the_application(
    alice: Party,
) -> None:
    """N2, N9, ADR-0005 section 4: the policy's silence is indistinguishable from an empty tenant,
    and nothing in this product fails silently."""
    with pytest.raises(TenantNotBound):
        Workspace.objects.count()


def test_the_binding_does_not_survive_its_transaction(alice: Party) -> None:
    """N2, ADR-0005 section 3 (probes C and D): a session-scoped binding reaches the next request
    on a reused connection, and a bare cast raises on every transaction after the first because the
    setting reverts to the empty string rather than to unset."""
    with tenant_scope(alice.tenant_id):
        assert Workspace.objects.filter(pk=alice.workspace_id).exists()

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {Workspace._meta.db_table}")

        assert cursor.fetchone() == (0,)


def test_a_read_bound_to_one_tenant_does_not_see_another_tenants_row(
    alice: Party, bob: Party
) -> None:
    """C4, N2, T6.1."""
    with tenant_scope(alice.tenant_id):
        assert Workspace.objects.filter(pk=alice.workspace_id).exists()
        assert not Workspace.objects.filter(pk=bob.workspace_id).exists()


def test_an_update_bound_to_one_tenant_does_not_reach_another_tenants_row(
    alice: Party, bob: Party
) -> None:
    """C4, N2."""
    with tenant_scope(alice.tenant_id):
        reached = Workspace.objects.filter(pk=bob.workspace_id).update(name="taken")

    assert reached == 0
    with tenant_scope(bob.tenant_id):
        assert Workspace.objects.get(pk=bob.workspace_id).name != "taken"


def test_a_delete_bound_to_one_tenant_does_not_reach_another_tenants_row(
    alice: Party, bob: Party
) -> None:
    """C4, N2."""
    with tenant_scope(alice.tenant_id):
        reached, _ = Workspace.objects.filter(pk=bob.workspace_id).delete()

    assert reached == 0
    with tenant_scope(bob.tenant_id):
        assert Workspace.objects.filter(pk=bob.workspace_id).exists()


def test_an_insert_cannot_smuggle_a_row_into_another_tenant(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 3 (probe F): WITH CHECK is what makes the write path as closed as
    the read path."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        Workspace.objects.create(id=uuid4(), tenant_id=bob.tenant_id, name="smuggled")


def test_a_foreign_key_cannot_reach_another_tenants_row(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 5 (probes H and N): referential integrity checks bypass the policy
    by design, so a single-column reference happily points at a row in another tenant. Only a
    composite key over (tenant_id, key) closes it."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        Project.objects.create(
            id=uuid4(),
            tenant_id=alice.tenant_id,
            workspace_id=bob.workspace_id,
            name="borrowed",
        )
