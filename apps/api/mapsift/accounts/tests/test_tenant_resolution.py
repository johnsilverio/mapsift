"""The tenant-resolution decision: which tenant is in force, and when the answer is none.

Trace: M1, T6.1; C4. Pure by construction (specs/testing.md section 3): plain data in, plain data
out, no database, so the edge cases are cheap to enumerate here rather than behind the wall.
"""

from uuid import uuid4

from mapsift.accounts.rules import resolve_tenant


def test_a_session_resolves_the_tenant_of_a_resource_it_belongs_to() -> None:
    """M1."""
    tenant = uuid4()

    assert resolve_tenant(member_of={tenant}, resource_tenant=tenant) == tenant


def test_holding_two_memberships_resolves_the_one_the_resource_names() -> None:
    """M1: a user belonging to two tenants has one identity and two memberships."""
    personal, organization = uuid4(), uuid4()

    assert (
        resolve_tenant(member_of={personal, organization}, resource_tenant=organization)
        == organization
    )


def test_a_resource_the_session_does_not_hold_never_falls_back_to_the_tenant_it_does() -> None:
    """C4, T6.1: the only membership a session holds is not a default for somebody else's row."""
    assert resolve_tenant(member_of={uuid4()}, resource_tenant=uuid4()) is None


def test_a_session_with_no_membership_resolves_to_no_tenant() -> None:
    """M1, C4."""
    assert resolve_tenant(member_of=set(), resource_tenant=uuid4()) is None


def test_a_foreign_resource_is_indistinguishable_from_one_that_does_not_exist() -> None:
    """T6.1: a cross-tenant read is indistinguishable from a resource that never existed, so the
    decision must not answer the two cases differently either."""
    member_of = {uuid4()}

    foreign = resolve_tenant(member_of=member_of, resource_tenant=uuid4())
    unknown = resolve_tenant(member_of=member_of, resource_tenant=None)

    assert foreign == unknown
