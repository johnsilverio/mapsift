"""The reads `accounts` publishes (ADR-0007 section 3)."""

from uuid import UUID

from django.db.models import QuerySet

from mapsift.accounts.models import Membership


def memberships_of_the_session_user() -> QuerySet[Membership]:
    """Every membership of the authenticated user, in every tenant they belong to (T6.1).

    Requires the user binding in force whatever else is bound, and raises `UserNotBound`
    without one (ADR-0005 section 8).
    """
    return Membership.of_the_session_user.all()


def the_session_user_holds_a_membership_in(tenant_id: UUID) -> bool:
    """Whether the authenticated user belongs to this tenant, answerable with no tenant bound.

    That is what lets a tenant claim be verified before the wall is configured from it
    (ADR-0005 section 8, ADR-0010 decision 6). Asks the database about one named tenant;
    `resolve_tenant` is the pure decision over a membership set already in hand.
    """
    return memberships_of_the_session_user().filter(tenant_id=tenant_id).exists()
