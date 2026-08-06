//! The closed operation catalog: what an operation may be, what it addresses, and what it carries.
//!
//! Trace: M9 (the closed named catalog, one target path per operation, the type-to-target-kind
//! pairing, the whole geometry rather than a vertex delta, the typed refusal of a type nobody
//! declared), M8 (the envelope this narrows), ADR-0009 section 5 (the guard rules).

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tsify::Tsify;

use crate::envelope::{FeatureTarget, PropertyTarget, TargetKind};

/// Every operation Mapsift declares. The set is closed, so a member is a decision rather than a
/// habit (M9), and nothing outside it reaches the queue.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OperationType {
    FeatureCreate,
    FeatureGeometrySet,
}

impl OperationType {
    /// The catalog in its canonical order, which is **append-only**: a new member goes at the
    /// end, never between two that exist, so a position in this slice keeps its meaning.
    pub const CATALOG: &'static [OperationType] = &[
        OperationType::FeatureCreate,
        OperationType::FeatureGeometrySet,
    ];

    /// The granularity this member addresses at, read off the target type its wire form declares
    /// so the pairing of M9 is stated once rather than twice.
    pub fn target_kind(&self) -> TargetKind {
        match self {
            Self::FeatureCreate => FeatureTarget::KIND,
            Self::FeatureGeometrySet => PropertyTarget::KIND,
        }
    }
}

/// A catalog member on the wire: the type that says how to read the operation, the one target
/// path it addresses, and the payload that type declares (M8, M9).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "operation_type")]
// Deleting this silently degrades the generated Pydantic union to routing by trial
// (ADR-0009 section 5).
#[schemars(extend("discriminator" = {"propertyName": "operation_type"}))]
pub enum Operation {
    #[serde(rename = "feature.create")]
    #[schemars(title = "FeatureCreateOperation")]
    FeatureCreate {
        target: FeatureTarget,
        payload: FeatureCreatePayload,
    },
    #[serde(rename = "feature.geometry.set")]
    #[schemars(title = "FeatureGeometrySetOperation")]
    FeatureGeometrySet {
        target: PropertyTarget,
        payload: FeatureGeometrySetPayload,
    },
}

/// What creating a feature carries: nothing beyond the address it creates. Everything the feature
/// then holds arrives as the operations that address it (M9, M15).
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
pub struct FeatureCreatePayload {}

/// The whole geometry the feature is being set to, never a vertex delta, because
/// preserve-not-discard needs both whole versions presentable (M9, C7).
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
pub struct FeatureGeometrySetPayload {
    /// A GeoJSON-shaped structure in the M5 storage frame. Opaque to the core until the boundary
    /// encoding is decided (MAP-33).
    #[tsify(type = "unknown")]
    pub geometry: Value,
}
