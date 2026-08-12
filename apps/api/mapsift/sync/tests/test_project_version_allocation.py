"""The ordering key a flush allocates: once, first inside the lock, and rolled back whole.

Trace: ADR-0004 decision 2's RANGE rule (a flush allocates its whole range in one statement and
distributes the N versions internally, so a 500-operation batch takes the lock once) and its LATE
rule as sharpened on 2026-08-10 (what is last is the **lock**, not the allocation: validation,
dedup and the conflict rule run before it, and inside it the order is allocation and then bulk
insert); ADR-0004 decision 4 with its addition of 2026-08-10 (the allocated version reaches disk as
a column beside the log entry, which is what makes that order forced rather than chosen); PRD M10
(the per-project version is server-assigned, monotonic per project, and allocated inside the flush
transaction under the project lock); T2.2's requirement sentence that the flush is a transactional
API call the database orders; C9, I2.

**Two of these look at what the flush does to the version row rather than at what it returns, and
that is the acceptance asking for it rather than this suite drifting.** The RANGE rule is a claim
about the number of times a lock is taken, and the atomicity clause is a claim about what survives
when one of two statements fails; neither has a return value, and reading the code instead is the
instrument this project already refuses. So both go through the route with an instrument on the
connection, which is the coarsest place they are visible at all, and the report that delivered them
names what each cannot see.

**Why the route and never the writer.** `mapsift/common/binding.py`'s `tenant_scope` opens
`transaction.atomic()` itself (read 2026-08-10), so a test whose only transaction is the one its
own context manager opened is green against an implementation that has none. That is the trap
that made the atomicity clause untestable in MAP-10 and testable here, and it is why nothing
below reaches past `POST /api/operations`.

**Everything here addresses a project that exists**, which the older flush suites do not, because
the allocation this module is about is keyed on one.
"""

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from django.db import connection

from conftest import (
    JsonObject,
    Party,
    a_browser,
    a_feature_create_claiming,
    statements_reaching,
)
from mapsift.common.binding import tenant_scope
from mapsift.sync.models import OperationLogEntry, ProjectVersionCounter

pytestmark = pytest.mark.django_db(transaction=True)

OPERATIONS_PATH = "/api/operations"
JSON = "application/json"

# Django's execute-wrapper contract, spelled the way `conftest` spells it: `object` rather than
# `Any`, so the lint rule that carries C5 stays on. Restated here rather than imported, because
# `the_append_refused` below is private to this suite and a shared alias would tie it to whatever
# else came to need one.
_Params = Sequence[object] | None
_Execute = Callable[[str, _Params, bool, dict[str, object]], object]


class TheAppendFailed(Exception):
    """The synthetic failure this suite injects into the append."""


@dataclass
class TheFlushAsTheDatabaseSawIt:
    """What had already reached the database when the append was refused.

    `allocated_before_the_append` carries two things at once and neither is decoration. An empty
    counter after a failed flush is also what a flush that never allocated produces, so the
    rollback assertion alone is satisfied by a flush that fell over earlier for another reason.
    And it is what refuses the escape ADR-0004 decision 2's sharpening names: an implementation
    reading its range from `max(project_version)` off the log and letting the counter statement
    trail behind as a mirror touches the counter *after* the append and never before it, so it
    fails here rather than passing every case in this module.
    """

    allocated: bool = False
    allocated_before_the_append: bool = False


@contextmanager
def the_append_refused() -> Iterator[TheFlushAsTheDatabaseSawIt]:
    """Fail the write that puts the batch into the log, and record what preceded it.

    The fault goes in at the connection and not at a collaborator inside the package, because the
    request still has to travel the whole route for the assertion to mean anything, and because
    the instrument must not know how the allocation is spelled: the counter statement is
    recognised by the table it names, which leaves its verb, its creation-on-first-use and its
    range arithmetic entirely to the implementation.
    """
    seen = TheFlushAsTheDatabaseSawIt()
    log, counter = (
        OperationLogEntry._meta.db_table,
        ProjectVersionCounter._meta.db_table,
    )

    def refuse(
        execute: _Execute, sql: str, params: _Params, many: bool, context: dict[str, object]
    ) -> object:
        # The append is matched on the verb as well as the table, because the escape named in
        # ADR-0004 decision 2's sharpening reads the log before writing it, and a read refused
        # here would never let the flush reach the write this test is about.
        if log in sql and "INSERT" in sql.upper():
            seen.allocated_before_the_append = seen.allocated
            raise TheAppendFailed(sql)
        if counter in sql:
            seen.allocated = True
        return execute(sql, params, many, context)

    with connection.execute_wrapper(refuse):
        yield seen


def _a_flush_of(*operation_ids: UUID, by: Party) -> JsonObject:
    """One client's queue, in one project of one tenant, in contiguous mutation order (M4, C12).

    **From zero, which is where a client's first queue starts** (M10's Shape, settled 2026-08-11).
    It read 1 until then, which minted a stream beginning one above its own start: MAP-13's
    contiguity rule refuses that as a gap from an absent cursor, and this module has no interest in
    the axis at all, so it would have met that refusal for a reason none of its cases are about.
    A fresh installation per call is what keeps the flushes here independent of MAP-12's dedup.
    """
    one_client = uuid4()
    return {
        "operations": [
            a_feature_create_claiming(
                by.tenant_id,
                operation_id=operation_id,
                client_id=one_client,
                mutation_number=number,
                project_id=by.project_id,
            )
            for number, operation_id in enumerate(operation_ids, start=0)
        ]
    }


def _the_version_of_each_operation(party: Party) -> dict[UUID, int]:
    """What the log recorded as each operation's place in its project's order (ADR-0004 4)."""
    with tenant_scope(party.tenant_id):
        return dict(OperationLogEntry.objects.values_list("operation_id", "project_version"))


def test_a_flush_takes_its_projects_version_row_exactly_once_whatever_its_size(
    alice: Party,
) -> None:
    """ADR-0004 decision 2's RANGE rule. Serialisation is not caused by the number of writers but
    by how long each writer holds the lock times how often it takes it, and the measured cost of
    getting this wrong is the worst interactive save going from 40 ms to 782 ms. Three operations
    rather than two because the defect is one acquisition per operation, so the two counts have to
    be unmistakable; the status is the positive control, since a batch refused before it ever
    reached the allocation touches the row zero times and would satisfy a bare inequality."""
    browser = a_browser(authenticated_as=alice.user_id)
    batch = _a_flush_of(uuid4(), uuid4(), uuid4(), by=alice)

    with statements_reaching(ProjectVersionCounter._meta.db_table) as allocation:
        response = browser.post(OPERATIONS_PATH, batch, JSON)

    assert response.status_code == HTTPStatus.OK
    assert len(allocation) == 1


def test_the_operations_of_one_flush_carry_consecutive_versions_in_the_order_they_were_sent(
    alice: Party,
) -> None:
    """ADR-0004 decision 2 and decision 4's addition of 2026-08-10, PRD M10. The RANGE rule
    allocates N versions in one statement and distributes them internally, and an allocation whose
    range never reaches the rows satisfies every other case in this module while leaving the log
    with no order in it at all, which is the log MAP-22's resync cannot read back. The comparison
    is relative because where the counter starts is the implementing window's; that the second
    operation follows the first is M10's, since the client's queue is what the range is
    distributed across."""
    first, second = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    browser.post(OPERATIONS_PATH, _a_flush_of(first, second, by=alice), JSON)

    version_of = _the_version_of_each_operation(alice)
    assert version_of[second] == version_of[first] + 1


def test_a_later_flush_continues_the_projects_version_above_the_flush_before_it(
    alice: Party,
) -> None:
    """PRD M10: the axis is monotonic per project, and it is the cursor a client presents to ask
    for everything since it last looked. A flush that numbers its own operations from the start
    passes the case above and hands two operations the same version, so a client that resyncs from
    the first one never sees the second: silent loss, which is the exact failure ADR-0004 exists to
    close at the root. Asserted as monotonic rather than as contiguous across flushes, because
    contiguity is the mutation number's word on a different axis (M10) and a burnt range is not a
    defect here."""
    earlier, later = uuid4(), uuid4()
    browser = a_browser(authenticated_as=alice.user_id)

    browser.post(OPERATIONS_PATH, _a_flush_of(earlier, by=alice), JSON)
    browser.post(OPERATIONS_PATH, _a_flush_of(later, by=alice), JSON)

    version_of = _the_version_of_each_operation(alice)
    assert version_of[later] > version_of[earlier]


def test_a_failure_appending_rolls_back_the_allocation_that_preceded_it(alice: Party) -> None:
    """T2.2's requirement sentence that the flush is a transactional API call the database orders,
    with ADR-0004's LATE rule, which is what puts two statements inside one critical section and so
    creates a failure that can leave one of them behind. Nothing ran beside the append in MAP-10,
    which is why the clause waited for this task rather than being written where no failure could
    reach it.

    **The direction is the one the sharpening of 2026-08-10 forces, not a preference.** The version
    is a column on the log row and `mapsift_app` holds no `UPDATE` there, so nothing can stamp a
    version onto a row already written; the allocation runs first by construction and the only
    reachable failure is this one. The counter is read back rather than the log, because a burnt
    range is what an allocation surviving its flush looks like, and the next flush would then hand
    out a number the resync cursor never sees.

    The first assertion is what stops the second from passing for the wrong reason twice over: an
    empty counter is also what a flush that never allocated produces, and it is what the mirror
    implementation the sharpening forbids produces, since that one touches the counter only after
    the append."""
    browser = a_browser(authenticated_as=alice.user_id)

    with the_append_refused() as flush, pytest.raises(TheAppendFailed):
        browser.post(OPERATIONS_PATH, _a_flush_of(uuid4(), uuid4(), by=alice), JSON)

    assert flush.allocated_before_the_append
    with tenant_scope(alice.tenant_id):
        assert ProjectVersionCounter.objects.count() == 0
