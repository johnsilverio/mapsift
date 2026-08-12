"""The routes the sync package publishes (ADR-0007 section 3)."""

from typing import Self
from uuid import UUID

from django.http import Http404
from ninja import Router, Schema
from pydantic import PrivateAttr, model_validator

from mapsift.accounts.selectors import the_session_user_holds_a_membership_in
from mapsift.common.binding import tenant_scope, user_scope
from mapsift.common.principal import AuthenticatedRequest
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    MalformedBatch,
    the_client_every_operation_claims,
    the_project_every_operation_claims,
    the_tenant_every_operation_claims,
)
from mapsift.sync.services import apply_the_flush

router = Router(tags=["sync"])


class OperationBatch(Schema):
    """One flush's operations, from one installation, addressing one tenant and one project.

    The three agreements are ADR-0010 decision 6 with its additions of 2026-08-10 and 2026-08-11.
    """

    operations: list[ClientHalf]

    _tenant_claimed: UUID = PrivateAttr()

    @model_validator(mode="after")
    def _read_the_tenant_and_check_the_three_agreements(self) -> Self:
        try:
            self._tenant_claimed = the_tenant_every_operation_claims(self.operations)
            # The order is contract rather than sequence: an empty batch names no project and no
            # installation either, and the refusal it earns is the tenant's; the clientID comes
            # last on the evidence in ADR-0010 decision 6's addition of 2026-08-11.
            the_project_every_operation_claims(self.operations)
            the_client_every_operation_claims(self.operations)
        except MalformedBatch as refusal:
            raise ValueError(str(refusal)) from refusal
        return self

    @property
    def tenant_claimed(self) -> UUID:
        """The one tenant every operation in this batch addresses, read where it was validated."""
        return self._tenant_claimed


class FlushAcknowledgement(Schema):
    """How far this installation's stream has been applied, and the closed object a client reads
    to advance its cursor (ADR-0010 decision 6's addition of 2026-08-11; T2.3, C12)."""

    last_applied_mutation_number: int


@router.post("/operations")
def flush_operations(request: AuthenticatedRequest, batch: OperationBatch) -> FlushAcknowledgement:
    """Append a batch to the operation log under a tenant claim the principal holds, and answer
    with the number this installation has now had applied (M15, T2.3)."""
    with user_scope(request.auth.id):
        _refuse_a_claim_this_principal_cannot_back(batch.tenant_claimed)
        with tenant_scope(batch.tenant_claimed):
            return FlushAcknowledgement(
                last_applied_mutation_number=apply_the_flush(batch.operations)
            )


def _refuse_a_claim_this_principal_cannot_back(tenant_id: UUID) -> None:
    if not the_session_user_holds_a_membership_in(tenant_id):
        # Bare: any message here tells this answer apart from the one a tenant that never existed
        # earns, and that difference is the leak (T6.5).
        raise Http404
