"""The cursor the server keeps per installation, as a table: inside the wall.

Trace: C4 and PRD N2 with ADR-0005 sections 1 and 3 (the cursor is a tenant-owned table, which is C4
reaching a new table rather than a criterion this file invented); PRD M4's Shape as sharpened
2026-08-11 and corrected the same day, which keys the cursor by clientID, tenant and project
together and is where the tenant of those three comes from, and why that one is the wall's rather
than a preference. Beside `test_project_version_table.py` and `test_append_only_log.py`: all three
are a table asserted as a table, and none is another's behaviour, which lives in
`test_dedup_and_the_echoed_cursor.py`, where the other two of the three are witnessed as behaviour
because that is the only place a key is observable without reaching into a schema.

**This is a hook and not a wall, and reading it as the wall is the trap it exists against.**
Everything the wall's own suite does to this table it does because the table appears in
`conftest.py`'s `tenant_owned_tables`, which enumerates from the catalogue **by the tenant column**.
A table without that column does not fail those cases, it disappears from them, and no assertion
about this table's width or its key closes that.

**The grant this table takes is asserted here now, and the sentence that said it could not be is
struck rather than deleted.** It read that the grant had no case anywhere and could have none from
here, because the suite connects as the owner and the owner holds every privilege. The premise is
true and the inference is false: the owner proves nothing about its **own** privileges and is
exactly what can ask about another role's, which `test_append_only_log.py` has done since MAP-10
(ADR-0005 section 2, correction of 2026-08-07; specs/log.md, 2026-08-11). It reached this docstring
first and `test_project_version_table.py`'s before that, and the hole it left was real: both narrow
tables shipped with correct grants and nothing watching them.

**What this module still does not cover.** The last-seen time M4's Shape names, and the collection
policy that would read it, are MAP-42's and have no column yet.
"""

import pytest

from conftest import the_runtime_grant_on
from mapsift.sync.models import ClientCursor

pytestmark = pytest.mark.django_db(transaction=True)

# ADR-0005 section 2's addition of 2026-08-10, which settles the grant per table by what that table
# guarantees. A cursor is created on an installation's first flush and advanced in place on every
# one after it, so it takes the same three the counter beside it takes, and a grant narrowed to
# SELECT and INSERT strands every installation at its first mutation number.
#
# Stated here rather than shared with the counter's identical set on purpose: the same addition
# makes a new table state its own, and one constant covering two of them recreates the inherited
# sentence that correction exists against. **MAP-42 is what changes this constant**, since expiring
# a cursor is a DELETE, and it changes ADR-0005 in the same pass or the change is not made.
THE_GRANT_AN_ADVANCING_CURSOR_NEEDS = {
    "SELECT": True,
    "INSERT": True,
    "UPDATE": True,
    "DELETE": False,
    "TRUNCATE": False,
}


def test_the_client_cursor_is_enumerated_among_the_tables_the_wall_sweeps(
    tenant_owned_tables: frozenset[str],
) -> None:
    """C4, PRD N2, ADR-0005 sections 1 and 3, M4's Shape. Carrying the tenant identifier is what
    puts a table into every catalogue-driven case of `tests/test_tenant_isolation.py`, and those
    cases are what hold row-level security enabled and forced, no runtime role owning the table,
    every unique key led by the tenant, and the policy set the wall's two decisions name. None of
    that is asserted here and none of it needs to be; the membership is what needs asserting,
    because a cursor keyed on the installation alone is not caught by those cases, it is absent
    from them."""
    assert ClientCursor._meta.db_table in tenant_owned_tables


def test_the_runtime_role_may_advance_the_cursor_and_do_nothing_else_to_it() -> None:
    """ADR-0005 section 2's addition of 2026-08-10. The whole grant is asserted rather than the one
    privilege that has to be present, so a widening fails here as well as a narrowing, and TRUNCATE
    is named for the reason the log's own case names it: it is a separate privilege the wall does
    not reach, and it empties every tenant's cursors in one statement, which under C12 restarts
    every installation's stream from nothing.

    **Green from the line it was written on, and that is what it is for.** The grant on disk is
    already right, which makes this a regression guard rather than a driver. What has no other
    witness anywhere is a later migration narrowing it: the whole suite connects as the owner, so
    every dedup case beside this one stays green while production cannot advance a cursor at all
    (specs/log.md, 2026-08-11). A behaviour case cannot buy this one, because behaviour here is
    only observable under a role no test in this module connects as."""
    grant = the_runtime_grant_on(ClientCursor._meta.db_table)

    assert grant == THE_GRANT_AN_ADVANCING_CURSOR_NEEDS
