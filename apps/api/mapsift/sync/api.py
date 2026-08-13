"""The routes the sync package publishes (ADR-0007 section 3)."""

from http import HTTPStatus
from typing import Self
from uuid import UUID

from django.http import Http404
from ninja import Router, Schema, Status
from pydantic import PrivateAttr, model_validator

from mapsift.accounts.selectors import the_session_user_holds_a_membership_in
from mapsift.common.binding import tenant_scope, user_scope
from mapsift.common.principal import AuthenticatedRequest
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    MalformedBatch,
    OneUnbrokenStream,
    ThisStreamCannotBeContinued,
    WhyAStreamCannotBeContinued,
    the_one_unbroken_stream_this_batch_carries,
)
from mapsift.sync.services import apply_the_flush

router = Router(tags=["sync"])


class OperationBatch(Schema):
    """One flush's operations, one unbroken stream from one installation, addressing one tenant
    and one project.

    The five composition rules are ADR-0010 decision 6 with its additions of 2026-08-10,
    2026-08-11 and 2026-08-13.
    """

    operations: list[ClientHalf]

    _stream_claimed: OneUnbrokenStream = PrivateAttr()

    @model_validator(mode="after")
    def _read_the_stream_and_check_the_composition_rules(self) -> Self:
        try:
            self._stream_claimed = the_one_unbroken_stream_this_batch_carries(self.operations)
        except MalformedBatch as refusal:
            raise ValueError(str(refusal)) from refusal
        return self

    @property
    def tenant_claimed(self) -> UUID:
        """The one tenant every operation in this batch addresses, read where it was validated."""
        return self._stream_claimed.tenant_id


class FlushAcknowledgement(Schema):
    """How far this installation's stream has been applied, and the closed object a client reads
    to advance its cursor (ADR-0010 decision 6's addition of 2026-08-11; T2.3, C12)."""

    last_applied_mutation_number: int


class FlushRefusal(Schema):
    """Why a stream was not continued and the mutation number its client resends from, the
    closed object this route's second answer carries (ADR-0010 decision 6's addition of
    2026-08-13; M10, M4)."""

    reason: WhyAStreamCannotBeContinued
    resend_from_mutation_number: int | None


@router.post(
    "/operations",
    response={HTTPStatus.OK: FlushAcknowledgement, HTTPStatus.CONFLICT: FlushRefusal},
)
def flush_operations(
    request: AuthenticatedRequest, batch: OperationBatch
) -> Status[FlushAcknowledgement] | Status[FlushRefusal]:
    """Append a batch to the operation log under a tenant claim the principal holds, and answer
    with the number this installation has now had applied, or with why its stream could not be
    continued here (M15, T2.3, M10, M4)."""
    with user_scope(request.auth.id):
        _refuse_a_claim_this_principal_cannot_back(batch.tenant_claimed)
        # The catch sits outside the binding rather than inside it, so the refusal leaves the
        # transaction rolled back and M10's "applies nothing at all" survives a later writer
        # landing above the comparison.
        try:
            with tenant_scope(batch.tenant_claimed):
                applied = apply_the_flush(batch.operations)
        except ThisStreamCannotBeContinued as refusal:
            return Status(
                HTTPStatus.CONFLICT,
                FlushRefusal(
                    reason=refusal.reason,
                    resend_from_mutation_number=refusal.resend_from_mutation_number,
                ),
            )
        return Status(HTTPStatus.OK, FlushAcknowledgement(last_applied_mutation_number=applied))


def _refuse_a_claim_this_principal_cannot_back(tenant_id: UUID) -> None:
    if not the_session_user_holds_a_membership_in(tenant_id):
        # Bare: any message here tells this answer apart from the one a tenant that never existed
        # earns, and that difference is the leak (T6.5).
        raise Http404
