//! The operation envelope where it is defined: one definition, two halves that never mix.
//!
//! Trace: M8 (the shape, and its first two acceptance bullets), M9 (one target address per
//! operation), M10 and T9.2 (the four envelope-borne version axes), T5.3 (created-at is the
//! client's claim, applied-at the server's stamp), T8.2 and C14 (mediation carried as a field),
//! ADR-0009 section 5 (both guard rules, on the source side).
//!
//! The third acceptance bullet, that every language reads a generated form, is pinned where the
//! generated forms are read: `apps/api/mapsift/sync/tests` and `apps/web/src/app/core`.

use mapsift_core::envelope::{
    AppliedOperation, ClientHalf, MediationProvenance, ServerHalf, TargetPath,
};
use serde_json::json;

// The four version-axis values differ from one another on purpose: equal values would let two
// axes be wired to one field and every assertion below would still pass.
const A_CLIENT_HALF: &str = r#"{
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
    "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02"
  },
  "payload": {
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[-47.9, -15.8], [-47.8, -15.8], [-47.8, -15.7], [-47.9, -15.8]]]
    }
  },
  "author_session_material": {"proof": "opaque-to-the-core"},
  "created_at": "2026-08-05T12:00:00Z",
  "mediation": null
}"#;

const A_SERVER_HALF: &str = r#"{
  "applied_at": "2026-08-05T12:00:03Z",
  "feature_version": 11,
  "applied_rule_version": 6,
  "legal_weight_in_force": true,
  "verdict": "applied"
}"#;

fn a_client_half() -> ClientHalf {
    serde_json::from_str(A_CLIENT_HALF).expect("the canonical client half must parse")
}

fn a_server_half() -> ServerHalf {
    serde_json::from_str(A_SERVER_HALF).expect("the canonical server half must parse")
}

fn as_value(wire: &str) -> serde_json::Value {
    serde_json::from_str(wire).expect("the canonical wire form must be JSON")
}

fn a_target_path(wire: &str) -> TargetPath {
    serde_json::from_str(wire).expect("the target path must parse")
}

#[test]
fn the_wire_form_of_a_client_half_survives_a_round_trip_unchanged() {
    let parsed = a_client_half();

    let re_emitted = serde_json::to_value(&parsed).expect("a client half must serialize");

    assert_eq!(re_emitted, as_value(A_CLIENT_HALF));
}

#[test]
fn the_wire_form_of_a_server_half_survives_a_round_trip_unchanged() {
    let parsed = a_server_half();

    let re_emitted = serde_json::to_value(&parsed).expect("a server half must serialize");

    assert_eq!(re_emitted, as_value(A_SERVER_HALF));
}

#[test]
fn the_four_envelope_borne_version_axes_are_four_distinct_fields() {
    let client = a_client_half();
    let server = a_server_half();

    assert_eq!(client.mutation_number, 7);
    assert_eq!(client.operation_schema_version, 3);
    assert_eq!(client.conflict_rule_version, 5);
    assert_eq!(server.feature_version, 11);
}

#[test]
fn an_operation_carries_the_type_that_says_how_to_read_its_payload() {
    let client = a_client_half();

    assert_eq!(client.operation_type, "feature.geometry.set");
}

#[test]
fn applying_an_operation_carries_the_client_half_through_whole() {
    let applied = AppliedOperation {
        client: a_client_half(),
        server: a_server_half(),
    };

    let wire = serde_json::to_value(&applied).expect("an applied operation must serialize");

    assert_eq!(wire["client"], as_value(A_CLIENT_HALF));
}

#[test]
fn an_applied_operation_keeps_the_rule_version_the_client_claimed_beside_the_one_applied() {
    let applied = AppliedOperation {
        client: a_client_half(),
        server: a_server_half(),
    };

    assert_eq!(applied.client.conflict_rule_version, 5);
    assert_eq!(applied.server.applied_rule_version, 6);
}

#[test]
fn an_applied_operation_keeps_the_clients_claimed_time_beside_the_servers_stamp() {
    let applied = AppliedOperation {
        client: a_client_half(),
        server: a_server_half(),
    };

    let wire = serde_json::to_value(&applied).expect("an applied operation must serialize");

    assert_eq!(wire["client"]["created_at"], json!("2026-08-05T12:00:00Z"));
    assert_eq!(wire["server"]["applied_at"], json!("2026-08-05T12:00:03Z"));
}

#[test]
fn the_payload_crosses_uninterpreted_whatever_shape_it_carries() {
    let a_payload_the_core_has_no_type_for = json!({
        "geometry": {"type": "Point", "coordinates": [-47.9, -15.8]},
        "captured_by": ["gnss", 0.03],
        "note": null
    });
    let operation = ClientHalf {
        payload: a_payload_the_core_has_no_type_for.clone(),
        ..a_client_half()
    };

    let wire = serde_json::to_value(&operation).expect("a client half must serialize");

    assert_eq!(wire["payload"], a_payload_the_core_has_no_type_for);
}

#[test]
fn the_author_session_material_crosses_uninterpreted_whatever_shape_it_carries() {
    let session_material_the_core_has_no_type_for = json!({
        "proof": "eyJhbGciOiJFZERTQSJ9",
        "issued_at": "2026-08-05T11:59:00Z",
        "scopes": ["write"]
    });
    let operation = ClientHalf {
        author_session_material: session_material_the_core_has_no_type_for.clone(),
        ..a_client_half()
    };

    let wire = serde_json::to_value(&operation).expect("a client half must serialize");

    assert_eq!(
        wire["author_session_material"],
        session_material_the_core_has_no_type_for
    );
}

#[test]
fn a_target_path_parses_into_the_variant_its_kind_names() {
    let tenant =
        a_target_path(r#"{"kind":"tenant","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b"}"#);
    let project = a_target_path(
        r#"{"kind":"project","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
            "project_id":"2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70"}"#,
    );
    let layer = a_target_path(
        r#"{"kind":"layer","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
            "project_id":"2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
            "layer_id":"5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19"}"#,
    );
    let feature = a_target_path(
        r#"{"kind":"feature","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
            "project_id":"2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
            "layer_id":"5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
            "feature_id":"c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02"}"#,
    );
    let property = a_target_path(
        r#"{"kind":"property","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
            "project_id":"2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
            "layer_id":"5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
            "feature_id":"c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
            "property":"geometry"}"#,
    );

    assert!(
        matches!(tenant, TargetPath::Tenant { .. }),
        "a tenant address parsed as {tenant:?}"
    );
    assert!(
        matches!(project, TargetPath::Project { .. }),
        "a project address parsed as {project:?}"
    );
    assert!(
        matches!(layer, TargetPath::Layer { .. }),
        "a layer address parsed as {layer:?}"
    );
    assert!(
        matches!(feature, TargetPath::Feature { .. }),
        "a feature address parsed as {feature:?}"
    );
    assert!(
        matches!(property, TargetPath::Property { .. }),
        "a property address parsed as {property:?}"
    );
}

#[test]
fn a_target_path_whose_kind_is_outside_the_closed_set_is_refused() {
    let outcome = serde_json::from_str::<TargetPath>(
        r#"{"kind":"basin","tenant_id":"7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b"}"#,
    );

    assert!(
        outcome.is_err(),
        "an unnamed target kind parsed as {outcome:?}"
    );
}

#[test]
fn an_agent_originated_operation_is_distinguishable_from_a_direct_human_write() {
    let direct = a_client_half();
    let through_an_agent = ClientHalf {
        mediation: Some(MediationProvenance {
            agent: "mapsift-agent".to_owned(),
        }),
        ..a_client_half()
    };

    assert_eq!(direct.mediation, None);
    assert_eq!(
        through_an_agent.mediation,
        Some(MediationProvenance {
            agent: "mapsift-agent".to_owned()
        })
    );
}

#[test]
fn a_mediated_operations_wire_form_carries_its_provenance_under_the_mediation_key() {
    let through_an_agent = ClientHalf {
        mediation: Some(MediationProvenance {
            agent: "mapsift-agent".to_owned(),
        }),
        ..a_client_half()
    };

    let wire = serde_json::to_value(&through_an_agent).expect("a client half must serialize");

    assert_eq!(wire["mediation"], json!({"agent": "mapsift-agent"}));
}
