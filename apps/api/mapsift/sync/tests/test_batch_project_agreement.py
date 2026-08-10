"""The project a batch addresses, decided before anything is verified or bound.

Trace: ADR-0010 decision 6's addition of 2026-08-10 (one flush addresses exactly one project, a
third typed refusal beside the two the tenant already earned); ADR-0004's Consequences, which is
where the rule comes from rather than being invented at the boundary (a batch across two projects
takes two locks, restoring the repeated acquisition the RANGE rule removes, and one transaction
over both makes the batch atomic across projects, which this strategy cannot express); M9 (a
target carries its ancestors, so the project travels in the envelope the way the tenant does).

Pure by construction (specs/testing.md section 3): plain data in, plain data out, no database. A
module of its own rather than four more cases in the tenant's, because the two refusals answer
different questions and the addition's whole point is that a client can tell them apart.
"""

from uuid import uuid4

import pytest

from conftest import JsonObject, a_feature_create_claiming, a_geometry_set_claiming
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    OperationsDisagreeOnTheirProject,
    OperationsDisagreeOnTheirTenant,
    the_project_every_operation_claims,
)


def _as_authored(*operations: JsonObject) -> list[ClientHalf]:
    """The batch as the generated reader sees it, which is what the rule decides over (M8)."""
    return [ClientHalf.model_validate(operation) for operation in operations]


def test_a_batch_whose_operations_all_address_one_project_answers_with_it() -> None:
    """ADR-0010 decision 6's addition of 2026-08-10, M8: the project travels in the envelope, so
    it is read there and not inferred. The positive control the refusal below depends on, since a
    rule that refuses every batch satisfies that one on its own."""
    tenant, project = uuid4(), uuid4()

    batch = _as_authored(
        a_feature_create_claiming(tenant, project_id=project),
        a_feature_create_claiming(tenant, project_id=project),
    )

    assert the_project_every_operation_claims(batch) == project


def test_two_projects_in_one_batch_of_one_tenant_are_refused_rather_than_read_first_wins() -> None:
    """ADR-0010 decision 6's addition of 2026-08-10. The tenant is held constant deliberately: a
    batch that disagrees on both axes is refused by the rule that runs first, so it says nothing
    about this one, and first-wins is the concrete defect here as it is there, because the lock
    ADR-0004 takes would then be one project's while a second project's operations were ordered
    under it. The second assertion is the addition's "told apart", stated on the value the act
    raised: a caller handling the tenant disagreement must not also catch this one."""
    tenant = uuid4()

    batch = _as_authored(
        a_feature_create_claiming(tenant, project_id=uuid4()),
        a_feature_create_claiming(tenant, project_id=uuid4()),
    )

    with pytest.raises(OperationsDisagreeOnTheirProject) as refusal:
        the_project_every_operation_claims(batch)

    assert not isinstance(refusal.value, OperationsDisagreeOnTheirTenant)


def test_operations_of_different_types_agreeing_on_one_project_answer_with_it() -> None:
    """M9: the two catalog members carry structurally different targets, a feature address and a
    property address, and both carry the project among their ancestors. A rule narrowed to one
    variant either raises here or answers with a placeholder for the other, and a placeholder
    reads as a second project, so this case fails towards refusal either way."""
    tenant, project = uuid4(), uuid4()

    batch = _as_authored(
        a_feature_create_claiming(tenant, project_id=project),
        a_geometry_set_claiming(tenant, project_id=project),
    )

    assert the_project_every_operation_claims(batch) == project
