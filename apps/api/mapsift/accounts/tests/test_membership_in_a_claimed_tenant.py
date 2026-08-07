"""Whether the session user holds a membership in a named tenant, asked before any tenant binds.

Trace: ADR-0005 section 8 (the wall's single deliberate exception, its guard, and the narrowing
whose witness that guard's last clause demands), T6.1 and M1, foundation I4; C4, T6.5. The read is
the `accounts` selector of ADR-0007 section 3, and MAP-34 is what gave it its first caller: it is
what makes a tenant claim verifiable before the wall is ever configured from that claim.

**These tests were born green and that is not success.** The read already existed when this module
was written, so what is here characterises behaviour that was inherited rather than chosen. Every
test therefore names, in its docstring, the change to the read that turns it red, and a test that
could not name one would be asserting nothing and does not belong.

The sibling module `test_login_memberships.py` covers the enumerating read. This one covers the
boolean, whose edges are different: it takes a tenant nobody has checked against the reader, and
section 8's three different empties all collapse into one `False` unless the guard keeps them
apart.
"""

from uuid import uuid4

import pytest

from mapsift.accounts.models import User
from mapsift.accounts.selectors import the_session_user_holds_a_membership_in
from mapsift.accounts.services import create_organization_account, create_personal_account
from mapsift.common.binding import UserNotBound, tenant_scope, user_scope

pytestmark = pytest.mark.django_db(transaction=True)


def test_the_session_user_holds_a_membership_in_a_tenant_they_belong_to() -> None:
    """M1, ADR-0005 section 8: the answer the whole verification seam rests on, and the only one
    reachable with no tenant bound at all.

    Turns red when the read stops keying on the session user's own rows, and again when it answers
    with the queryset rather than a boolean: `is True` fails on a truthy `QuerySet` where a bare
    `assert held` would pass."""
    ana = create_personal_account(email="ana@example.com")

    with user_scope(ana.user_id):
        held = the_session_user_holds_a_membership_in(ana.tenant_id)

    assert held is True


def test_the_session_user_holds_no_membership_in_another_users_tenant() -> None:
    """T6.1, C4, ADR-0005 section 8: the exception is the reader's own places and nothing else.

    Turns red when the read drops its tenant argument and answers whether the user holds any
    membership at all, which is the shape a caller verifying a claim accepts without noticing."""
    ana = create_personal_account(email="ana@example.com")
    bruno = create_personal_account(email="bruno@example.com")

    with user_scope(ana.user_id):
        held = the_session_user_holds_a_membership_in(bruno.tenant_id)

    assert held is False


def test_a_tenant_that_never_existed_is_answered_exactly_as_one_the_user_is_not_in() -> None:
    """T6.5's cross-tenant half at the read that decides it: not-yours and never-existed are one
    answer, so nothing downstream can tell them apart.

    Turns red when the read fetches a row and lets `Membership.DoesNotExist` escape, which makes a
    refusal out of what should be an answer. The `is False` line is the arm a mutation reaches
    today; the comparison is what stops a later existence check from splitting the two outcomes,
    and it needs the line above it, because two Trues would satisfy a comparison on their own."""
    ana = create_personal_account(email="ana@example.com")
    bruno = create_personal_account(email="bruno@example.com")

    with user_scope(ana.user_id):
        on_a_tenant_that_exists = the_session_user_holds_a_membership_in(bruno.tenant_id)
        on_a_tenant_that_never_did = the_session_user_holds_a_membership_in(uuid4())

    assert on_a_tenant_that_exists is False
    assert on_a_tenant_that_never_did == on_a_tenant_that_exists


def test_a_user_who_belongs_nowhere_is_answered_false_rather_than_refused() -> None:
    """M1, ADR-0005 section 8, the guard: with the user binding in force an empty answer is a
    genuine answer, and it is the only one of section 8's three empties that is an answer at all.

    Turns red when the guard is widened to treat an empty membership set as an absent binding,
    which collapses the empty that answers into the two that refuse."""
    ana = create_personal_account(email="ana@example.com")
    nobody = User.objects.create(email="nobody@example.com")

    with user_scope(nobody.id):
        held = the_session_user_holds_a_membership_in(ana.tenant_id)

    assert held is False


def test_the_read_with_no_user_binding_in_force_refuses_rather_than_answering_false() -> None:
    """ADR-0005 section 8, the guard, and the load-bearing case of this module: the wall denies by
    returning nothing, so a read that answered here would answer `False`, which is exactly what a
    user who belongs nowhere legitimately gets.

    Turns red when the guard is removed. Nothing else in the suite would notice, because the wrong
    answer is a plausible right one, and a caller verifying a claim would read it as a denial while
    the reason for it was that nobody was authenticated at all."""
    ana = create_personal_account(email="ana@example.com")

    with pytest.raises(UserNotBound):
        the_session_user_holds_a_membership_in(ana.tenant_id)


def test_the_read_with_only_a_tenant_in_force_refuses_rather_than_answering_from_it() -> None:
    """ADR-0005 section 8, the guard's "whatever else is bound": answering from the tenant policy
    alone hands back every member of that tenant as the reader's own.

    Turns red when the guard asks whether anything is bound rather than whether the user is, at
    which point this call answers `True` for a session holding no membership anywhere."""
    ana = create_personal_account(email="ana@example.com")

    with pytest.raises(UserNotBound), tenant_scope(ana.tenant_id):
        the_session_user_holds_a_membership_in(ana.tenant_id)


def test_with_both_bindings_in_force_the_reader_holds_no_membership_they_never_had() -> None:
    """ADR-0005 section 8's last clause, which asks for exactly this witness: the two permissive
    policies combine with OR, so a tenant-bound read sees that tenant's whole roll and the read
    path has to narrow to its own key.

    Turns red when that narrowing is dropped and the read leans on the policy, at which point
    Bruno's row answers `True` for Ana. Binding a tenant the reader does not hold is not a state
    production reaches, and that is the point: it is the state the verification exists to prevent,
    so the read must not be the thing that trusts it."""
    ana = create_personal_account(email="ana@example.com")
    bruno = create_personal_account(email="bruno@example.com")
    acme = create_organization_account(name="Acme Ambiental", owner=bruno.user)

    with tenant_scope(acme.tenant_id), user_scope(ana.user_id):
        held = the_session_user_holds_a_membership_in(acme.tenant_id)

    assert held is False


def test_a_user_holding_two_memberships_holds_each_of_the_tenants_they_name() -> None:
    """M1, ADR-0005 section 8: a user belonging to two tenants has one identity and two
    memberships, and both are reachable with no tenant bound.

    Turns red when the read compares the named tenant against a single membership rather than
    querying for it, which answers `True` for one of the two arbitrarily and `False` for the
    other."""
    personal = create_personal_account(email="ana@example.com")
    organization = create_organization_account(name="Acme Ambiental", owner=personal.user)

    with user_scope(personal.user_id):
        holds_the_personal_tenant = the_session_user_holds_a_membership_in(personal.tenant_id)
        holds_the_organization = the_session_user_holds_a_membership_in(organization.tenant_id)

    assert holds_the_personal_tenant is True
    assert holds_the_organization is True
