"""The row a flush locks, as a table: inside the wall, narrow, its own, vacuumed on its own terms.

Trace: C4 and PRD N2 with ADR-0005 sections 1 and 3 (the counter is a tenant-owned table, which is
C4 reaching a new table rather than a criterion this file invented); ADR-0004 decision 2's two
supporting rules (the version row lives in a narrow dedicated table so its updates stay HOT and the
table stays cached, and that small extremely hot table carries its own aggressive autovacuum
settings, because a row updated thousands of times per second is where bloat starts); M10 (the
per-project version is the resync cursor and has one owner). Beside `test_append_only_log.py`
rather than inside it: both are a table asserted as a table, and neither is the other's behaviour.

**What is asserted is the property each rule protects, never the shape somebody remembered.** The
column list and the tuning values are the implementing window's, and a spec that pins a spelling
inside an acceptance bullet invites a test that pins implementation (specs/log.md, 2026-08-10).
So the width is bounded rather than enumerated, and the tuning is asserted to exist rather than to
equal a number nobody has measured yet.

**The first case is a hook and not a wall, and reading it as the wall is the trap it exists
against.** Everything the wall's own suite does to this table it does because the table appears in
`conftest.py`'s `tenant_owned_tables`, which enumerates from the catalogue **by the tenant column**.
A table without that column does not fail those cases, it disappears from them. So the hook is
pinned here, and the cases themselves stay where they are.

**The grant this table takes is asserted here now, and the paragraph that said it could not be is
struck rather than deleted.** That paragraph read that a grant assertion written from this suite
would prove nothing, because the suite connects as the owner and the owner holds every privilege.
The premise is true and the inference is false: the owner proves nothing about its **own**
privileges and is exactly what can ask about another role's, which `test_append_only_log.py` has
done since MAP-10 (ADR-0005 section 2, correction of 2026-08-07; specs/log.md, 2026-08-11). What
it cost is recorded rather than tidied away: this table and the cursor beside it shipped with
correct grants and nothing watching them, so an `UPDATE` dropped from either breaks the flush in
production with the whole suite green.
"""

import pytest
from django.db import connection

from conftest import the_runtime_grant_on
from mapsift.sync.models import ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0004 decision 2 spells the dedicated table "identifier and version only", which is three
# columns once the wall's own is counted: the tenant every policy keys on (ADR-0005 section 3),
# the project this counts, and the version. A literal rather than a comparison against the project
# table, because reading `accounts.models` from here is the import ADR-0007 section 4's protected
# contract exists to refuse, and a test is not exempt from it.
THE_WIDTH_A_NARROW_TABLE_ADMITS = 3

# ADR-0005 section 2's addition of 2026-08-10, which settles the grant per table by what that table
# guarantees. This row's normal operation IS an in-place increment, so anything narrower than these
# three stops a flush running at all, and the two absences are what stop a counter that only counts
# upward from being emptied under a role that owns nothing.
#
# Stated here rather than shared with the cursor's identical set on purpose: the same addition makes
# a new table state its own, and one constant covering two of them recreates the inherited sentence
# that correction exists against.
THE_GRANT_AN_ALLOCATION_NEEDS = {
    "SELECT": True,
    "INSERT": True,
    "UPDATE": True,
    "DELETE": False,
    "TRUNCATE": False,
}


def _columns_of(table: str) -> frozenset[str]:
    """Every live column of a table, read from the catalogue rather than from a model."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT a.attname
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = %s
              AND a.attnum > 0
              AND NOT a.attisdropped
            """,
            [table],
        )
        return frozenset(row[0] for row in cursor.fetchall())


def _storage_options_of(table: str) -> list[str]:
    """The per-table storage settings the migration left on a relation, or none at all."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT reloptions FROM pg_class WHERE relname = %s", [table])
        options: list[str] | None = cursor.fetchone()[0]
        return options or []


def test_the_counter_is_enumerated_among_the_tables_the_wall_sweeps(
    tenant_owned_tables: frozenset[str],
) -> None:
    """C4, PRD N2, ADR-0005 sections 1 and 3. Carrying the tenant identifier is what puts a table
    into every catalogue-driven case of `tests/test_tenant_isolation.py`, and those cases are what
    hold row-level security enabled and forced, no runtime role owning it, every unique key led by
    the tenant, and the policy set the wall's two decisions name. None of that is asserted here and
    none of it needs to be; what needs asserting is the membership, because the enumeration is by
    column and a counter built without one is not caught by those cases, it is absent from them.

    The width case below is no substitute: a two-column counter of a project and a version passes
    it and sits outside the wall entirely."""
    assert ProjectVersionCounter._meta.db_table in tenant_owned_tables


def test_the_version_row_lives_in_a_table_of_its_own_carrying_nothing_but_what_it_counts() -> None:
    """ADR-0004 decision 2: the whole reason for a dedicated table is that an update to a wide row
    with several indexes stops being HOT, and the project row this would otherwise be a column on
    carries the workspace reference, the name and their indexes. A version integer bolted there
    satisfies M10's ordering and loses exactly what decision 2 bought, which is why the assertion
    is on the width rather than on the ordering. The first line is what makes the second mean
    anything: a table that does not exist reports no columns at all and would pass the width on
    its own."""
    counter = _columns_of(ProjectVersionCounter._meta.db_table)

    assert counter
    assert len(counter) <= THE_WIDTH_A_NARROW_TABLE_ADMITS


def test_the_runtime_role_may_increment_the_counter_and_do_nothing_else_to_it() -> None:
    """ADR-0005 section 2's addition of 2026-08-10. The whole grant is asserted rather than the one
    privilege that has to be present, so a widening fails here as well as a narrowing, and TRUNCATE
    is named for the reason the log's own case names it: it is a separate privilege the wall does
    not reach, and it empties every tenant's counters in one statement.

    **Green from the line it was written on, and that is what it is for.** The grant on disk is
    already right, which makes this a regression guard rather than a driver. What has no other
    witness anywhere is a later migration narrowing it: the whole suite connects as the owner, so
    every flush case in this package stays green while production cannot allocate a version at all
    (specs/log.md, 2026-08-11). A behaviour case cannot buy this one, because behaviour here is
    only observable under a role no test in this module connects as."""
    grant = the_runtime_grant_on(ProjectVersionCounter._meta.db_table)

    assert grant == THE_GRANT_AN_ALLOCATION_NEEDS


def test_the_version_table_carries_autovacuum_settings_of_its_own() -> None:
    """ADR-0004 decision 2's second supporting rule. This is the one hot row per project the
    strategy's Consequences accept, so it is the one table in this schema where the cluster
    default is the wrong policy, and the settings reach the database from the migration or they do
    not exist at all. That they exist is the decision's; which values they take is measurement
    nobody has taken (ADR-0004 decision 3's "tuned against measurement, never guessed"), so a
    numeric assertion here would be a guess wearing a test's clothes."""
    storage = _storage_options_of(ProjectVersionCounter._meta.db_table)

    assert [option for option in storage if option.startswith("autovacuum_")]
