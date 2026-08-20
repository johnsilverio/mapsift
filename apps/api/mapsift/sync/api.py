"""The routes the sync package publishes (ADR-0007 section 3)."""

from http import HTTPStatus
from typing import Self
from uuid import UUID

from django.http import Http404
from ninja import Router, Schema, Status
from pydantic import PrivateAttr, model_validator

from mapsift.accounts.selectors import (
    the_bound_tenant_holds_the_project,
    the_session_user_holds_a_membership_in,
)
from mapsift.common.binding import tenant_scope, user_scope
from mapsift.common.decision_trail import (
    TheDecisionARecordNames,
    correlated_by,
    record_the_decision,
)
from mapsift.common.principal import AuthenticatedRequest
from mapsift.sync.envelope import ClientHalf
from mapsift.sync.rules import (
    MalformedBatch,
    OneUnbrokenStream,
    ThisStreamCannotBeContinued,
    WhyAStreamCannotBeContinued,
    the_one_unbroken_stream_this_batch_carries,
    the_operation_identifiers_in,
)
from mapsift.sync.services import apply_the_flush

router = Router(tags=["sync"])

# Not a `WhyAStreamCannotBeContinued`: that set is the 409's wire contract and this value is a
# record's alone, which ADR-0011 section 4 leaves open where a refusal has no upstream set.
NO_MEMBERSHIP_IN_THE_TENANT_CLAIMED = "no_membership_in_the_tenant_claimed"
NO_PROJECT_IN_THE_TENANT_VERIFIED = "no_project_in_the_tenant_verified"


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

    @property
    def project_claimed(self) -> UUID:
        """The one project every operation in this batch addresses, read where it was validated."""
        return self._stream_claimed.project_id

    @property
    def client_claimed(self) -> UUID:
        """The one installation this batch comes from, read where it was validated."""
        return self._stream_claimed.client_id


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
    with (
        correlated_by(
            tenant_id=batch.tenant_claimed,
            client_id=batch.client_claimed,
            operation_ids=the_operation_identifiers_in(batch.operations),
        ),
        user_scope(request.auth.id),
    ):
        _refuse_a_claim_this_principal_cannot_back(batch.tenant_claimed)
        # The catch sits outside the binding rather than inside it, so the refusal leaves the
        # transaction rolled back and M10's "applies nothing at all" survives a later writer
        # landing above the comparison.
        try:
            with tenant_scope(batch.tenant_claimed):
                _refuse_a_project_the_verified_tenant_does_not_hold(batch.project_claimed)
                applied = apply_the_flush(batch.operations)
        except ThisStreamCannotBeContinued as refusal:
            record_the_decision(
                TheDecisionARecordNames.REQUEST_REFUSED,
                status=HTTPStatus.CONFLICT,
                reason=refusal.reason,
            )
            return Status(
                HTTPStatus.CONFLICT,
                FlushRefusal(
                    reason=refusal.reason,
                    resend_from_mutation_number=refusal.resend_from_mutation_number,
                ),
            )
        return Status(HTTPStatus.OK, FlushAcknowledgement(last_applied_mutation_number=applied))


def _refuse_a_claim_this_principal_cannot_back(tenant_id: UUID) -> None:
    if the_session_user_holds_a_membership_in(tenant_id):
        return

    record_the_decision(
        TheDecisionARecordNames.REQUEST_REFUSED,
        status=HTTPStatus.NOT_FOUND,
        reason=NO_MEMBERSHIP_IN_THE_TENANT_CLAIMED,
    )
    # Bare: any message here tells this answer apart from the one a tenant that never existed
    # earns, and that difference is the leak (T6.5).
    raise Http404


def _refuse_a_project_the_verified_tenant_does_not_hold(project_id: UUID) -> None:
    if the_bound_tenant_holds_the_project(project_id):
        return

    record_the_decision(
        TheDecisionARecordNames.REQUEST_REFUSED,
        status=HTTPStatus.NOT_FOUND,
        reason=NO_PROJECT_IN_THE_TENANT_VERIFIED,
    )
    # Bare for the reason the sibling above is, on the project axis (T6.5, ADR-0010 decision 6's
    # addition of 2026-08-20).
    raise Http404
