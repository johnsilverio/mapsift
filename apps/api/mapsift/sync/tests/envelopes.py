"""Client halves addressed at a real party, for the two suites that flush them.

Shared rather than duplicated: a client half is twenty lines of address, and the one field a test
is actually about would be lost inside two copies of it.
"""

from typing import Any
from uuid import UUID, uuid4

from conftest import Party

# `Any` because a document here is a decoded JSON body rather than a modelled shape: its whole job
# is to reach the generated reader untyped, the way a wire payload arrives.
JsonObject = dict[str, Any]


def an_operation_addressed_at(
    party: Party, *, operation_id: UUID, mutation_number: int
) -> JsonObject:
    """One `feature.create` client half whose target names this party's tenant and project."""
    return {
        "operation_id": str(operation_id),
        "client_id": "1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9",
        "mutation_number": mutation_number,
        "operation_type": "feature.create",
        "operation_schema_version": 3,
        "conflict_rule_version": 5,
        "target": {
            "kind": "feature",
            "tenant_id": str(party.tenant_id),
            "project_id": str(party.project_id),
            # Neither has to exist: what a log entry addresses is resolved by the projection, and
            # a create addresses the feature it is about to bring into being (M9, M15).
            "layer_id": str(uuid4()),
            "feature_id": str(uuid4()),
        },
        "payload": {},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-08-07T12:00:00Z",
        "mediation": None,
    }
