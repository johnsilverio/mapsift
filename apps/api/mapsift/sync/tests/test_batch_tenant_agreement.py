"""The tenant a batch addresses, decided before anything is verified or bound.

Trace: ADR-0010 decision 6 (the tenant is read from the envelope, all operations of one flush
agree on it, and a disagreement is a typed refusal); M8 (the envelope is self-describing enough
to route without inferring from context); M9 (a target carries its ancestors). Pure by
construction (specs/testing.md section 3): plain data in, plain data out, no database, so the
edge cases are cheap to enumerate here rather than behind the wall.
"""

from uuid import uuid4

import pytest

from conftest import JsonObject, a_feature_create_claiming, a_geometry_set_claiming
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    BatchClaimsNoTenant,
    OperationsDisagreeOnTheirTenant,
    the_tenant_every_operation_claims,
)


def _as_authored(*operations: JsonObject) -> list[ClientHalf]:
    """The batch as the generated reader sees it, which is what the rule decides over (M8)."""
    return [ClientHalf.model_validate(operation) for operation in operations]


def test_a_batch_whose_operations_all_address_one_tenant_answers_with_it() -> None:
    """ADR-0010 decision 6, M8: the tenant travels in the envelope, so it is read, not inferred."""
    tenant = uuid4()

    batch = _as_authored(a_feature_create_claiming(tenant), a_feature_create_claiming(tenant))

    assert the_tenant_every_operation_claims(batch) == tenant


def test_a_batch_addressing_two_tenants_is_refused_rather_than_read_first_wins() -> None:
    """ADR-0010 decision 6: a disagreement is a typed refusal, and first-wins is the failure it
    names, because the first operation would then choose the wall's value for the whole batch. The
    second assertion is one direction of the addition's "two named refusals, not one", stated on
    the value the act actually raised: a caller handling the empty batch must not also catch this
    one. The other direction is the empty-batch test's, and only the pair holds the guarantee."""
    batch = _as_authored(a_feature_create_claiming(uuid4()), a_feature_create_claiming(uuid4()))

    with pytest.raises(OperationsDisagreeOnTheirTenant) as refusal:
        the_tenant_every_operation_claims(batch)

    assert not isinstance(refusal.value, BatchClaimsNoTenant)


def test_operations_of_different_types_agreeing_on_one_tenant_answer_with_it() -> None:
    """M9: the two catalog members carry structurally different targets, a feature address and a
    property address, so a rule reading the tenant off one variant is green on a batch of it."""
    tenant = uuid4()

    batch = _as_authored(a_feature_create_claiming(tenant), a_geometry_set_claiming(tenant))

    assert the_tenant_every_operation_claims(batch) == tenant


def test_operations_of_different_types_disagreeing_on_their_tenant_are_refused() -> None:
    """ADR-0010 decision 6 over M9's second variant: the half of the previous case that a rule
    reading one variant's target and defaulting on the other would still pass."""
    batch = _as_authored(a_feature_create_claiming(uuid4()), a_geometry_set_claiming(uuid4()))

    with pytest.raises(OperationsDisagreeOnTheirTenant):
        the_tenant_every_operation_claims(batch)


def test_a_batch_with_no_operations_is_refused_as_its_own_thing_and_not_as_a_disagreement() -> None:
    """ADR-0010 decision 6's addition of 2026-08-07: a batch of no operations does not disagree
    with itself, it names no tenant at all, so it is the second of two named refusals rather than
    the first one stretched. The second assertion is what the addition forbids, stated on the value
    the act actually raised: a caller handling the disagreement must not also catch this one."""
    with pytest.raises(BatchClaimsNoTenant) as refusal:
        the_tenant_every_operation_claims([])

    assert not isinstance(refusal.value, OperationsDisagreeOnTheirTenant)
