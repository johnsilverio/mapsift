"""What a container-scoped bounding-box read answers, and the plan it takes under the policy.

Trace: C4, N2, M2; foundation I4 and I6; ADR-0013 decision 5 case 8, as corrected 2026-08-25,
which extends ADR-0005 decision 7's list, and decision 2 for the shape the seam publishes.
Invariant acceptance tests; they may never be weakened (specs/testing.md sections 4 and 9).

What the plan cases witness is the **shape of the index path when that path is taken**, and not
that the planner takes it in production, and not any timing. The two answer cases sit beside them
because a plan case says nothing about the rows: a read that honours its container and reads a box
of its own plans identically. Case 7, the catalogue half, is cross-package and lives in
`apps/api/tests/`.
"""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import pytest
from django.contrib.gis.geos import Point, Polygon
from django.db import connection
from django.db.models import QuerySet

from conftest import Party, second_project_of
from mapsift.common.binding import tenant_scope
from mapsift.layers.models import Feature, Layer
from mapsift.layers.rules import GeometryKind, StorageClass
from mapsift.layers.selectors import (
    features_of_a_layer_intersecting,
    features_of_a_project_intersecting,
)

pytestmark = pytest.mark.django_db(transaction=True)

# The two btrees ADR-0013 condition 2 names, as the catalogue names them. `Index Name` is the only
# field measured to tell the sanctioned schema from one whose index does not lead on the tenant:
# on that pair the index condition came back byte-identical and so did every row count
# (ADR-0013 decision 5's correction of 2026-08-25).
THE_LAYER_CONTAINER_BTREE = "feature_layer_by_tenant"
THE_PROJECT_CONTAINER_BTREE = "feature_project_by_tenant"

# The predicate that must stay behind the policy as a heap filter, because nothing in PostGIS is
# leakproof and ADR-0013 decision 1 refuses to assert that anything is. Spelled as EXPLAIN renders
# it in a node's condition, which is not the catalogue signature the case 7 module reads.
THE_SPATIAL_PREDICATE_IN_A_PLAN = "st_intersects"

# What `SHOW enable_seqscan` must answer for the forcing below to be in force.
SEQUENTIAL_SCAN_DISABLED = "off"

STORAGE_FRAME_SRID = 4674
A_BOX_OVER_THE_FEDERAL_DISTRICT = Polygon.from_bbox((-48.0, -16.0, -47.8, -15.7))
A_BOX_OVER_THE_FEDERAL_DISTRICT.srid = STORAGE_FRAME_SRID

# The plan fixture's holdings, every one of them inside that box, so what narrows that read is the
# container it names and never the box, which is the property the law of ADR-0013 rests on. The
# answer fixture does the opposite on purpose and counts nothing, so it spells its own sizes.
FEATURES_IN_THE_LAYER_THE_READ_NAMES = 4
FEATURES_IN_A_SECOND_LAYER_OF_THE_SAME_PROJECT = 3
FEATURES_THE_PROJECT_THE_READ_NAMES_HOLDS = (
    FEATURES_IN_THE_LAYER_THE_READ_NAMES + FEATURES_IN_A_SECOND_LAYER_OF_THE_SAME_PROJECT
)
FEATURES_IN_ANOTHER_PROJECT_OF_THE_SAME_TENANT = 40
FEATURES_THE_OTHER_TENANT_HOLDS_IN_THE_SAME_BOX = 6

# The two places the answer cases put a feature at. What separates them is the longitude alone, so
# a read that kept the box and lost the container fails on the same assertion as one that kept the
# container and lost the box.
A_PLACE_INSIDE_THE_BOX = (-47.9, -15.8)
A_PLACE_OUTSIDE_THE_BOX = (-47.0, -15.8)


# `Any` because an EXPLAIN node is a decoded JSON document rather than a modelled shape: which keys
# it carries is PostgreSQL's to change between majors and differs by node type, so the case reads
# the few it names and asserts nothing about the rest.
PlanNode = dict[str, Any]


@dataclass(frozen=True)
class TheReadersHoldings:
    """What the bound tenant owns, as the two containers a spatial read may name."""

    layer_id: UUID
    project_id: UUID


@dataclass(frozen=True)
class TheAnswerEachContainerOwes:
    """The identifiers each of the two reads must come back with, and no others."""

    layer_id: UUID
    project_id: UUID
    of_that_layer: frozenset[UUID]
    of_that_project: frozenset[UUID]


@dataclass(frozen=True)
class ThePlan:
    """One EXPLAIN of one read, reduced to the fields ADR-0013 decision 5 case 8 asserts over."""

    index_names: tuple[str, ...]
    index_conditions: tuple[str, ...]
    filters: tuple[str, ...]
    orderings: tuple[str, ...]
    index_entries: int


def _every_node(node: PlanNode) -> list[PlanNode]:
    return [node, *(deeper for child in node.get("Plans", []) for deeper in _every_node(child))]


def _across_every_loop(node: PlanNode, key: str) -> float:
    """One of a node's row counts as a total, since EXPLAIN renders it averaged over its loops."""
    return float(node.get(key, 0)) * int(node["Actual Loops"])


def _index_entries_visited(nodes: list[PlanNode]) -> int:
    """How many index entries the scan actually visited, read per node type rather than by formula.

    `Actual Rows + Rows Removed by Filter` is not that number: it was measured returning 180 on a
    bitmap path and 90 on an index-scan path for the same read at the same instant, because the
    bitmap path reports the entries on its own node and the heap rows on the one above it
    (ADR-0013 decision 5's correction of 2026-08-25).
    """
    bitmap = [node for node in nodes if node["Node Type"] == "Bitmap Index Scan"]
    if bitmap:
        return round(sum(_across_every_loop(node, "Actual Rows") for node in bitmap))
    return round(
        sum(
            _across_every_loop(node, "Actual Rows")
            + _across_every_loop(node, "Rows Removed by Filter")
            for node in nodes
            if node["Node Type"] in ("Index Scan", "Index Only Scan")
        )
    )


def _orderings_of(nodes: list[PlanNode]) -> tuple[str, ...]:
    """Every ordering a plan carries, the one an index provides and the one a sort node imposes.

    `Order By` alone reads none of the orderings a Django developer writes: `Distance()` compiles
    to `st_distance(...)` and lands as a `Sort` node under `Sort Key`, while `Order By` is emitted
    only where the index itself provides the order (measured 2026-08-27, ten of ten green).
    """
    provided_by_an_index = [node["Order By"] for node in nodes if node.get("Order By")]
    imposed_by_a_sort = [key for node in nodes for key in node.get("Sort Key", [])]

    return tuple(provided_by_an_index) + tuple(imposed_by_a_sort)


def the_forced_index_plan_of(read: QuerySet[Feature]) -> ThePlan:
    """EXPLAIN one read with the sequential scan disabled, and reduce it to what case 8 asserts.

    Forcing is the ruling of ADR-0013 decision 5's note, and it buys independence from
    `st_intersects`'s declared cost of 5000, a constant this product does not own and upstream can
    change; growing the fixture until the planner chooses unforced was refused, because that turns
    a gate into a measurement.
    """
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL enable_seqscan = off")
        # The forcing is read back rather than trusted, because losing it is silent: with the
        # statement above replaced by `SELECT 1` this whole suite came back byte-identical, so
        # nothing else here would notice the ruling above having stopped holding (2026-08-27).
        cursor.execute("SHOW enable_seqscan")
        forcing = cursor.fetchone()

    assert forcing == (SEQUENTIAL_SCAN_DISABLED,), (
        "the sequential scan is not disabled on the connection this read runs on, so the forcing "
        "ADR-0013 decision 5's note rules is inert and the plan below is whichever one the cost "
        f"model happened to choose: SHOW enable_seqscan answered {forcing}"
    )

    explained = read.explain(
        format="JSON", analyze=True, buffers=True, costs=False, timing=False, summary=False
    )
    nodes = _every_node(json.loads(explained)[0]["Plan"])

    return ThePlan(
        index_names=tuple(node["Index Name"] for node in nodes if "Index Name" in node),
        index_conditions=tuple(node["Index Cond"] for node in nodes if node.get("Index Cond")),
        filters=tuple(node["Filter"] for node in nodes if node.get("Filter")),
        orderings=_orderings_of(nodes),
        index_entries=_index_entries_visited(nodes),
    )


def _a_layer_of(tenant_id: UUID, project_id: UUID, name: str) -> Layer:
    return Layer.objects.create(
        id=uuid4(),
        tenant_id=tenant_id,
        project_id=project_id,
        name=name,
        geometry_kind=GeometryKind.POINT,
        storage_class=StorageClass.ELEMENT,
    )


def _features_of(layer: Layer, at: tuple[float, float], how_many: int) -> frozenset[UUID]:
    """Put features of one layer at one place, and answer with the identifiers they carry."""
    longitude, latitude = at
    features = [
        Feature(
            id=uuid4(),
            tenant_id=layer.tenant_id,
            project_id=layer.project_id,
            layer_id=layer.pk,
            geometry=Point(longitude, latitude + which * 0.001, srid=STORAGE_FRAME_SRID),
        )
        for which in range(how_many)
    ]
    Feature.objects.bulk_create(features)

    return frozenset(feature.pk for feature in features)


@pytest.fixture
def a_tenant_holding_more_than_the_read_names(alice: Party, bob: Party) -> TheReadersHoldings:
    """Two projects and three layers for the reader, and a second tenant inside the same box.

    The other tenant is what makes "no foreign entry" a claim rather than a scarcity, and the
    forty of the reader's own forty-seven features that sit in another project are what makes the
    container rather than the box the thing that narrows the read.
    """
    another_project = second_project_of(alice)

    with tenant_scope(alice.tenant_id):
        the_layer = _a_layer_of(alice.tenant_id, alice.project_id, "cover")
        _features_of(the_layer, A_PLACE_INSIDE_THE_BOX, FEATURES_IN_THE_LAYER_THE_READ_NAMES)
        beside_it = _a_layer_of(alice.tenant_id, alice.project_id, "parcels")
        _features_of(
            beside_it, A_PLACE_INSIDE_THE_BOX, FEATURES_IN_A_SECOND_LAYER_OF_THE_SAME_PROJECT
        )
        elsewhere = _a_layer_of(alice.tenant_id, another_project, "imagery outlines")
        _features_of(
            elsewhere, A_PLACE_INSIDE_THE_BOX, FEATURES_IN_ANOTHER_PROJECT_OF_THE_SAME_TENANT
        )

    with tenant_scope(bob.tenant_id):
        theirs = _a_layer_of(bob.tenant_id, bob.project_id, "cover")
        _features_of(
            theirs, A_PLACE_INSIDE_THE_BOX, FEATURES_THE_OTHER_TENANT_HOLDS_IN_THE_SAME_BOX
        )

    # Without statistics both container keys fall back to one default selectivity constant, the two
    # btrees tie on cost, and which one the plan names becomes arbitrary (measured 2026-08-27).
    with connection.cursor() as cursor:
        cursor.execute(f"ANALYZE {Feature._meta.db_table}")

    return TheReadersHoldings(layer_id=the_layer.pk, project_id=alice.project_id)


@pytest.fixture
def a_tenant_holding_features_on_both_sides_of_the_box(
    alice: Party, bob: Party
) -> TheAnswerEachContainerOwes:
    """Every container the reader owns holds features inside the box and features outside it.

    Both halves are load-bearing and neither is in the plan fixture beside it, which puts every
    feature inside the box on purpose. Without the features outside it a read that discards the
    caller's box answers correctly; without the second project and the second tenant a read that
    discards its container does.
    """
    another_project = second_project_of(alice)

    with tenant_scope(alice.tenant_id):
        the_layer = _a_layer_of(alice.tenant_id, alice.project_id, "cover")
        of_that_layer = _features_of(the_layer, A_PLACE_INSIDE_THE_BOX, 2)
        _features_of(the_layer, A_PLACE_OUTSIDE_THE_BOX, 2)

        beside_it = _a_layer_of(alice.tenant_id, alice.project_id, "parcels")
        of_the_second_layer = _features_of(beside_it, A_PLACE_INSIDE_THE_BOX, 1)
        _features_of(beside_it, A_PLACE_OUTSIDE_THE_BOX, 1)

        elsewhere = _a_layer_of(alice.tenant_id, another_project, "imagery outlines")
        _features_of(elsewhere, A_PLACE_INSIDE_THE_BOX, 3)

    with tenant_scope(bob.tenant_id):
        theirs = _a_layer_of(bob.tenant_id, bob.project_id, "cover")
        _features_of(theirs, A_PLACE_INSIDE_THE_BOX, 2)

    return TheAnswerEachContainerOwes(
        layer_id=the_layer.pk,
        project_id=alice.project_id,
        of_that_layer=of_that_layer,
        of_that_project=of_that_layer | of_the_second_layer,
    )


def test_a_layer_scoped_read_answers_the_features_of_that_layer_inside_the_box(
    alice: Party, a_tenant_holding_features_on_both_sides_of_the_box: TheAnswerEachContainerOwes
) -> None:
    """M2, C4, ADR-0013 decisions 2 and 4: the container narrows the read and so does the box the
    caller hands over, and no plan case in this module can say either. Measured 2026-08-27: a
    selector that honours its container and intersects a box of its own passes all ten of them,
    because which box the heap filter names changes no index condition, no index name and no entry
    count."""
    owed = a_tenant_holding_features_on_both_sides_of_the_box

    with tenant_scope(alice.tenant_id):
        answered = {
            feature.pk
            for feature in features_of_a_layer_intersecting(
                owed.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT
            )
        }

    assert answered == owed.of_that_layer


def test_a_project_scoped_read_answers_the_features_of_that_project_inside_the_box(
    alice: Party, a_tenant_holding_features_on_both_sides_of_the_box: TheAnswerEachContainerOwes
) -> None:
    """M2, C4, ADR-0013 decisions 2 and 4, on the second of the two containers condition 2 names:
    the answer spans every layer of that project and still stops at the box."""
    owed = a_tenant_holding_features_on_both_sides_of_the_box

    with tenant_scope(alice.tenant_id):
        answered = {
            feature.pk
            for feature in features_of_a_project_intersecting(
                owed.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT
            )
        }

    assert answered == owed.of_that_project


def test_a_layer_scoped_read_builds_its_index_condition_from_the_tenant_and_the_layer(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decisions 2 and 5 case 8: both halves of the condition are `uuid_eq`, the
    policy's own half included, so the scan never leaves the reader's prefix with nothing marked.
    The condition is proven present before anything is claimed about it, because the same read
    forced to a sequential scan yields an empty condition every assertion over it passes on."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_layer_intersecting(holdings.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.index_conditions, f"the read took no index path at all: {plan}"
    not_comparing_the_tenant = [
        condition for condition in plan.index_conditions if "tenant_id" not in condition
    ]
    assert not_comparing_the_tenant == [], (
        f"an index condition of this read does not compare the tenant: {plan}"
    )
    not_comparing_the_layer = [
        condition for condition in plan.index_conditions if str(holdings.layer_id) not in condition
    ]
    assert not_comparing_the_layer == [], (
        f"an index condition of this read does not compare the layer it names: {plan}"
    )


def test_a_project_scoped_read_builds_its_index_condition_from_the_tenant_and_the_project(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decisions 2 and 5 case 8: the project is a sanctioned container beside the
    layer, and condition 2 as corrected 2026-08-25 owes it a btree of its own rather than a
    position inside the layer's, which on PostgreSQL 17 costs the tenant's whole index prefix."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_project_intersecting(holdings.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.index_conditions, f"the read took no index path at all: {plan}"
    not_comparing_the_tenant = [
        condition for condition in plan.index_conditions if "tenant_id" not in condition
    ]
    assert not_comparing_the_tenant == [], (
        f"an index condition of this read does not compare the tenant: {plan}"
    )
    not_comparing_the_project = [
        condition
        for condition in plan.index_conditions
        if str(holdings.project_id) not in condition
    ]
    assert not_comparing_the_project == [], (
        f"an index condition of this read does not compare the project it names: {plan}"
    )


def test_a_layer_scoped_read_takes_the_btree_that_leads_on_the_tenant_and_the_layer(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decision 5 case 8: the index the plan names is the only field measured to
    separate the sanctioned schema from one whose index does not lead on the tenant, where the
    condition, the rows and the rows removed by filter all came back identical (ADR-0013 decision
    5's correction of 2026-08-25, which holds the figures that pair cost)."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_layer_intersecting(holdings.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert set(plan.index_names) == {THE_LAYER_CONTAINER_BTREE}


def test_a_project_scoped_read_takes_the_btree_that_leads_on_the_tenant_and_the_project(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decision 5 case 8, on the second of the two containers condition 2 names."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_project_intersecting(holdings.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert set(plan.index_names) == {THE_PROJECT_CONTAINER_BTREE}


def test_a_layer_scoped_read_leaves_the_geometry_predicate_behind_the_policy(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, ADR-0013 decisions 1 and 2: an index condition is evaluated ahead of the row-security
    check, so a predicate that names its arguments in an error message must never reach one. Where
    it does appear is asserted too, because a negative over a field that defaults to empty passes
    on a plan that has no index condition at all."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_layer_intersecting(holdings.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.index_conditions, f"the read took no index path at all: {plan}"
    assert [
        condition
        for condition in plan.index_conditions
        if THE_SPATIAL_PREDICATE_IN_A_PLAN in condition
    ] == []
    assert [
        predicate for predicate in plan.filters if THE_SPATIAL_PREDICATE_IN_A_PLAN in predicate
    ] != []


def test_a_project_scoped_read_leaves_the_geometry_predicate_behind_the_policy(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, ADR-0013 decisions 1 and 2, on the second of the two containers condition 2 names."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_project_intersecting(holdings.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.index_conditions, f"the read took no index path at all: {plan}"
    assert [
        condition
        for condition in plan.index_conditions
        if THE_SPATIAL_PREDICATE_IN_A_PLAN in condition
    ] == []
    assert [
        predicate for predicate in plan.filters if THE_SPATIAL_PREDICATE_IN_A_PLAN in predicate
    ] != []


def test_a_layer_scoped_read_visits_no_index_entry_outside_that_layer(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decision 5 case 8: the property is zero foreign entries rather than an
    exact count, so the magnitude is bounded rather than equated. The lower bound is what keeps a
    plan that visited nothing from passing as a plan that visited only the reader's."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_layer_intersecting(holdings.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert 0 < plan.index_entries <= FEATURES_IN_THE_LAYER_THE_READ_NAMES, (
        f"the scan visited {plan.index_entries} index entries for a layer holding "
        f"{FEATURES_IN_THE_LAYER_THE_READ_NAMES}: {plan}"
    )


def test_a_project_scoped_read_visits_no_index_entry_outside_that_project(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """C4, I6, ADR-0013 decision 5 case 8, on the second of the two containers condition 2 names."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_project_intersecting(holdings.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert 0 < plan.index_entries <= FEATURES_THE_PROJECT_THE_READ_NAMES_HOLDS, (
        f"the scan visited {plan.index_entries} index entries for a project holding "
        f"{FEATURES_THE_PROJECT_THE_READ_NAMES_HOLDS}: {plan}"
    )


def test_a_layer_scoped_read_takes_no_ordering_path(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """ADR-0013's Consequences: the leakproof gate governs quals and not `ORDER BY` pathkeys, so a
    nearest-neighbour ordering takes the plain GiST with nothing marked and does visit entries a
    tenant cannot see. That path has no owner and this case does not give it one; what it refuses
    is that path arriving here disguised as a clean plan. The ordering is read before the index
    condition and not after: a nearest-neighbour ordering spelled with the raw operator takes the
    condition away with it, so this case answered under the other assertion's name and never once
    under its own (measured 2026-08-27, across four mutants)."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_layer_intersecting(holdings.layer_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.orderings == ()
    assert plan.index_conditions, f"the read took no index path at all: {plan}"


def test_a_project_scoped_read_takes_no_ordering_path(
    alice: Party, a_tenant_holding_more_than_the_read_names: TheReadersHoldings
) -> None:
    """ADR-0013's Consequences, on the second of the two containers condition 2 names."""
    holdings = a_tenant_holding_more_than_the_read_names

    with tenant_scope(alice.tenant_id):
        plan = the_forced_index_plan_of(
            features_of_a_project_intersecting(holdings.project_id, A_BOX_OVER_THE_FEDERAL_DISTRICT)
        )

    assert plan.orderings == ()
    assert plan.index_conditions, f"the read took no index path at all: {plan}"
