"""What the catalogue must say for a spatial read to be fast and closed at the same time.

Trace: C4, N2; foundation I4 and I6; ADR-0013 decision 5 case 7, as corrected 2026-08-25, which
extends ADR-0005 decision 7's list. These are invariant acceptance tests and they may never be
weakened (specs/testing.md sections 4 and 9).

Nothing here performs a spatial read: case 8, the plan half, lives with the selector it reads
through, under `mapsift/layers/tests/`. Six cases here are neither of the ADR's arms: they run the
two container gates against a schema built for the purpose, because how a gate reads the catalogue
is itself a C4 channel and a catalogue gate can only be shown a schema, never told about one.
"""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from django.db import connection

from conftest import (
    EVERY_SCRATCH_TABLE,
    SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER,
    SCRATCH_GEOMETRY_TABLE_NAMING_NO_CONTAINER,
    THE_KEY_COLUMNS_OF_EVERY_INDEX,
)

pytestmark = pytest.mark.django_db(transaction=True)

# Core's own markings are outside this case and have to stay outside it: ADR-0013 decision 2's
# whole plan rests on `uuid_eq` being marked here, so a gate widened to the catalogue would fail a
# clean install and refuse what the ADR depends on.
CORE_SCHEMAS = ("pg_catalog", "information_schema")

# The overload a spatial qual actually uses, and the one ADR-0013 decision 1 disqualifies on its
# own error surface. Named so the enumeration below is shown to be looking at it, and spelled as
# the catalogue spells a signature, which is not how a plan renders the same predicate.
THE_SPATIAL_PREDICATE_IN_THE_CATALOGUE = "public.st_intersects(geometry,geometry)"

# What every key of the sanctioned container prefix is compared under, which is decision 2's
# "built entirely from uuid_eq" written in the catalogue rather than in prose.
THE_LEAKPROOF_EQUALITY = "pg_catalog.uuid_eq(uuid,uuid)"
UUID_OPERATOR_CLASS = "uuid_ops"

# The containers ADR-0013 decision 2 sanctions, as the columns the two that are modelled carry
# (its note of 2026-08-25: a layer set is named by the decision and modelled by nothing).
THE_CONTAINER_KEYS = ("layer_id", "project_id")

TENANT_KEY = "tenant_id"

# The scratch schema the container cases below are shown. `tenant_id` is what puts a table inside
# the wall and so into the enumeration; the geometry column is deliberately not called `geometry`,
# so a reading that found it by name rather than by type would not pass here.
THE_GEOMETRY_COLUMN_OF_A_SCRATCH_TABLE = "footprint"
A_GEOMETRY_COLUMN = f"{THE_GEOMETRY_COLUMN_OF_A_SCRATCH_TABLE} geometry NOT NULL"
A_NULLABLE_GEOMETRY_COLUMN = f"{THE_GEOMETRY_COLUMN_OF_A_SCRATCH_TABLE} geometry"
THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES = f"id uuid NOT NULL, {TENANT_KEY} uuid NOT NULL"

# Taken from the tuple the gates enumerate rather than spelled again beside it. Copied, a schema
# built here goes on naming a column the enumeration above no longer asks about, and every case
# below then passes by having been shown a table that names no container at all.
THE_CONTAINER_THE_SCRATCH_TABLE_NAMES = THE_CONTAINER_KEYS[0]


def the_leakproof_flag_of_every_function_outside_core() -> dict[str, bool]:
    """Every function an extension or this product put in this database, and how each declares.

    Keyed on the schema and the argument types rather than on `regprocedure`, which renders a
    `public` function bare or qualified depending on the connection's search path, or on
    `pg_get_function_identity_arguments`, which carries parameter names an upstream release renames.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT n.nspname || '.' || p.proname || '(' || coalesce((
                       SELECT string_agg(format_type(a.argtype, NULL), ',' ORDER BY a.ord)
                       FROM unnest(p.proargtypes) WITH ORDINALITY AS a(argtype, ord)
                   ), '') || ')',
                   p.proleakproof
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname <> ALL(%s)
            """,
            [list(CORE_SCHEMAS)],
        )
        return dict(cursor.fetchall())


def the_container_btree_every_geometry_table_owes(
    tenant_owned_tables: frozenset[str],
) -> dict[str, dict[str, bool]]:
    """Per tenant-owned table carrying a geometry column, the sanctioned containers it names, each
    answered with whether a btree already leads on the tenant and then that container.

    Answers over every such table and every container key that table carries, so a table that
    gains a geometry column later is examined without anybody editing a list (ADR-0005 decision 7's
    shape). A table naming **no** sanctioned container answers as an empty mapping rather than
    dropping out of the enumeration: ADR-0013 decision 2 sanctions three containers, a table
    carrying none has no sanctioned read shape at all, and a row the reading reaches and then loses
    is the same class of false pass as the expression key MAP-59 was opened to recover.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            THE_KEY_COLUMNS_OF_EVERY_INDEX
            + """
            SELECT geometry_table.relname,
                   named.column_name,
                   named.carried
            FROM pg_class geometry_table
            JOIN pg_namespace n ON n.oid = geometry_table.relnamespace
            LEFT JOIN LATERAL (
                SELECT container.column_name,
                       EXISTS (
                           SELECT 1
                           FROM pg_index x
                           JOIN pg_class i ON i.oid = x.indexrelid
                           JOIN pg_am am ON am.oid = i.relam
                           JOIN index_key_columns tenant_key
                             ON tenant_key.indexrelid = x.indexrelid AND tenant_key.ord = 1
                           JOIN index_key_columns container_key
                             ON container_key.indexrelid = x.indexrelid AND container_key.ord = 2
                           JOIN pg_opclass tenant_ops ON tenant_ops.oid = x.indclass[0]
                           JOIN pg_opclass container_ops ON container_ops.oid = x.indclass[1]
                           WHERE x.indrelid = geometry_table.oid
                             AND am.amname = 'btree'
                             AND x.indisvalid AND x.indisready AND x.indislive
                             AND x.indpred IS NULL
                             AND tenant_key.key_column = %s
                             AND container_key.key_column = container.column_name
                             AND tenant_ops.opcname = %s
                             AND container_ops.opcname = %s
                       ) AS carried
                FROM unnest(%s::text[]) AS container(column_name)
                WHERE EXISTS (
                    SELECT 1 FROM pg_attribute a
                    WHERE a.attrelid = geometry_table.oid
                      AND a.attnum > 0 AND NOT a.attisdropped
                      AND a.attname = container.column_name
                )
            ) AS named ON true
            WHERE n.nspname = 'public'
              AND geometry_table.relkind = 'r'
              AND geometry_table.relname = ANY(%s)
              AND EXISTS (
                  SELECT 1 FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid
                  WHERE a.attrelid = geometry_table.oid
                    AND a.attnum > 0 AND NOT a.attisdropped AND t.typname = 'geometry'
              )
            """,
            [
                TENANT_KEY,
                UUID_OPERATOR_CLASS,
                UUID_OPERATOR_CLASS,
                list(THE_CONTAINER_KEYS),
                sorted(tenant_owned_tables),
            ],
        )
        rows = cursor.fetchall()

    named: dict[str, dict[str, bool]] = {table: {} for table, _, _ in rows}
    for table, container, carried in rows:
        if container is not None:
            named[table][container] = carried
    return named


@pytest.fixture(autouse=True)
def no_scratch_table_left_from_a_killed_run(transactional_db: None) -> None:
    """Guarantee every scratch table is absent before a case in this module reads the catalogue."""
    # Every one and not just this module's: a killed run commits its table (`transaction=True` is
    # autocommit) and any module's leftover poisons the same enumeration. Autouse, and the builders
    # depend on it, because the cases it breaks run earlier here than the builders do.
    with connection.cursor() as cursor:
        for scratch_table in EVERY_SCRATCH_TABLE:
            cursor.execute(f"DROP TABLE IF EXISTS {scratch_table}")


@pytest.fixture
def a_geometry_table_naming_no_container(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """One table inside the wall with a geometry column and none of the sanctioned containers."""
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE {SCRATCH_GEOMETRY_TABLE_NAMING_NO_CONTAINER} "
            f"({THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES}, {A_GEOMETRY_COLUMN})"
        )

    yield SCRATCH_GEOMETRY_TABLE_NAMING_NO_CONTAINER

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {SCRATCH_GEOMETRY_TABLE_NAMING_NO_CONTAINER}")


@contextmanager
def _a_scratch_geometry_table_under(columns: str, index: str) -> Iterator[str]:
    """One geometry-carrying table inside the wall, under one index, dropped when the case ends.

    The columns and the index are the fixture's to spell, because each fixture below differs from
    the sanctioned schema in exactly one of the things ADR-0013 condition 2 asks of an index, and
    that difference is what its case is named for.
    """
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE TABLE {SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER} ({columns})")
        cursor.execute(f"CREATE INDEX ON {SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER} {index}")

    yield SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER}")


@pytest.fixture
def a_geometry_table_naming_one_container(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """One table inside the wall naming a single sanctioned container and carrying its btree."""
    with _a_scratch_geometry_table_under(
        f"{THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES}, "
        f"{THE_CONTAINER_THE_SCRATCH_TABLE_NAMES} uuid NOT NULL, {A_GEOMETRY_COLUMN}",
        f"({TENANT_KEY}, {THE_CONTAINER_THE_SCRATCH_TABLE_NAMES})",
    ) as scratch_table:
        yield scratch_table


@pytest.fixture
def a_geometry_table_whose_btree_leads_on_the_container(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """The sanctioned schema under the same two keys in the other order."""
    with _a_scratch_geometry_table_under(
        f"{THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES}, "
        f"{THE_CONTAINER_THE_SCRATCH_TABLE_NAMES} uuid NOT NULL, {A_GEOMETRY_COLUMN}",
        f"({THE_CONTAINER_THE_SCRATCH_TABLE_NAMES}, {TENANT_KEY})",
    ) as scratch_table:
        yield scratch_table


@pytest.fixture
def a_geometry_table_whose_container_btree_is_partial(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """The sanctioned schema under the sanctioned key order, restricted by a predicate.

    The geometry column is nullable here and the predicate is the one a developer reaches for on
    such a column, which is the partial index ADR-0013 decision 5 case 7 refuses to reason about
    rather than an implausible one built to be refused.
    """
    with _a_scratch_geometry_table_under(
        f"{THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES}, "
        f"{THE_CONTAINER_THE_SCRATCH_TABLE_NAMES} uuid NOT NULL, {A_NULLABLE_GEOMETRY_COLUMN}",
        f"({TENANT_KEY}, {THE_CONTAINER_THE_SCRATCH_TABLE_NAMES}) "
        f"WHERE {THE_GEOMETRY_COLUMN_OF_A_SCRATCH_TABLE} IS NOT NULL",
    ) as scratch_table:
        yield scratch_table


@pytest.fixture
def a_geometry_table_whose_tenant_key_is_not_a_uuid(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """The sanctioned schema with the tenant key typed so its btree half is compared by `texteq`."""
    with _a_scratch_geometry_table_under(
        f"id uuid NOT NULL, {TENANT_KEY} text NOT NULL, "
        f"{THE_CONTAINER_THE_SCRATCH_TABLE_NAMES} uuid NOT NULL, {A_GEOMETRY_COLUMN}",
        f"({TENANT_KEY}, {THE_CONTAINER_THE_SCRATCH_TABLE_NAMES})",
    ) as scratch_table:
        yield scratch_table


@pytest.fixture
def a_geometry_table_whose_container_key_is_not_a_uuid(
    no_scratch_table_left_from_a_killed_run: None,
) -> Iterator[str]:
    """The same, with the container half of the prefix typed away from `uuid_ops` instead."""
    with _a_scratch_geometry_table_under(
        f"{THE_COLUMNS_EVERY_SCRATCH_TABLE_CARRIES}, "
        f"{THE_CONTAINER_THE_SCRATCH_TABLE_NAMES} text NOT NULL, {A_GEOMETRY_COLUMN}",
        f"({TENANT_KEY}, {THE_CONTAINER_THE_SCRATCH_TABLE_NAMES})",
    ) as scratch_table:
        yield scratch_table


def test_no_function_outside_core_declares_itself_leakproof() -> None:
    """C4, N2, ADR-0013 decisions 1 and 5 case 7: a marking is what would let a PostGIS predicate
    be evaluated ahead of the policy, so one added by hand on a live database fails the build. The
    enumeration is shown to still hold the spatial predicate before it is asked to find nothing,
    because a negative over an enumeration that lost its subject is a false pass."""
    outside_core = the_leakproof_flag_of_every_function_outside_core()

    assert THE_SPATIAL_PREDICATE_IN_THE_CATALOGUE in outside_core, (
        f"the enumeration no longer covers {THE_SPATIAL_PREDICATE_IN_THE_CATALOGUE}, so finding "
        "nothing marked says nothing (ADR-0013 decision 5 case 7)"
    )
    marked = sorted(signature for signature, leakproof in outside_core.items() if leakproof)
    assert marked == [], (
        "a function outside core is marked LEAKPROOF, which ADR-0013 decision 1 refuses on any "
        f"connection and in any database: {marked}"
    )


def test_the_equality_the_container_prefix_is_built_from_is_still_leakproof_in_core() -> None:
    """ADR-0013 decision 5 case 7's positive arm: decision 2's whole plan rests on `uuid_eq` being
    marked in core, and a core marking is revocable, PostgreSQL having unmarked `gen_random_uuid()`
    in 2024. Unmarked, the container half of the index condition stops being eligible and every
    container-scoped read silently becomes the tenant-wide one."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT proleakproof FROM pg_proc WHERE oid = %s::regprocedure",
            [THE_LEAKPROOF_EQUALITY],
        )

        assert cursor.fetchone() == (True,)


def test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(
    tenant_owned_tables: frozenset[str],
) -> None:
    """C4, N2, I6, ADR-0013 decision 5 case 7 and condition 2 as corrected 2026-08-25: one btree
    per container, each leading on the tenant and then that container, so the index condition is
    built out of `uuid_eq` alone and the scan never leaves the reader's own prefix. Sized from
    condition 2 rather than from case 7's sentence, which an index already present can be read as
    satisfying: two containers are modelled, so two btrees are owed."""
    named = the_container_btree_every_geometry_table_owes(tenant_owned_tables)

    assert named, (
        "no tenant-owned table carrying a geometry column was examined, so this gate found "
        "nothing because it looked nowhere (ADR-0005 decision 7's shape)"
    )
    missing = sorted(
        (table, container)
        for table, containers in named.items()
        for container, carried in containers.items()
        if not carried
    )
    assert missing == [], (
        "a geometry-carrying table has no valid, non-partial btree leading on the tenant and the "
        f"container under {UUID_OPERATOR_CLASS}, as (table, container key): {missing}"
    )


def test_every_tenant_owned_table_with_a_geometry_column_names_a_sanctioned_container(
    tenant_owned_tables: frozenset[str],
) -> None:
    """C4, N2, ADR-0013 decision 2: a spatial read names a layer, a layer set or a project as well
    as the tenant, so a table carrying a geometry column and none of those has no sanctioned read
    shape at all and every read of it is the tenant-wide one, at 36,930 buffers per read against
    a million rows (2026-08-24). The btree gate beside this one cannot say so, because a table
    naming no container owes no btree and passes it by having nothing to answer for."""
    named = the_container_btree_every_geometry_table_owes(tenant_owned_tables)

    assert named, (
        "no tenant-owned table carrying a geometry column was examined, so this gate found "
        "nothing because it looked nowhere (ADR-0005 decision 7's shape)"
    )
    naming_none = sorted(table for table, containers in named.items() if not containers)
    assert naming_none == [], (
        "a geometry-carrying table names none of the containers ADR-0013 decision 2 sanctions, so "
        f"no read of it can be container-scoped: {naming_none}"
    )


def test_the_container_gate_catches_a_geometry_table_naming_no_sanctioned_container(
    a_geometry_table_naming_no_container: str, a_geometry_table_naming_one_container: str
) -> None:
    """C4, ADR-0013 decision 2: the gate is shown a table it must refuse beside one it must not,
    so the refusal cannot be the enumeration having found nothing, which is the shape the reading
    failed in before: a table naming no container never reached the answer at all, and the
    non-vacuity guard stayed satisfied by whatever else the schema held."""
    tables = frozenset(
        {a_geometry_table_naming_no_container, a_geometry_table_naming_one_container}
    )

    with pytest.raises(AssertionError, match=SCRATCH_GEOMETRY_TABLE_NAMING_NO_CONTAINER):
        test_every_tenant_owned_table_with_a_geometry_column_names_a_sanctioned_container(tables)


def test_the_btree_gate_accepts_a_geometry_table_naming_one_sanctioned_container(
    a_geometry_table_naming_one_container: str,
) -> None:
    """C4, ADR-0013 decision 2: the containers are an `or`, so one of them with its btree is a
    whole sanctioned read shape and the gate owes such a table nothing further. Green from the day
    it was written and kept for stating the `or` on the gate that answers per container: the
    tempting way to reach the case above is to stop asking whether the table carries the container
    column, and under that widening every geometry table owes both modelled containers. Two cases
    turn red on it, this one and the neighbour above (measured 2026-08-27), so what this one adds
    is which of the two gates the widening breaks and not that it is caught at all."""
    tables = frozenset({a_geometry_table_naming_one_container})

    test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(tables)


def test_the_btree_gate_refuses_an_index_that_leads_on_the_container_and_not_the_tenant(
    a_geometry_table_whose_btree_leads_on_the_container: str,
) -> None:
    """C4, N2, ADR-0013 condition 2 and decision 5 case 7: the key order is the security property
    of this gate. Led by the container, the index is swept end to end for the tenant key, which the
    ADR's own pair measured at 553 buffers against 7 under a byte-identical index condition. Shown
    a schema rather than told, because widening the two ordinal positions to accept either order
    left every other case in this file green (measured 2026-08-27)."""
    with pytest.raises(AssertionError, match=SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER):
        test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(
            frozenset({a_geometry_table_whose_btree_leads_on_the_container})
        )


def test_the_btree_gate_refuses_a_container_index_restricted_by_a_predicate(
    a_geometry_table_whose_container_btree_is_partial: str,
) -> None:
    """C4, N2, ADR-0013 decision 5 case 7: a partial index serves the prefix for the rows its
    predicate admits and nothing for the rest, so a read of a row outside it falls back to the
    tenant-wide scan, and the case rejects `indpred IS NOT NULL` outright rather than reasoning
    about which predicates happen to still serve. Shown a schema rather than told, because deleting
    that clause left every other case in this file green while its own failure message went on
    promising a non-partial btree (measured 2026-08-27)."""
    with pytest.raises(AssertionError, match=SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER):
        test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(
            frozenset({a_geometry_table_whose_container_btree_is_partial})
        )


def test_the_btree_gate_refuses_a_container_index_whose_tenant_key_is_not_compared_by_uuid_eq(
    a_geometry_table_whose_tenant_key_is_not_a_uuid: str,
) -> None:
    """C4, ADR-0013 decision 2: "built entirely from `uuid_eq`" is what the operator-class check
    says in the catalogue, and it has two halves that fail independently. This one is the policy's
    own half, which is the one the reader never wrote and cannot see."""
    with pytest.raises(AssertionError, match=SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER):
        test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(
            frozenset({a_geometry_table_whose_tenant_key_is_not_a_uuid})
        )


def test_the_btree_gate_refuses_a_container_index_whose_container_key_is_not_compared_by_uuid_eq(
    a_geometry_table_whose_container_key_is_not_a_uuid: str,
) -> None:
    """C4, ADR-0013 decision 2, on the other half of the same prefix: deleting the two
    operator-class checks together with the access method and the three validity flags left every
    other case in this file green (measured 2026-08-27), and one case per half is what tells a
    deletion of one from a deletion of both."""
    with pytest.raises(AssertionError, match=SCRATCH_GEOMETRY_TABLE_NAMING_A_CONTAINER):
        test_every_tenant_owned_table_with_a_geometry_column_carries_its_container_btrees(
            frozenset({a_geometry_table_whose_container_key_is_not_a_uuid})
        )
