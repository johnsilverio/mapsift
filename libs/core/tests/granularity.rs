//! Two operations meet only when they address the same target path: the pure decision the
//! granularity ladder rests on.
//!
//! Trace: M9 (the conflict unit **is** the target path), T3.1 (different features never conflict,
//! and neither do different properties of one feature), foundation section 4; C2.
//!
//! What a verdict is once two operations do meet belongs to the conflict rule (M13) and is not
//! decided here; this is the disjointness half alone. The nested case, an ancestor address against
//! a descendant of it, is deferred to the conflict slice with T3.4 (delete against edit) rather
//! than pinned here, because that is where the rule that decides it lands.

use mapsift_core::envelope::TargetPath;
use mapsift_core::granularity;

const THE_GEOMETRY_OF_ONE_FEATURE: &str = r#"{
  "kind": "property",
  "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
  "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
  "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
  "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
  "property": "geometry"
}"#;

const THE_NAME_OF_THE_SAME_FEATURE: &str = r#"{
  "kind": "property",
  "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
  "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
  "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
  "feature_id": "c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02",
  "property": "name"
}"#;

const THE_GEOMETRY_OF_ANOTHER_FEATURE_IN_THE_SAME_LAYER: &str = r#"{
  "kind": "property",
  "tenant_id": "7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b",
  "project_id": "2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70",
  "layer_id": "5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19",
  "feature_id": "8d2f6a04-7b19-4c53-ae86-0f5d3b1c9e47",
  "property": "geometry"
}"#;

fn a_target_path(wire: &str) -> TargetPath {
    serde_json::from_str(wire).expect("the target path must parse")
}

#[test]
fn two_operations_on_different_properties_of_one_feature_never_conflict() {
    let geometry = a_target_path(THE_GEOMETRY_OF_ONE_FEATURE);
    let name = a_target_path(THE_NAME_OF_THE_SAME_FEATURE);

    assert!(granularity::are_disjoint(&geometry, &name));
}

#[test]
fn two_operations_on_the_same_property_of_different_features_never_conflict() {
    let one_reserve = a_target_path(THE_GEOMETRY_OF_ONE_FEATURE);
    let its_neighbour = a_target_path(THE_GEOMETRY_OF_ANOTHER_FEATURE_IN_THE_SAME_LAYER);

    assert!(granularity::are_disjoint(&one_reserve, &its_neighbour));
}

#[test]
fn two_operations_on_one_property_of_one_feature_meet_on_the_same_conflict_unit() {
    let drawn_on_one_client = a_target_path(THE_GEOMETRY_OF_ONE_FEATURE);
    let redrawn_on_another = a_target_path(THE_GEOMETRY_OF_ONE_FEATURE);

    assert!(!granularity::are_disjoint(
        &drawn_on_one_client,
        &redrawn_on_another
    ));
}
