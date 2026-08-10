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

**What this module still does not cover, so nothing here reads as the whole story.** The grant this
table takes (`SELECT, INSERT, UPDATE`, ADR-0005 section 2's addition of 2026-08-10) has no case
anywhere and cannot have one from here: the suite connects as the owner, which holds every
privilege, so a grant assertion written against it would prove nothing (ADR-0005 section 2,
correction of 2026-08-07).
"""

import pytest
from django.db import connection

from mapsift.sync.models import ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0004 decision 2 spells the dedicated table "identifier and version only", which is three
# columns once the wall's own is counted: the tenant every policy keys on (ADR-0005 section 3),
# the project this counts, and the version. A literal rather than a comparison against the project
# table, because reading `accounts.models` from here is the import ADR-0007 section 4's protected
# contract exists to refuse, and a test is not exempt from it.
THE_WIDTH_A_NARROW_TABLE_ADMITS = 3


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


def test_the_version_table_carries_autovacuum_settings_of_its_own() -> None:
    """ADR-0004 decision 2's second supporting rule. This is the one hot row per project the
    strategy's Consequences accept, so it is the one table in this schema where the cluster
    default is the wrong policy, and the settings reach the database from the migration or they do
    not exist at all. That they exist is the decision's; which values they take is measurement
    nobody has taken (ADR-0004 decision 3's "tuned against measurement, never guessed"), so a
    numeric assertion here would be a guess wearing a test's clothes."""
    storage = _storage_options_of(ProjectVersionCounter._meta.db_table)

    assert [option for option in storage if option.startswith("autovacuum_")]
