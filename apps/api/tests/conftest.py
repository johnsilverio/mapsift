"""What the wall needs to be tested on: two real tenants, and the catalogue's own view of it.

Trace: M1, N2; C4; ADR-0005.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from django.db import connection

from accounts.binding import tenant_scope
from accounts.models import Project, Workspace
from accounts.services import create_personal_account

# ADR-0005 section 3: every policy keys on this column, so carrying it is what puts a table inside
# the wall. The enumeration below reads it from the catalogue rather than from a list somebody
# maintains, which is what N2 means by coverage that holds by construction.
TENANT_COLUMN = "tenant_id"


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
