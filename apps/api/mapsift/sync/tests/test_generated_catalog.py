"""The catalog as Python reads it: a generated form of the closed set defined in `libs/core`.

Trace: M9 (the closed named catalog and its typed refusal of an operation nobody declared, the
typed payload each member carries), M8's third acceptance bullet with M12 (every language reads a
generated form), ADR-0009 section 5 (both guard rules, now over the union the catalog adds).

Why the generated shape is not re-asserted here: `test_generated_envelope.py`'s docstring. The
set-geometry member's survival is witnessed by every refusal test below, each of which validates a
set-geometry document; the create member needs its own witness and has one at the end.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from mapsift.sync.envelope import ClientHalf

# `Any` because a fixture here is a decoded JSON document rather than a modelled shape: its whole
# job is to reach the generated reader untyped, the way a wire payload arrives.
JsonObject = dict[str, Any]

A_SET_GEOMETRY_OPERATION: JsonObject = {
    "operation_id": "4e8a1c60-7b23-4d95-8f01-6a2c9d3e5b74",
    "client_id": "1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9",
    "mutation_number": 7,
    "operation_type": "feature.geometry.set",
    "operation_schema_version": 3,
    "conflict_rule_version": 5,
    "target": {
        "kind": "property",
        "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
        "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
        "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
        "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
        "property": "geometry",
    },
    "payload": {
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-47.882933418, -15.793889112],
                    [-47.882102337, -15.793889112],
                    [-47.882102337, -15.793055201],
                    [-47.882933418, -15.793889112],
                ]
            ],
        }
    },
    "author_session_material": {"proof": "opaque-to-the-core"},
    "created_at": "2026-08-05T12:00:00Z",
    "mediation": None,
}

A_CREATE_FEATURE_OPERATION: JsonObject = {
    "operation_id": "0b3d5f71-2c48-4e69-a15b-7d9e0f2a4c68",
    "client_id": "1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9",
    "mutation_number": 6,
    "operation_type": "feature.create",
    "operation_schema_version": 3,
    "conflict_rule_version": 5,
    "target": {
        "kind": "feature",
        "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
        "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
        "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
        "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
    },
    "payload": {},
    "author_session_material": {"proof": "opaque-to-the-core"},
    "created_at": "2026-08-05T11:59:58Z",
    "mediation": None,
}


def test_an_operation_type_outside_the_closed_catalog_is_refused_by_the_discriminator() -> None:
    """M9 and ADR-0009 section 5. The tell is the error type rather than the fact that something
    raised: a discriminator that degraded to a plain union still refuses this input, member by
    member, so `pytest.raises(ValidationError)` alone would pass over the defect this test is
    here to catch."""
    typed_at_an_operation_nobody_declared = {
        **A_SET_GEOMETRY_OPERATION,
        "operation_type": "basin.dredge",
    }

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(typed_at_an_operation_nobody_declared)

    assert [error["type"] for error in refused.value.errors()] == ["union_tag_invalid"]


def test_an_operation_carrying_no_type_at_all_is_refused_by_the_discriminator() -> None:
    """ADR-0009 section 5, the other half: an operation with nothing to route on is not guessed."""
    untyped = dict(A_SET_GEOMETRY_OPERATION)
    del untyped["operation_type"]

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(untyped)

    assert [error["type"] for error in refused.value.errors()] == ["union_tag_not_found"]


def test_a_set_geometry_operation_carrying_no_geometry_is_refused() -> None:
    """M9: every member of the catalog carries its own typed payload, so a reader that accepts a
    set-geometry operation with nothing to set is one that left the payload opaque."""
    carrying_nothing_to_set = {**A_SET_GEOMETRY_OPERATION, "payload": {}}

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(carrying_nothing_to_set)

    assert [error["type"] for error in refused.value.errors()] == ["missing"]


def test_an_operation_addressed_at_a_kind_its_type_does_not_declare_is_refused() -> None:
    """M9 as sharpened 2026-08-06, in the generated reader: create declares the feature, so a
    property address reads it finer than the catalog fixes. The refusal is structural, coming from
    the variant this member's target field is typed to, which is why the error is a `literal_error`
    on `kind` and not a rule some caller remembered to run."""
    addressed_finer_than_the_catalog_fixes = {
        **A_CREATE_FEATURE_OPERATION,
        "target": A_SET_GEOMETRY_OPERATION["target"],
    }

    with pytest.raises(ValidationError) as refused:
        ClientHalf.model_validate(addressed_finer_than_the_catalog_fixes)

    assert [error["type"] for error in refused.value.errors()] == ["literal_error"]


def test_the_create_feature_member_survives_the_generator() -> None:
    """ADR-0009 section 5's guard class, and the one test in this module that is green before the
    catalog exists: today's opaque payload accepts this document already. It is kept deliberately,
    because member survival is exactly what the freshness gate cannot see, the same way
    discriminator survival is: a generator that dropped or collapsed a union member writes a green
    file, and a red suite is the only tell."""
    parsed = ClientHalf.model_validate(A_CREATE_FEATURE_OPERATION)

    assert parsed.model_dump(mode="json") == A_CREATE_FEATURE_OPERATION
