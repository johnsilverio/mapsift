"""The envelope as Python reads it: a generated form of the one definition in `libs/core`.

Trace: M8's third acceptance bullet (every language reads a generated form), M12 (generated,
never hand-written twice), ADR-0009 sections 2 and 5 (the toolchain and its two guard rules),
ADR-0007 section 7 (the `sync` package arrives here).

The generated model's field list is deliberately not re-asserted: a generated type is guaranteed
by the generator plus the freshness gate, and a hand-written copy of its shape is the second copy
`specs/testing.md` section 7 names. What is pinned here is what the gate cannot see, because
`datamodel-code-generator` produces a green file in both cases: whether the discriminator survived
the generator, and whether the opaque payload came through un-narrowed.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from mapsift.sync.envelope import AppliedOperation, ClientHalf

# `Any` because a fixture here is a decoded JSON document rather than a modelled shape: its whole
# job is to reach the generated reader untyped, the way a wire payload arrives.
JsonObject = dict[str, Any]

A_CLIENT_HALF: JsonObject = {
    "operation_id": "9f1c0d3a-6b2e-4f57-8c19-2d4a7e5b0c31",
    "client_id": "1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9",
    "mutation_number": 7,
    "operation_type": "feature.geometry.set",
    "operation_schema_version": 3,
    "conflict_rule_version": 5,
    "target": {
        "kind": "feature",
        "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
        "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
        "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
        "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
    },
    "payload": {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-47.9, -15.8], [-47.8, -15.8], [-47.8, -15.7], [-47.9, -15.8]]],
        }
    },
    "author_session_material": {"proof": "opaque-to-the-core"},
    "created_at": "2026-08-05T12:00:00Z",
    "mediation": None,
}

A_SERVER_HALF: JsonObject = {
    "applied_at": "2026-08-05T12:00:03Z",
    "feature_version": 11,
    "applied_rule_version": 6,
    "legal_weight_in_force": True,
    "verdict": "applied",
}


def test_a_client_halfs_wire_form_survives_a_round_trip_through_the_generated_reader() -> None:
    """M8: the envelope has one definition and every language reads a generated form of it."""
    parsed = ClientHalf.model_validate(A_CLIENT_HALF)

    assert parsed.model_dump(mode="json") == A_CLIENT_HALF


def test_a_mediated_client_half_survives_a_round_trip_through_the_generated_reader() -> None:
    """C14, T8.2: the provenance that makes an agent write distinguishable is the first thing a
    reader that typed `mediation` as absent-only would drop."""
    through_an_agent = {**A_CLIENT_HALF, "mediation": {"agent": "mapsift-agent"}}

    parsed = ClientHalf.model_validate(through_an_agent)

    assert parsed.model_dump(mode="json") == through_an_agent


def test_the_generated_reader_reaches_both_halves_of_an_applied_operation() -> None:
    """M8: the server half is added at application and the client half arrives intact under it."""
    applied = AppliedOperation.model_validate({"client": A_CLIENT_HALF, "server": A_SERVER_HALF})

    assert applied.client.model_dump(mode="json") == A_CLIENT_HALF
    assert applied.server.model_dump(mode="json") == A_SERVER_HALF


def test_a_target_path_outside_the_closed_set_is_refused_by_the_discriminator() -> None:
    """ADR-0009 section 5. The tell is the error type rather than the fact that something raised:
    a discriminator that degraded to a plain union still refuses this input, member by member, so
    `pytest.raises(ValidationError)` alone would pass over the defect this test exists to catch."""
    addressed_at_a_kind_nobody_declared = {
        **A_CLIENT_HALF,
        "target": {**A_CLIENT_HALF["target"], "kind": "basin"},
    }

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(addressed_at_a_kind_nobody_declared)

    assert [error["type"] for error in refused.value.errors()] == ["union_tag_invalid"]


def test_a_target_path_carrying_no_kind_at_all_is_refused_by_the_discriminator() -> None:
    """ADR-0009 section 5, the other half: an address with nothing to route on is not guessed."""
    unaddressed = {
        **A_CLIENT_HALF,
        "target": {"tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b"},
    }

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(unaddressed)

    assert [error["type"] for error in refused.value.errors()] == ["union_tag_not_found"]


def test_the_opaque_payload_crosses_the_generated_reader_unchanged() -> None:
    """ADR-0009 section 5: a payload the generated reader narrowed or flattened fails here."""
    a_payload_no_generator_can_type = {
        "geometry": {"type": "Point", "coordinates": [-47.9, -15.8]},
        "captured_by": ["gnss", 0.03],
        "note": None,
    }

    parsed = ClientHalf.model_validate(
        {**A_CLIENT_HALF, "payload": a_payload_no_generator_can_type}
    )

    assert parsed.model_dump(mode="json")["payload"] == a_payload_no_generator_can_type


def test_the_opaque_session_material_crosses_the_generated_reader_unchanged() -> None:
    """ADR-0009 section 5, and OQ-18 still owns the shape: a reader that typed this field would
    pin a decision nobody has taken."""
    opaque_material = {
        "proof": "eyJhbGciOiJFZERTQSJ9",
        "issued_at": "2026-08-05T11:59:00Z",
        "scopes": ["write"],
    }

    parsed = ClientHalf.model_validate(
        {**A_CLIENT_HALF, "author_session_material": opaque_material}
    )

    assert parsed.model_dump(mode="json")["author_session_material"] == opaque_material
