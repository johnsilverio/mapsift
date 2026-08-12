"""What the wall needs to be tested on: two real tenants, and the catalogue's own view of it.

Trace: M1, N2; C4; ADR-0005. The request-level harness at the foot of this file serves the
authenticated request of ADR-0010 and is here rather than beside its suite because the flush
(MAP-10) consumes the same three pieces: a client that is refused what a browser is refused, a
record of which bindings a request opened, and an operation as the client authored it.
"""

from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import pytest
from django.conf import settings
from django.db import Error, connection
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory

from mapsift.accounts.models import Project, User, Workspace
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
UNIQUE_VIOLATION = "23505"
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
    """One user in one tenant, holding one workspace and one project: what the wall reads on."""

    user_id: UUID
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

    return Party(
        user_id=membership.user_id,
        tenant_id=membership.tenant_id,
        workspace_id=workspace_id,
        project_id=project_id,
    )


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


# ADR-0005 section 2: the role the Django runtime connects as, and the one whose per-table grant is
# where each table's own guarantee lives.
RUNTIME_ROLE = "mapsift_app"

# Every privilege a table carries. TRUNCATE is in the list because it is a privilege of its own that
# row-level security does not reach, so an enumeration of four that calls itself the whole grant
# misses exactly the one that empties the table (ADR-0005 section 2, addition of 2026-08-07).
EVERY_TABLE_PRIVILEGE = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")


def the_runtime_grant_on(table: str) -> dict[str, bool]:
    """What `mapsift_app` may do to a table, read from the catalogue rather than from a migration.

    Here rather than in the suites that read it, for the reason `statements_reaching` is here: the
    grant is settled per table by what that table guarantees (ADR-0005 section 2, addition of
    2026-08-10), three tables in this schema now state their own, and an instrument copied per
    module is three instruments that drift.

    **Asking from the owner connection this suite runs on is correct, and the opposite was believed
    for a day.** The owner can prove nothing about its OWN privileges, holding every one of them
    implicitly, and it is exactly what can ask about another role's, because the role travels as a
    parameter (ADR-0005 section 2, correction of 2026-08-07; specs/log.md, 2026-08-11). The cost of
    the inference that ran the other way is on the record: two tables shipped with correct grants
    and no guard over them at all.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT privilege, has_table_privilege(%s, %s, privilege)
            FROM unnest(%s::text[]) AS privilege
            """,
            [RUNTIME_ROLE, table, list(EVERY_TABLE_PRIVILEGE)],
        )
        return dict(cursor.fetchall())


# The request-level harness (ADR-0010). Everything below serves the seam MAP-34 opens.

# ADR-0005 sections 3 and 8: the two parameters a request binds, and the only two statements the
# recorder below looks at.
TENANT_PARAMETER = "mapsift.tenant_id"
USER_PARAMETER = "mapsift.user_id"

# ADR-0005 section 3 fixes the statement as `SELECT set_config('<parameter>', %s, true)`, and the
# recorder reads all three of its arguments. Two of the three ways it can be wrong are invisible to
# a witness that records only which parameter was set and with what value: the interpolated
# spelling differs in the second argument (measurement E) and the session-scoped one differs in the
# third and in nothing else (measurement D).
PLACEHOLDER = "%s"
TRANSACTION_LOCAL = "true"

# What `current_setting(<parameter>, true)` answers once a request is over. Measured 2026-08-07
# against PostgreSQL 18.4 in this project's own stack, and the three states are distinct, which is
# the whole reason this is the instrument for measurement D: a parameter never defined on the
# connection answers NULL, a transaction-scoped binding reverts to the empty string once its
# transaction ends, and a session-scoped one still answers with its value.
REVERTED_WITH_ITS_TRANSACTION = ""

# A decoded JSON document rather than a modelled shape: an operation reaches the API untyped, the
# way a wire payload arrives, which is the same reason the generated-envelope suite uses one.
JsonObject = dict[str, Any]

# Django's execute-wrapper contract (`wrapper(execute, sql, params, many, context)`), spelled in
# `object` rather than `Any` so the lint rule that carries C5 stays on.
_Params = Sequence[object] | None
_Execute = Callable[[str, _Params, bool, dict[str, object]], object]


@dataclass
class BindingsOpened:
    """Which bindings a block of work opened, in order, and how each one was spelled.

    What it buys is the discrimination ADR-0005 section 4 forces on this suite: the wall denies by
    returning nothing, so a refusal is the verification's only if no tenant was ever bound, and the
    wall's if one was. The last two lists carry the arms a value-only witness cannot see:
    `interpolated` names a binding whose value reached the statement as text rather than as a
    parameter (measurement E), and `session_scoped` names one whose statement does not fix
    `is_local` as the literal `true` (measurement D). Both are security controls here rather than
    style preferences, and both are asserted empty, so `tests/test_authenticated_request.py` carries
    the two control tests that stop those assertions from being empty of meaning.
    """

    tenants: list[UUID] = field(default_factory=list)
    users: list[UUID] = field(default_factory=list)
    interpolated: list[str] = field(default_factory=list)
    session_scoped: list[str] = field(default_factory=list)


@contextmanager
def bindings_opened() -> Iterator[BindingsOpened]:
    """Record every tenant and user binding executed on this connection inside the block.

    Scoped to the block rather than offered as a fixture, because a fixture would also record the
    bindings the arrange step opens while it builds its tenants.

    **One statement, one binding, and the limitation is named rather than closed.** The value is
    read positionally from the first parameter, so a single statement binding both the tenant and
    the user attributes both to the first one. That spelling is the one round trip the structural
    performance rule of foundation section 10 actively invites, so it is worth knowing it is not
    supported here: every assertion in the suite fails towards red under it, never towards a false
    green, which is why this is a docstring rather than a defect.
    """
    opened = BindingsOpened()

    def record(
        execute: _Execute,
        sql: str,
        params: _Params,
        many: bool,
        context: dict[str, object],
    ) -> object:
        _record_binding(opened, sql, params)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(record):
        yield opened


def _record_binding(opened: BindingsOpened, sql: str, params: _Params) -> None:
    for parameter, recorded in ((TENANT_PARAMETER, opened.tenants), (USER_PARAMETER, opened.users)):
        if f"set_config('{parameter}'" not in sql:
            continue
        value, scope = _the_value_and_the_scope_of(sql)
        if value == PLACEHOLDER and params:
            recorded.append(UUID(str(params[0])))
        else:
            opened.interpolated.append(parameter)
        if scope != TRANSACTION_LOCAL:
            opened.session_scoped.append(parameter)


def _the_value_and_the_scope_of(sql: str) -> tuple[str, str]:
    """`set_config`'s second and third arguments, as the statement spells them.

    A statement this cannot read reports as both interpolated and session-scoped rather than as
    neither, because an instrument that fails towards "fine" is how a witness goes silent.
    """
    inside = sql.partition("set_config(")[2].partition(")")[0]
    arguments = [argument.strip() for argument in inside.split(",")]
    if len(arguments) != 3:
        return "", ""
    return arguments[1], arguments[2]


@contextmanager
def statements_reaching(table: str) -> Iterator[list[str]]:
    """Every statement whose text names a table, in the order the connection ran them.

    Here rather than in the suites that read it, for the reason `bindings_opened` is here: two of
    them consume it and a connection instrument copied per module is two instruments that drift.
    It names a table and nothing else, so what an implementation spells as the verb, the creation
    on first use or the range arithmetic stays entirely its own.
    """
    seen: list[str] = []

    def record(
        execute: _Execute, sql: str, params: _Params, many: bool, context: dict[str, object]
    ) -> object:
        if table in sql:
            seen.append(sql)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(record):
        yield seen


def a_browser(
    *, authenticated_as: UUID | None = None, carrying_its_csrf_token: bool = True
) -> Client:
    """A client that is refused what a browser is refused, which the default one is not.

    `Client()` carries `enforce_csrf_checks=False` while django-ninja's session auth runs the CSRF
    check itself, so a write test written with the default client reports success about a check it
    never ran (measured 2026-08-07, `specs/dependencies.md` section 1; ADR-0010 decision 1).
    """
    secret, token = _a_csrf_pair()
    browser = Client(enforce_csrf_checks=True)

    if carrying_its_csrf_token:
        browser.defaults[settings.CSRF_HEADER_NAME] = token
    if authenticated_as is not None:
        browser.force_login(User.objects.get(pk=authenticated_as))
    browser.cookies[settings.CSRF_COOKIE_NAME] = secret

    return browser


def _a_csrf_pair() -> tuple[str, str]:
    """The cookie secret and header token a browser carries (ADR-0010 decision 3)."""
    minted = RequestFactory().get("/")
    token = get_token(minted)
    return minted.META["CSRF_COOKIE"], token


def a_feature_create_claiming(
    tenant_id: UUID,
    *,
    operation_id: UUID | None = None,
    client_id: UUID | None = None,
    mutation_number: int = 0,
    project_id: UUID | None = None,
) -> JsonObject:
    """One catalog operation as the client authored it, addressed at a tenant (M8, M9).

    The three client-minted fields are settable because a flush is one client's queue and the
    suites that post more than one operation have to say so (M4, C12); each defaults to what a
    caller that does not care about them would have written anyway. The project joins them for
    the same reason on the other axis: a flush addresses exactly one project too (ADR-0010
    decision 6's addition of 2026-08-10), so a suite about that axis has to be able to say which.

    **The mutation number defaults to zero because zero is the first one** (M10's Shape, settled
    2026-08-11). It read 1 until then, which every caller that does not care about the axis
    inherited, so the whole suite minted streams beginning one above their own start; MAP-13's
    contiguity rule would refuse those as a gap from an absent cursor, and the modules meeting
    that refusal would be the ones with no interest in the axis at all.
    """
    return {
        "operation_id": str(operation_id or uuid4()),
        "client_id": str(client_id or uuid4()),
        "mutation_number": mutation_number,
        "operation_type": "feature.create",
        "operation_schema_version": 1,
        "conflict_rule_version": 1,
        "target": {
            "kind": "feature",
            "tenant_id": str(tenant_id),
            "project_id": str(project_id or uuid4()),
            "layer_id": str(uuid4()),
            "feature_id": str(uuid4()),
        },
        "payload": {},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-08-07T12:00:00Z",
        "mediation": None,
    }


def a_geometry_set_claiming(tenant_id: UUID, *, project_id: UUID | None = None) -> JsonObject:
    """The catalog's other member, whose target is a property rather than a feature (M9).

    The variant matters to this suite rather than being decoration: the two members carry
    structurally different target types, so a rule that reads the tenant off one of them is green
    against a batch of the other, and the same holds of a rule that reads the project.

    **The mutation number is zero here for the reason it defaults to zero above** (M10's Shape,
    settled 2026-08-11). It read 2, minted before the first value of the axis was decided and
    surviving the correction of its sibling because it is a literal rather than a default, which is
    how a stale value outlives the round that retired it.
    """
    return {
        "operation_id": str(uuid4()),
        "client_id": str(uuid4()),
        "mutation_number": 0,
        "operation_type": "feature.geometry.set",
        "operation_schema_version": 1,
        "conflict_rule_version": 1,
        "target": {
            "kind": "property",
            "tenant_id": str(tenant_id),
            "project_id": str(project_id or uuid4()),
            "layer_id": str(uuid4()),
            "feature_id": str(uuid4()),
            "property": "geometry",
        },
        "payload": {"geometry": {"type": "Point", "coordinates": [-47.9, -15.8]}},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-08-07T12:00:00Z",
        "mediation": None,
    }
