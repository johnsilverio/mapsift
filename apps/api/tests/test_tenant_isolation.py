"""The isolation wall, proven where it lives: in the database.

Trace: C4, N2, T6.1; foundation I4; ADR-0005 (the roles, the binding, the composite keys, and in
section 8 the wall's single deliberate exception). These are invariant acceptance tests and they
may never be weakened (specs/testing.md sections 4 and 9). Every case here is one of ADR-0005's
probes, or its section 8 decision, turned from a measurement into a gate.
"""

from uuid import uuid4

import pytest
from django.db import connection

from conftest import FOREIGN_KEY_VIOLATION, POLICY_VIOLATION, Party, refused_with
from mapsift.accounts.models import Membership, Project, Workspace
from mapsift.accounts.selectors import memberships_of_the_session_user
from mapsift.common.binding import TenantNotBound, UserAlreadyBound, tenant_scope, user_scope

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0005 section 2. The owner is the migrate profile and owns the tables; the other three are
# what an application connects as.
CONNECTING_ROLES = ("mapsift_owner", "mapsift_app", "mapsift_tile", "mapsift_tokens")
RUNTIME_ROLES = ("mapsift_app", "mapsift_tile", "mapsift_tokens")

# One policy as pg_policy answers it, without its expression: the command, whether it is
# permissive, and whether it carries a USING and a WITH CHECK. `*` is FOR ALL, `r` is FOR SELECT.
TENANT_ISOLATION = ("*", True, True, True)
THE_LOGIN_QUESTION = ("r", True, True, False)


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


def test_a_binding_for_a_second_tenant_inside_one_in_force_is_refused_naming_the_rule(
    alice: Party, bob: Party
) -> None:
    """C4, N2, N9, ADR-0005 section 3: the binding is made once per request and once per
    background task, so a scope opened for a second tenant while one is in force is refused by
    name, never restored, because restoring would make nesting look supported (MAP-29)."""
    from mapsift.common.binding import TenantAlreadyBound

    with tenant_scope(alice.tenant_id):
        with pytest.raises(TenantAlreadyBound) as refusal, tenant_scope(bob.tenant_id):
            pytest.fail("the nested binding must be refused before its block runs")

        message = str(refusal.value)
        assert "once per request and once per background task" in message
        assert "ADR-0005 section 3" in message


def test_a_refused_binding_leaves_the_outer_tenant_in_force(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 sections 3 and 4: the refusal comes before the inner binding reaches the
    database, so the wall and the guard never disagree: after it, the guard still passes the
    outer tenant's query and the wall still answers with that tenant's row and nobody else's."""
    from mapsift.common.binding import TenantAlreadyBound

    with tenant_scope(alice.tenant_id):
        with pytest.raises(TenantAlreadyBound), tenant_scope(bob.tenant_id):
            pass

        assert Workspace.objects.filter(pk=alice.workspace_id).exists()
        assert not Workspace.objects.filter(pk=bob.workspace_id).exists()


def test_reentering_the_scope_with_the_same_tenant_is_a_harmless_no_op(alice: Party) -> None:
    """ADR-0005 section 3: one binding per request means the same tenant twice is still one
    binding, so re-entry executes its block and tenant-scoped queries keep answering as that
    tenant (MAP-29)."""
    with tenant_scope(alice.tenant_id):
        with tenant_scope(alice.tenant_id):
            assert Workspace.objects.filter(pk=alice.workspace_id).exists()

        assert Workspace.objects.filter(pk=alice.workspace_id).exists()


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
    with refused_with(POLICY_VIOLATION), tenant_scope(alice.tenant_id):
        Workspace.objects.create(id=uuid4(), tenant_id=bob.tenant_id, name="smuggled")


def test_a_foreign_key_cannot_reach_another_tenants_row(alice: Party, bob: Party) -> None:
    """C4, N2, ADR-0005 section 5 (probes H and N): referential integrity checks bypass the policy
    by design, so a single-column reference happily points at a row in another tenant. Only a
    composite key over (tenant_id, key) closes it."""
    with refused_with(FOREIGN_KEY_VIOLATION), tenant_scope(alice.tenant_id):
        Project.objects.create(
            id=uuid4(),
            tenant_id=alice.tenant_id,
            workspace_id=bob.workspace_id,
            name="borrowed",
        )


def test_the_wall_carries_exactly_the_policies_its_two_decisions_name(
    tenant_owned_tables: frozenset[str],
) -> None:
    """N2, T6.1, ADR-0005 sections 3 and 8, case 6. The whole schema is scanned and compared as
    shape rather than as expression text, for two reasons that are the same reason: a scan for one
    spelling of the key is a grep, and the widening it must catch can arrive in any spelling, on a
    table nobody thought to enumerate, or as a FOR INSERT policy whose key exists only in
    WITH CHECK, where a scan of USING alone never looks."""
    expected = [
        *((table, *TENANT_ISOLATION) for table in tenant_owned_tables),
        (Membership._meta.db_table, *THE_LOGIN_QUESTION),
    ]

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname,
                   p.polcmd::text,
                   p.polpermissive,
                   p.polqual IS NOT NULL,
                   p.polwithcheck IS NOT NULL
            FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
            """
        )

        assert sorted(cursor.fetchall()) == sorted(expected)


def test_a_user_binding_alone_exposes_that_users_rows_and_nobody_elses(
    alice: Party, bob: Party
) -> None:
    """T6.1, C4, ADR-0005 section 8: the exception lives in a policy rather than in an ORM filter,
    so it is proven at the wall, where an application-side answer would also pass."""
    with user_scope(alice.user_id), connection.cursor() as cursor:
        cursor.execute(f"SELECT DISTINCT user_id FROM {Membership._meta.db_table}")

        assert cursor.fetchall() == [(alice.user_id,)]


def test_a_binding_for_a_second_user_inside_one_in_force_is_refused_naming_the_rule(
    alice: Party, bob: Party
) -> None:
    """ADR-0005 section 8 under decision 3: the binding is made once per authenticated request, so
    a scope opened for a second user while one is in force is refused by name, never restored,
    because restoring would make nesting look supported."""
    with user_scope(alice.user_id):
        with pytest.raises(UserAlreadyBound) as refusal, user_scope(bob.user_id):
            pytest.fail("the nested binding must be refused before its block runs")

        message = str(refusal.value)
        assert "once per authenticated request" in message
        assert "ADR-0005 section 8" in message


def test_reentering_the_user_scope_with_the_same_user_is_a_harmless_no_op(alice: Party) -> None:
    """ADR-0005 section 8 under decision 3: one binding per authenticated request means the same
    user twice is still one binding, so re-entry runs its block and the read keeps answering."""
    with user_scope(alice.user_id):
        with user_scope(alice.user_id):
            assert memberships_of_the_session_user().exists()

        assert memberships_of_the_session_user().exists()


def test_the_user_binding_does_not_survive_its_transaction(alice: Party, bob: Party) -> None:
    """N2, ADR-0005 section 8 under decision 3 (probes C and D): the statement after the scope
    answers with nothing rather than raising invalid input syntax for type uuid on an empty
    string. Two parties, so the bounded read proves selectivity rather than scarcity."""
    with user_scope(alice.user_id), connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {Membership._meta.db_table}")

        assert cursor.fetchone() == (1,)

    with connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {Membership._meta.db_table}")

        assert cursor.fetchone() == (0,)


def test_a_user_bound_session_cannot_insert_a_membership_into_another_tenant(
    alice: Party, bob: Party
) -> None:
    """C4, N2, ADR-0005 section 8: the write path stays under the tenant policy alone, which is
    what FOR SELECT buys and what the catalogue case above can only pin as a shape."""
    with refused_with(POLICY_VIOLATION), user_scope(alice.user_id), connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO {Membership._meta.db_table} "
            "(id, tenant_id, user_id, role, licence) VALUES (%s, %s, %s, %s, %s)",
            [uuid4(), bob.tenant_id, alice.user_id, "member", "viewer"],
        )
