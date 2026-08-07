"""The operation log as a table: inside the wall, and append-only by privilege rather than by care.

Trace: M15 (append-only, sharpened 2026-08-07 from a property a test watches into one the database
holds), C4 and N2 (the wall), ADR-0005 section 2's addition of 2026-08-07 and section 4.

The wall's catalogue-driven cases live in the MAP-3 suite and cover this table the moment it
carries the tenant identifier, which is what the first test here pins.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

import pytest
from django.db import Error, connection, transaction

from conftest import Party
from mapsift.common.binding import TenantNotBound, tenant_scope
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry
from mapsift.sync.services import append_to_the_operation_log
from mapsift.sync.tests.envelopes import an_operation_addressed_at

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0005 section 2: the role the Django runtime connects as, and the one whose grant is what
# makes the log append-only.
RUNTIME_ROLE = "mapsift_app"

# `insufficient_privilege`, which is the same code the wall's own policy raises. That collision is
# the reason the helper below reads the message as well (ADR-0005 section 2's addition).
INSUFFICIENT_PRIVILEGE = "42501"


@contextmanager
def as_the_runtime_role() -> Iterator[None]:
    """Run the block as `mapsift_app`, which is what a request actually connects as.

    There is no second connection to open: `mapsift_app` is NOLOGIN and holds no credential, and
    measured on this cluster the owner's membership in it carries `set_option` false, so a plain
    `SET ROLE` is refused. The grant below is taken inside a transaction this always rolls back,
    so the cluster keeps the privilege set the wall's own suite asserts.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(f"GRANT {RUNTIME_ROLE} TO CURRENT_USER WITH SET TRUE, INHERIT FALSE")
            cursor.execute(f"SET LOCAL ROLE {RUNTIME_ROLE}")
        try:
            yield
        finally:
            transaction.set_rollback(True)


@contextmanager
def refused_by_the_missing_privilege() -> Iterator[None]:
    """Assert the grant refused the write, and not the policy that shares its SQLSTATE.

    `conftest.refused_with` cannot separate these two: PostgreSQL raises 42501 both for a
    privilege a role does not hold and for a row-level security violation, so the code alone
    leaves the wall and the grant indistinguishable (ADR-0005 section 2's addition, section 4).
    """
    with pytest.raises(Error) as caught:
        yield

    refusal = caught.value.__cause__
    assert getattr(refusal, "sqlstate", None) == INSUFFICIENT_PRIVILEGE
    assert "permission denied" in str(refusal)


def _an_entry_of(party: Party) -> ClientHalf:
    return ClientHalf.model_validate(
        an_operation_addressed_at(party, operation_id=uuid4(), mutation_number=0)
    )


def test_the_operation_log_table_is_inside_the_isolation_wall(
    tenant_owned_tables: frozenset[str],
) -> None:
    """C4, N2, ADR-0005 sections 3 and 7: carrying the tenant identifier is what puts a table into
    every catalogue-driven case of the wall's suite, so this is the hook they hang from."""
    assert OperationLogEntry._meta.db_table in tenant_owned_tables


def test_reading_the_operation_log_with_no_tenant_bound_raises_in_the_application(
    alice: Party,
) -> None:
    """C4, N9, ADR-0005 section 4: the policy answers an unbound read with nothing, which reads
    exactly like a tenant that has flushed nothing, so the guard beside it is what tells them
    apart."""
    with pytest.raises(TenantNotBound):
        OperationLogEntry.objects.count()


def test_the_runtime_role_may_append_to_the_log_and_may_not_rewrite_or_remove_an_entry() -> None:
    """M15, ADR-0005 section 2's addition: the whole grant is asserted rather than the two halves
    that must be absent, so a widening in either direction fails here."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT privilege, has_table_privilege(%s, %s, privilege)
            FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE']) AS privilege
            """,
            [RUNTIME_ROLE, OperationLogEntry._meta.db_table],
        )

        assert dict(cursor.fetchall()) == {
            "SELECT": True,
            "INSERT": True,
            "UPDATE": False,
            "DELETE": False,
        }


def test_the_runtime_role_can_still_append_an_entry(alice: Party) -> None:
    """M15: the negative control the two refusals below depend on. A role granted nothing at all
    passes both of them, and the flush would be broken rather than append-only."""
    with tenant_scope(alice.tenant_id), as_the_runtime_role():
        append_to_the_operation_log([_an_entry_of(alice)])

        assert OperationLogEntry.objects.count() == 1


def test_rewriting_an_entry_in_place_is_refused_by_the_privilege_rather_than_matching_no_rows(
    alice: Party,
) -> None:
    """M15: three readings have to be separated here, and asserting that nothing changed satisfies
    all three. The count excludes a statement that matched nothing, and the message excludes the
    policy, which refuses with the same SQLSTATE."""
    with tenant_scope(alice.tenant_id):
        append_to_the_operation_log([_an_entry_of(alice)])

    with tenant_scope(alice.tenant_id), as_the_runtime_role():
        assert OperationLogEntry.objects.count() == 1

        with refused_by_the_missing_privilege(), connection.cursor() as cursor:
            # Assigning the column to itself is not a typo: a rewrite that moved the tenant would
            # trip the policy's WITH CHECK, and 42501 would stop saying which mechanism refused.
            cursor.execute(f"UPDATE {OperationLogEntry._meta.db_table} SET tenant_id = tenant_id")


def test_removing_an_entry_is_refused_by_the_privilege_rather_than_matching_no_rows(
    alice: Party,
) -> None:
    """M15: a log that can be emptied is not append-only, so the delete half of the grant carries
    as much as the update half. Same three readings, separated the same way."""
    with tenant_scope(alice.tenant_id):
        append_to_the_operation_log([_an_entry_of(alice)])

    with tenant_scope(alice.tenant_id), as_the_runtime_role():
        assert OperationLogEntry.objects.count() == 1

        with refused_by_the_missing_privilege(), connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {OperationLogEntry._meta.db_table}")
