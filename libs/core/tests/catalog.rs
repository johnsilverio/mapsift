//! The closed operation catalog: what an operation may be, what it addresses, and what it carries.
//!
//! Trace: M9 (the closed named catalog, one target path per operation, the type-to-target-kind
//! pairing, the whole geometry rather than a vertex delta, the typed refusal of a type nobody
//! declared), M8 (the envelope this narrows), M5 rule 4 (a coordinate crosses at full precision),
//! ADR-0009 section 5 (the guard rules, on the source side). Each test names the clause it carries.
//!
//! The catalog's generated forms are pinned where they are read: `apps/api/mapsift/sync/tests`
//! and `apps/web/src/app/core`.

use mapsift_core::catalog::OperationType;
use mapsift_core::envelope::{ClientHalf, TargetKind};
use serde_json::{Value, json};

/// The vertices carry survey precision on purpose: a coordinate that comes back with fewer digits
/// than it went in with still looks like a polygon, and it is M5 rule 4 broken.
fn a_whole_ring() -> Value {
    json!({
        "type": "Polygon",
        "coordinates": [[
            [-47.882933418, -15.793889112],
            [-47.882102337, -15.793889112],
            [-47.882102337, -15.793055201],
            [-47.882933418, -15.793889112]
        ]]
    })
}

/// Addressed at the geometry property rather than at the feature, which is the granularity M9
/// fixes for a geometry operation.
fn a_set_geometry_operation() -> Value {
    json!({
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
            "property": "geometry"
        },
        "payload": {"geometry": a_whole_ring()},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-08-05T12:00:00Z",
        "mediation": null
    })
}

fn a_create_feature_operation() -> Value {
    json!({
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
            "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02"
        },
        "payload": {},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-08-05T11:59:58Z",
        "mediation": null
    })
}

/// Parses a client half and hands back what it re-emits. The re-emitted form rather than the value
/// itself, because `ClientHalf` derives no `Debug` (the note on its derive says why) and an
/// assertion that refuses a wrong operation has to be able to show what got through.
fn read(wire: &Value) -> Result<Value, String> {
    let parsed: ClientHalf =
        serde_json::from_value(wire.clone()).map_err(|refusal| refusal.to_string())?;
    serde_json::to_value(&parsed).map_err(|failure| failure.to_string())
}

/// M9: the catalog is closed, so a member is a decision rather than a habit. The order below is
/// canonical and a member is appended, never inserted.
#[test]
fn the_catalog_is_closed_over_the_two_operations_this_slice_declares() {
    assert_eq!(
        OperationType::CATALOG,
        [
            OperationType::FeatureCreate,
            OperationType::FeatureGeometrySet
        ]
        .as_slice()
    );
}

/// M9: every operation addresses exactly one target path, and this is the one create addresses.
#[test]
fn creating_a_feature_addresses_the_feature_it_creates() {
    assert_eq!(
        OperationType::FeatureCreate.target_kind(),
        TargetKind::Feature
    );
}

/// M9: the conflict unit of a geometry operation is the geometry property, which is what makes the
/// granularity ladder decidable at all.
#[test]
fn setting_a_geometry_addresses_the_geometry_property_rather_than_the_whole_feature() {
    assert_eq!(
        OperationType::FeatureGeometrySet.target_kind(),
        TargetKind::Property
    );
}

/// M9 and M8: a declared member of the catalog travels in the envelope and comes back unchanged.
#[test]
fn a_create_feature_operation_survives_a_round_trip_unchanged() {
    let wire = a_create_feature_operation();

    let re_emitted = read(&wire).expect("a declared operation must parse");

    assert_eq!(re_emitted, wire);
}

/// M9 (the whole geometry, never a vertex delta) and M5 rule 4 (no silent precision loss).
#[test]
fn a_set_geometry_operation_carries_the_whole_geometry_it_was_drawn_with() {
    let wire = a_set_geometry_operation();

    let re_emitted = read(&wire).expect("a declared operation must parse");

    assert_eq!(re_emitted["payload"]["geometry"], a_whole_ring());
}

/// M9: an operation type outside the catalog is rejected with a typed error, never applied
/// speculatively.
#[test]
fn an_operation_type_outside_the_closed_catalog_is_refused() {
    let mut typed_at_an_operation_nobody_declared = a_set_geometry_operation();
    typed_at_an_operation_nobody_declared["operation_type"] = json!("basin.dredge");

    let outcome = read(&typed_at_an_operation_nobody_declared);

    assert!(
        outcome.is_err(),
        "an operation type outside the catalog parsed as {outcome:?}"
    );
}

/// M9: each member carries its own typed payload, so a set-geometry operation with nothing to set
/// is not an operation the catalog declares.
#[test]
fn a_set_geometry_operation_carrying_no_geometry_is_refused() {
    let mut carrying_nothing_to_set = a_set_geometry_operation();
    carrying_nothing_to_set["payload"] = json!({});

    let outcome = read(&carrying_nothing_to_set);

    assert!(
        outcome.is_err(),
        "a set-geometry operation with nothing to set parsed as {outcome:?}"
    );
}

/// M9 as sharpened 2026-08-06: an operation addressed at a target kind other than the one its type
/// declares is refused, never read at a coarser granularity than the catalog fixes.
#[test]
fn a_set_geometry_operation_addressed_at_the_whole_feature_is_refused() {
    let mut addressed_coarser_than_the_catalog_fixes = a_set_geometry_operation();
    addressed_coarser_than_the_catalog_fixes["target"] = json!({
        "kind": "feature",
        "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
        "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
        "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
        "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02"
    });

    let outcome = read(&addressed_coarser_than_the_catalog_fixes);

    assert!(
        outcome.is_err(),
        "a set-geometry operation addressed at the whole feature parsed as {outcome:?}"
    );
}

/// M9 as sharpened 2026-08-06, the other direction: finer than the catalog fixes is refused too,
/// so a create is never read as an edit of one property.
#[test]
fn a_create_feature_operation_addressed_at_a_property_is_refused() {
    let mut addressed_finer_than_the_catalog_fixes = a_create_feature_operation();
    addressed_finer_than_the_catalog_fixes["target"] = json!({
        "kind": "property",
        "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
        "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
        "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
        "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
        "property": "geometry"
    });

    let outcome = read(&addressed_finer_than_the_catalog_fixes);

    assert!(
        outcome.is_err(),
        "a create-feature operation addressed at one property parsed as {outcome:?}"
    );
}
