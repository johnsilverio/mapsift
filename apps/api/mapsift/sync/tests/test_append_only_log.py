"""The operation log as a table: inside the wall, append-only by privilege, one operation once.

Trace: M15 (append-only, sharpened 2026-08-07 from a property a test watches into one the database
holds), M8 with boundary decision 8 of 2026-08-10 (the same operation never lands twice), C4 and N2
(the wall), ADR-0005 section 2's addition of 2026-08-07 and section 4.

**What the MAP-3 suite covers here is enumerated rather than assumed**, because the sentence this
replaces claimed the whole wall. Its catalogue-driven cases reach this table the moment it carries
the tenant identifier, which is what the first test below pins, and what they reach is four things:
row-level security enabled and forced, no runtime role owning the table, every unique key led by
the tenant, and the policy set the wall's two decisions name. A composite foreign key and the
leading column of a non-unique index are per-table and are reached by none of them, so nothing here
should be read as covering either.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from django.db import Error, connection, transaction

from conftest import UNIQUE_VIOLATION, Party, a_feature_create_claiming, refused_with
from mapsift.common.binding import TenantNotBound, tenant_scope
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry
from mapsift.sync.services import append_to_the_operation_log

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0005 section 2: the role the Django runtime connects as, and the one whose grant is what
# makes the log append-only.
RUNTIME_ROLE = "mapsift_app"

# `insufficient_privilege`, which is the same code the wall's own policy raises. That collision is
# the reason the helper below reads the message as well (ADR-0005 section 2's addition).
INSUFFICIENT_PRIVILEGE = "42501"

# The whole grant on the log, as M15's acceptance names it. `has_table_privilege` answers on all
# five spellings, TRUNCATE included (measured 2026-08-10 against this project's PostgreSQL 18).
APPEND_ONLY_GRANT = {
    "SELECT": True,
    "INSERT": True,
    "UPDATE": False,
    "DELETE": False,
    "TRUNCATE": False,
}


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
    return ClientHalf.model_validate(a_feature_create_claiming(party.tenant_id))


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


def test_the_grant_the_runtime_role_holds_on_the_log_admits_an_append_and_nothing_else() -> None:
    """M15, ADR-0005 section 2's addition: the whole grant is asserted rather than the halves that
    must be absent, so a widening in any direction fails here. TRUNCATE is named because it empties
    the log without touching either of the other two, which the first version of this assertion
    left open."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT privilege, has_table_privilege(%s, %s, privilege)
            FROM unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']) AS privilege
            """,
            [RUNTIME_ROLE, OperationLogEntry._meta.db_table],
        )

        assert dict(cursor.fetchall()) == APPEND_ONLY_GRANT


def test_the_runtime_role_can_still_append_an_entry(alice: Party) -> None:
    """M15: the negative control the three refusals below depend on. A role granted nothing at all
    passes every one of them, and the flush would be broken rather than append-only."""
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


def test_emptying_the_log_wholesale_is_refused_by_the_privilege_rather_than_matching_no_rows(
    alice: Party,
) -> None:
    """M15: TRUNCATE is the third way to empty this table and it is refused by a privilege of its
    own, so a grant narrowed on UPDATE and DELETE alone still leaves the log erasable. Same three
    readings as its two neighbours: TRUNCATE on an empty table succeeds and looks identical, which
    is what the count above it excludes."""
    with tenant_scope(alice.tenant_id):
        append_to_the_operation_log([_an_entry_of(alice)])

    with tenant_scope(alice.tenant_id), as_the_runtime_role():
        assert OperationLogEntry.objects.count() == 1

        with refused_by_the_missing_privilege(), connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE {OperationLogEntry._meta.db_table}")


def test_the_same_operation_never_lands_twice_in_one_tenant(alice: Party) -> None:
    """M8 and boundary decision 8 of 2026-08-10: `operation_id` is the operation's identity, and a
    log admitting it twice cannot carry the idempotency MAP-12 claims over these rows. The SQLSTATE
    is what says the database refused it rather than a check the writer remembered: a Python guard
    ahead of the INSERT raises something with no `unique_violation` under it and fails here."""
    resent = _an_entry_of(alice)

    with tenant_scope(alice.tenant_id):
        append_to_the_operation_log([resent])

    with refused_with(UNIQUE_VIOLATION), tenant_scope(alice.tenant_id):
        append_to_the_operation_log([resent])
