"""The five entities of the account tree, and the rules that hold them together.

Trace: M1 (the tree and the tenant identifier), M3 (identity of every created object); C4;
ADR-0005 section 7 (which tables are inside the wall), ADR-0006 (the identifier variant).

Five cases at the foot are not about an entity. They run the two identifier gates against a schema
built for the purpose, because how a gate reads a column name out of the catalogue is itself part of
what M3 rests on, and a catalogue gate can only be shown a schema, never told about one.
"""

from collections.abc import Callable, Iterator

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import Error, connection

from conftest import (
    EVERY_SCRATCH_TABLE,
    SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES,
    THE_KEY_COLUMNS_OF_EVERY_INDEX,
    Party,
)
from mapsift.accounts.models import Membership, Project, Tenant, Workspace
from mapsift.accounts.services import create_organization_account, create_personal_account
from mapsift.common.binding import tenant_scope

pytestmark = pytest.mark.django_db(transaction=True)

ACCOUNT_TREE_APP = "accounts"

# The scratch schema the four catching cases at the foot are shown. This column is `uuid` and
# carries no default, so the only column either gate can have an opinion about is the identifier.
THE_COLUMN_THAT_MAKES_IT_TENANT_OWNED = "tenant_id uuid NOT NULL"

# The quotes on `"Id"` are the variable under test rather than a style: PostgreSQL renders a name it
# would have to quote WITH them, so `"Id"` matches no raw `attname` (measured on 18.6, 2026-08-26).
# Un-quoting one of these leaves the case looking identical to its neighbour and asserting nothing.
AN_IDENTIFIER_STORED_AS_TEXT = "id text NOT NULL"
A_QUOTED_IDENTIFIER_STORED_AS_TEXT = '"Id" text NOT NULL'
AN_IDENTIFIER_THE_SERVER_ALLOCATES = "id uuid NOT NULL DEFAULT gen_random_uuid()"
A_QUOTED_IDENTIFIER_THE_SERVER_ALLOCATES = '"Id" uuid NOT NULL DEFAULT gen_random_uuid()'

# The one legal schema, for the accepting case at the foot. The defaulted column must stay out of
# every index rather than merely off the leading key: MAP-60 widens how many KEY columns a gate
# reads, and a default parked on a second key column would turn that widening red here.
AN_IDENTIFIER_THE_CLIENT_ALLOCATES = "id uuid NOT NULL"
A_DEFAULT_ON_A_COLUMN_NO_INDEX_COVERS = "recorded_at timestamptz NOT NULL DEFAULT now()"


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
            THE_KEY_COLUMNS_OF_EVERY_INDEX
            + """
            SELECT c.relname, a.attname, format_type(a.atttypid, a.atttypmod)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_index x ON x.indrelid = c.oid AND x.indisprimary
            JOIN index_key_columns leading_key
              ON leading_key.indexrelid = x.indexrelid AND leading_key.ord = 1
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
            WHERE n.nspname = 'public'
              AND c.relname = ANY(%s)
              AND (quote_ident(a.attname) = leading_key.key_column OR a.attname = 'tenant_id')
              AND format_type(a.atttypid, a.atttypmod) <> 'uuid'
            """,
            [sorted(tenant_owned_tables)],
        )
        columns_not_stored_as_uuid = cursor.fetchall()

        assert columns_not_stored_as_uuid == [], (
            "a tenant-owned table stores an identifier as something other than the native uuid "
            "(ADR-0006 sections 1 and 4)"
        )


def test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier(
    tenant_owned_tables: frozenset[str],
) -> None:
    """M3, ADR-0006 section 3: a default there quietly makes the server the allocator the moment a
    code path forgets to send one."""
    with connection.cursor() as cursor:
        cursor.execute(
            THE_KEY_COLUMNS_OF_EVERY_INDEX
            + """
            SELECT c.relname, a.attname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_index x ON x.indrelid = c.oid AND x.indisprimary
            JOIN index_key_columns leading_key
              ON leading_key.indexrelid = x.indexrelid AND leading_key.ord = 1
            JOIN pg_attribute a
              ON a.attrelid = c.oid AND quote_ident(a.attname) = leading_key.key_column
            WHERE n.nspname = 'public' AND c.relname = ANY(%s) AND a.atthasdef
            """,
            [sorted(tenant_owned_tables)],
        )
        identifiers_the_server_would_allocate = cursor.fetchall()

        assert identifiers_the_server_would_allocate == [], (
            "a tenant-owned table lets the server allocate an identifier (ADR-0006 section 3)"
        )


def test_the_server_never_allocates_an_identifier_for_an_object_a_client_creates(
    alice: Party,
) -> None:
    """M3, ADR-0006 section 3: the same rule one level up from the column default, because a
    generator on the model is the server allocating just as much as one in the database is."""
    with pytest.raises(Error), tenant_scope(alice.tenant_id):
        Workspace.objects.create(tenant_id=alice.tenant_id, name="unnamed")


@pytest.fixture(autouse=True)
def no_scratch_table_left_from_a_killed_run(transactional_db: None) -> None:
    """Guarantee every scratch table is absent before a case in this module reads the catalogue."""
    # Every one and not just this module's: a killed run commits its table (`transaction=True` is
    # autocommit) and either module's leftover enters the same enumeration. Autouse, and the builder
    # depends on it, because both gates it breaks run earlier in this file than the builder does.
    with connection.cursor() as cursor:
        for scratch_table in EVERY_SCRATCH_TABLE:
            cursor.execute(f"DROP TABLE IF EXISTS {scratch_table}")


@pytest.fixture
def a_table_whose_identifier_is(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[Callable[[str], frozenset[str]]]:
    """Build one table inside the wall on the given identifier column, and answer as an enumeration.

    Answers in the shape a catalogue gate takes its tables in, so the gate under test is reached the
    way the suite reaches it rather than through a second reading written here.
    """

    def declared_as(identifier_column: str) -> frozenset[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE TABLE {SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES} "
                f"({identifier_column} PRIMARY KEY, {THE_COLUMN_THAT_MAKES_IT_TENANT_OWNED})"
            )

        return frozenset({SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES})

    yield declared_as

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES}")


@pytest.fixture
def a_table_whose_only_default_is_off_its_identifier(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[frozenset[str]]:
    """Build one table inside the wall carrying a default no rule forbids, and answer as an
    enumeration.

    Its own schema rather than the builder's, because the builder's carries no column a gate is
    allowed to find anything on, which is the property the four catching cases rest on.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE {SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES} "
            f"({AN_IDENTIFIER_THE_CLIENT_ALLOCATES} PRIMARY KEY, "
            f"{THE_COLUMN_THAT_MAKES_IT_TENANT_OWNED}, "
            f"{A_DEFAULT_ON_A_COLUMN_NO_INDEX_COVERS})"
        )

    yield frozenset({SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES})

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {SCRATCH_TABLE_OF_THE_IDENTIFIER_GATES}")


def test_the_uuid_type_gate_catches_a_text_identifier_whose_column_name_is_quoted(
    a_table_whose_identifier_is: Callable[[str], frozenset[str]],
) -> None:
    """M3, ADR-0006 sections 1 and 4: what the rule forbids is an identifier stored as anything but
    the native sixteen bytes, and a column name PostgreSQL renders quoted changes nothing about what
    is stored. A reading that loses that column returns nothing rather than something odd, so the
    gate never examines it and the failure mode is a false pass. The gate is handed that one table
    and nothing else, so a refusal here can be about no other schema."""
    tables = a_table_whose_identifier_is(A_QUOTED_IDENTIFIER_STORED_AS_TEXT)

    with pytest.raises(AssertionError):
        test_every_identifier_is_stored_as_the_native_uuid_type(tables)


def test_the_uuid_type_gate_catches_a_text_identifier_whose_column_name_is_plain(
    a_table_whose_identifier_is: Callable[[str], frozenset[str]],
) -> None:
    """M3, ADR-0006 sections 1 and 4: the arm that says the case above is red for the quoting. Same
    defect, same harness, plain name, and this spelling has always been caught, so how the name
    renders is the only thing left between them. Green from the day it was written and not deletable
    for it: a reading that reached the quoted name by losing the plain one satisfies the case above
    on its own, and the real schema carries no quoted column name to notice with."""
    tables = a_table_whose_identifier_is(AN_IDENTIFIER_STORED_AS_TEXT)

    with pytest.raises(AssertionError):
        test_every_identifier_is_stored_as_the_native_uuid_type(tables)


def test_the_identifier_default_gate_catches_a_server_allocated_identifier_whose_name_is_quoted(
    a_table_whose_identifier_is: Callable[[str], frozenset[str]],
) -> None:
    """M3, ADR-0006 section 3: a default there makes the server the allocator the moment a code path
    forgets to send one, and the column name it hides behind is not part of that rule. The same
    reading loses the same column here, so this gate is blind to the same schema the one above is,
    and the two are separate guarantees rather than one asserted twice."""
    tables = a_table_whose_identifier_is(A_QUOTED_IDENTIFIER_THE_SERVER_ALLOCATES)

    with pytest.raises(AssertionError):
        test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier(tables)


def test_the_identifier_default_gate_catches_a_server_allocated_identifier_whose_name_is_plain(
    a_table_whose_identifier_is: Callable[[str], frozenset[str]],
) -> None:
    """M3, ADR-0006 section 3: the arm that says the case above is red for the quoting. Green from
    the day it was written and not deletable for it, and this gate needs it more than its neighbour
    does: the real schema carries no column default anywhere, so nothing else in the suite has ever
    watched this gate fire."""
    tables = a_table_whose_identifier_is(AN_IDENTIFIER_THE_SERVER_ALLOCATES)

    with pytest.raises(AssertionError):
        test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier(tables)


def test_the_identifier_default_gate_accepts_a_default_on_a_column_no_index_covers(
    a_table_whose_only_default_is_off_its_identifier: frozenset[str],
) -> None:
    """M3, ADR-0006 section 3: what the rule forbids is a default on the identifier, so a default on
    a column no key reaches is a schema the rule permits and the gate must stay quiet about it.
    Green from the day it was written and not deletable for it: the tempting widening, reading every
    column rather than the key, leaves both cases above red and the real schema green, because that
    schema carries no column default at all. Measured 2026-08-26, the whole suite runs
    byte-identical under that widening and this is the only case anywhere that turns red."""
    test_no_tenant_owned_table_carries_a_server_side_default_for_its_identifier(
        a_table_whose_only_default_is_off_its_identifier
    )
