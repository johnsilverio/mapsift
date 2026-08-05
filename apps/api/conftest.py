"""What the wall needs to be tested on: two real tenants, and the catalogue's own view of it.

Trace: M1, N2; C4; ADR-0005.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from django.db import Error, connection

from mapsift.accounts.models import Project, Workspace
from mapsift.accounts.services import create_personal_account
from mapsift.common.binding import tenant_scope

# ADR-0005 section 3: every policy keys on this column, so carrying it is what puts a table inside
# the wall. The enumeration below reads it from the catalogue rather than from a list somebody
# maintains, which is what N2 means by coverage that holds by construction.
TENANT_COLUMN = "tenant_id"

# PostgreSQL SQLSTATE codes. They are what says WHICH mechanism refused a write, and the wall has
# more than one that can (ADR-0005).
POLICY_VIOLATION = "42501"
NOT_NULL_VIOLATION = "23502"
FOREIGN_KEY_VIOLATION = "23503"
# PostGIS raises this one from the column's own type modifier, which is why it needs no constraint.
INVALID_PARAMETER_VALUE = "22023"


@contextmanager
def refused_with(sqlstate: str) -> Iterator[None]:
    """Assert which mechanism refused the write, rather than that something did.

    The trap this closes: `pytest.raises(Error)` passes when the row is refused for any reason at
    all, so a composite-key test goes green while the policy, not the key, did the refusing, which
    is the exact defect ADR-0005 probes H and N exist to catch.
    """
    with pytest.raises(Error) as caught:
        yield

    assert getattr(caught.value.__cause__, "sqlstate", None) == sqlstate


@dataclass(frozen=True)
class Party:
    """One tenant holding one workspace and one project: the smallest shape the wall reads on."""

    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID


def _party(email: str, name: str) -> Party:
    membership = create_personal_account(email=email)
    workspace_id, project_id = uuid4(), uuid4()

    with tenant_scope(membership.tenant_id):
        Workspace.objects.create(id=workspace_id, tenant_id=membership.tenant_id, name=name)
        Project.objects.create(
            id=project_id,
            tenant_id=membership.tenant_id,
            workspace_id=workspace_id,
            name=name,
        )

    return Party(tenant_id=membership.tenant_id, workspace_id=workspace_id, project_id=project_id)


def second_project_of(party: Party) -> UUID:
    """A second project inside one tenant, for the invariants that need two of them to show."""
    project_id = uuid4()

    with tenant_scope(party.tenant_id):
        Project.objects.create(
            id=project_id,
            tenant_id=party.tenant_id,
            workspace_id=party.workspace_id,
            name="the other project",
        )

    return project_id


@pytest.fixture
def alice(transactional_db: None) -> Party:
    return _party("alice@example.com", "Alice")


@pytest.fixture
def bob(transactional_db: None) -> Party:
    return _party("bob@example.com", "Bob")


@pytest.fixture
def tenant_owned_tables(transactional_db: None) -> frozenset[str]:
    """Every table carrying the tenant identifier, read from the catalogue rather than listed."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND a.attname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
            """,
            [TENANT_COLUMN],
        )
        return frozenset(row[0] for row in cursor.fetchall())
