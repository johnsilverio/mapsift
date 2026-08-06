"""The reads `accounts` publishes (ADR-0007 section 3)."""

from django.db.models import QuerySet

from mapsift.accounts.models import Membership


def memberships_of_the_session_user() -> QuerySet[Membership]:
    """Every membership of the authenticated user, in every tenant they belong to (T6.1).

    Requires the user binding in force whatever else is bound, and raises `UserNotBound`
    without one (ADR-0005 section 8).
    """
    return Membership.of_the_session_user.all()
