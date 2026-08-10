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
from mapsift.sync.rules import MalformedBatch, the_tenant_every_operation_claims
from mapsift.sync.services import append_to_the_operation_log

router = Router(tags=["sync"])


class OperationBatch(Schema):
    """One flush's operations, which address one tenant between them (ADR-0010 decision 6)."""

    operations: list[ClientHalf]

    _tenant_claimed: UUID = PrivateAttr()

    @model_validator(mode="after")
    def _read_the_one_tenant_this_batch_claims(self) -> Self:
        try:
            self._tenant_claimed = the_tenant_every_operation_claims(self.operations)
        except MalformedBatch as refusal:
            raise ValueError(str(refusal)) from refusal
        return self

    @property
    def tenant_claimed(self) -> UUID:
        """The one tenant every operation in this batch addresses, read where it was validated."""
        return self._tenant_claimed


@router.post("/operations")
def flush_operations(request: AuthenticatedRequest, batch: OperationBatch) -> None:
    """Append a batch to the operation log under a tenant claim the principal holds (M15)."""
    with user_scope(request.auth.id):
        _refuse_a_claim_this_principal_cannot_back(batch.tenant_claimed)
        with tenant_scope(batch.tenant_claimed):
            append_to_the_operation_log(batch.operations)


def _refuse_a_claim_this_principal_cannot_back(tenant_id: UUID) -> None:
    if not the_session_user_holds_a_membership_in(tenant_id):
        # Bare: any message here tells this answer apart from the one a tenant that never existed
        # earns, and that difference is the leak (T6.5).
        raise Http404
