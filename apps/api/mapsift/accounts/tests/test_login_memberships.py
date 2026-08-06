"""The login question: which tenants this user belongs to, asked before any tenant is bound.

Trace: T6.1 and M1 (the wall's single deliberate exception), foundation I4; C4; ADR-0005
section 8, whose test case 6 this is. The read path is the `accounts` selector of ADR-0007
section 3, which is the seam the authentication surface will consume.
"""

from uuid import uuid4

import pytest
from django.db import connection

from mapsift.accounts.models import Membership, User
from mapsift.accounts.selectors import memberships_of_the_session_user
from mapsift.accounts.services import create_organization_account, create_personal_account
from mapsift.common.binding import UserNotBound, tenant_scope, user_scope

pytestmark = pytest.mark.django_db(transaction=True)


def test_a_user_in_two_tenants_enumerates_exactly_those_two_with_no_tenant_bound() -> None:
    """T6.1, M1, ADR-0005 section 8: the wall's single deliberate exception, and the whole of it."""
    personal = create_personal_account(email="ana@example.com")
    organization = create_organization_account(name="Acme Ambiental", owner=personal.user)

    with user_scope(personal.user_id):
        tenants = set(memberships_of_the_session_user().values_list("tenant_id", flat=True))

    assert tenants == {personal.tenant_id, organization.tenant_id}


def test_the_login_read_never_answers_with_another_users_membership() -> None:
    """T6.1, C4, ADR-0005 section 8: the exception is the reader's own places and nothing else."""
    ana = create_personal_account(email="ana@example.com")
    create_personal_account(email="bruno@example.com")

    with user_scope(ana.user_id):
        tenants = set(memberships_of_the_session_user().values_list("tenant_id", flat=True))

    assert tenants == {ana.tenant_id}


def test_a_user_who_belongs_to_no_tenant_enumerates_nothing_rather_than_raising() -> None:
    """M1, ADR-0005 section 8, the guard: with the user binding in force an empty result is a
    genuine answer, and it is the only one of the three empties here that is an answer at all."""
    create_personal_account(email="ana@example.com")
    nobody = User.objects.create(email="nobody@example.com")

    with user_scope(nobody.id):
        assert list(memberships_of_the_session_user()) == []


def test_the_login_read_with_no_user_binding_in_force_raises_rather_than_returning_empty() -> None:
    """N9, N12, ADR-0005 section 8, the guard: the wall's own denial is indistinguishable from a
    user who belongs nowhere, and only one of the two is an answer."""
    create_personal_account(email="ana@example.com")

    with pytest.raises(UserNotBound):
        list(memberships_of_the_session_user())


def test_the_login_read_with_only_a_tenant_in_force_refuses_rather_than_answering_for_it() -> None:
    """T6.1, ADR-0005 section 8, the guard: the user binding is required whatever else is bound,
    because the tenant policy alone answers with every member of that tenant."""
    ana = create_personal_account(email="ana@example.com")

    with pytest.raises(UserNotBound), tenant_scope(ana.tenant_id):
        list(memberships_of_the_session_user())


def test_with_both_bindings_in_force_the_read_answers_the_readers_own_rows_alone() -> None:
    """T6.1, ADR-0005 section 8, the guard: the two permissive policies combine with OR, so a
    tenant-bound read sees that tenant's whole roll and the read path narrows to its own key."""
    ana_personal = create_personal_account(email="ana@example.com")
    ana_organization = create_organization_account(name="Acme Ambiental", owner=ana_personal.user)
    bruno = create_personal_account(email="bruno@example.com")

    with tenant_scope(ana_organization.tenant_id):
        Membership.objects.create(
            id=uuid4(),
            tenant_id=ana_organization.tenant_id,
            user=bruno.user,
            role=Membership.Role.MEMBER,
            licence=Membership.Licence.VIEWER,
        )

    with tenant_scope(ana_organization.tenant_id), user_scope(ana_personal.user_id):
        answered = set(memberships_of_the_session_user().values_list("id", flat=True))

    assert answered == {ana_personal.id, ana_organization.id}


def test_a_user_who_belongs_nowhere_gets_the_genuine_empty_with_a_tenant_also_bound() -> None:
    """M1, ADR-0005 section 8, the guard: the empty answers the question that was asked, and is
    never the bound tenant's roll handed to somebody who holds no place in it."""
    ana = create_personal_account(email="ana@example.com")
    nobody = User.objects.create(email="nobody@example.com")

    with tenant_scope(ana.tenant_id), user_scope(nobody.id):
        assert list(memberships_of_the_session_user()) == []


def test_membership_is_indexed_by_the_user_the_login_question_asks_about() -> None:
    """ADR-0005 section 8, the index: decision 5's tenant-leading rule governs tenant-scoped
    queries, and this one has no tenant bound at all, so nothing else in the suite would notice
    the index missing."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT i.relname
            FROM pg_index x
            JOIN pg_class c ON c.oid = x.indrelid
            JOIN pg_class i ON i.oid = x.indexrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = x.indkey[0]
            WHERE n.nspname = 'public' AND c.relname = %s AND a.attname = %s
            """,
            [Membership._meta.db_table, "user_id"],
        )

        assert cursor.fetchone() is not None
