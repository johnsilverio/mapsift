//! The operation envelope, defined once and read everywhere else through a generated form.
//!
//! Trace: M8 (the envelope and its two halves), M9 (one target path per operation, and the
//! type-to-target-kind pairing), M10 and T9.2 (the five envelope-borne version axes, each of them
//! a type), ADR-0004 section 4 (the fifth is the per-project version, the resync cursor), T5.3
//! (created-at against applied-at), M7 (the classification in force), T8.2 and C14 (mediation),
//! ADR-0009 (the generation toolchain).

use chrono::{DateTime, Utc};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tsify::Tsify;
use uuid::Uuid;

use crate::catalog::Operation;

/// The per-client monotonic axis the server dedups a resent flush by (C12).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct MutationNumber(pub u64);

/// The build-time axis, one per operation type, that drives upcasting (T9.3).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct OperationSchemaVersion(pub u32);

/// The build-time axis, one per runtime, that detects temporal skew between them (T4.3).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct ConflictRuleVersion(pub u32);

/// The per-feature axis that orders and detects conflict on one feature (M10).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct FeatureVersion(pub u64);

/// The per-project axis a client presents as its resync cursor (M10, ADR-0004 section 4).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct ProjectVersion(pub u64);

/// An operation as the client authored it. Every field here is the client's claim; nothing in it
/// is authoritative until the server half exists beside it.
// Debug is absent on purpose and stays absent: an all-fields Debug prints the payload and the
// session material, and neither may reach a log line (N5, N9).
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
// An absent mediation goes on the wire as an explicit null (M8, the envelope is self-describing),
// so the generated TypeScript has to say `null` and not tsify's default `undefined`.
#[tsify(missing_as_null)]
pub struct ClientHalf {
    #[tsify(type = "string")]
    pub operation_id: Uuid,
    #[tsify(type = "string")]
    pub client_id: Uuid,
    pub mutation_number: MutationNumber,
    /// The catalog member this operation is, with the target and payload that member declares.
    // Flattened so the type, the target and the payload stay flat sibling keys of the envelope
    // (M8): a nested object here would be a wire change nobody asked for.
    #[serde(flatten)]
    #[tsify(type = "Operation")]
    pub operation: Operation,
    pub operation_schema_version: OperationSchemaVersion,
    pub conflict_rule_version: ConflictRuleVersion,
    /// Opaque to the core: the proof mechanism is OQ-18's and the server is what verifies it.
    #[tsify(type = "unknown")]
    pub author_session_material: Value,
    #[tsify(type = "string")]
    pub created_at: DateTime<Utc>,
    pub mediation: Option<MediationProvenance>,
}

/// What the server added when it applied the operation. Authoritative, and never merged into the
/// client's half.
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
pub struct ServerHalf {
    #[tsify(type = "string")]
    pub applied_at: DateTime<Utc>,
    pub feature_version: FeatureVersion,
    pub project_version: ProjectVersion,
    pub applied_rule_version: ConflictRuleVersion,
    pub legal_weight_in_force: bool,
    pub verdict: Verdict,
}

/// An operation the server has applied: both halves, side by side and separately addressable.
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
pub struct AppliedOperation {
    pub client: ClientHalf,
    pub server: ServerHalf,
}

/// The granularity an address is measured at (M9). A decision helper the core reads a catalog
/// member's declared target through; it never crosses the boundary and has no generated form.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TargetKind {
    Tenant,
    Project,
    Layer,
    Feature,
    Property,
}

/// A tenant address, and the whole of what one operation may target at that granularity (M9).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum TenantTarget {
    #[schemars(title = "TenantAddress")]
    Tenant {
        #[tsify(type = "string")]
        tenant_id: Uuid,
    },
}

impl TenantTarget {
    /// The static half of the M9 pairing: this address type declares tenant granularity.
    pub const KIND: TargetKind = TargetKind::Tenant;
}

/// A project address, carrying its ancestors so it resolves without a lookup (M9).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum ProjectTarget {
    #[schemars(title = "ProjectAddress")]
    Project {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
    },
}

impl ProjectTarget {
    /// The static half of the M9 pairing: this address type declares project granularity.
    pub const KIND: TargetKind = TargetKind::Project;
}

/// A layer address, carrying its ancestors so it resolves without a lookup (M9).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum LayerTarget {
    #[schemars(title = "LayerAddress")]
    Layer {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
        #[tsify(type = "string")]
        layer_id: Uuid,
    },
}

impl LayerTarget {
    /// The static half of the M9 pairing: this address type declares layer granularity.
    pub const KIND: TargetKind = TargetKind::Layer;
}

/// A whole-feature address, carrying its ancestors so it resolves without a lookup (M9).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum FeatureTarget {
    #[schemars(title = "FeatureAddress")]
    Feature {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
        #[tsify(type = "string")]
        layer_id: Uuid,
        #[tsify(type = "string")]
        feature_id: Uuid,
    },
}

impl FeatureTarget {
    /// The static half of the M9 pairing: this address type declares feature granularity.
    pub const KIND: TargetKind = TargetKind::Feature;
}

/// One property of one feature, the finest granularity the ladder measures a conflict on (M9).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
pub enum PropertyTarget {
    #[schemars(title = "PropertyAddress")]
    Property {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
        #[tsify(type = "string")]
        layer_id: Uuid,
        #[tsify(type = "string")]
        feature_id: Uuid,
        property: String,
    },
}

impl PropertyTarget {
    /// The static half of the M9 pairing: this address type declares property granularity.
    pub const KIND: TargetKind = TargetKind::Property;
}

/// Any one address an operation may target (M9), and the union the disjointness decision in
/// `crate::granularity` consumes.
// Untagged because each member already carries its own `kind` as a validated literal, which is
// what lets a catalog member's target field be typed to one member rather than to this union.
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(untagged)]
// Deleting this silently degrades the generated Pydantic union to routing by trial
// (ADR-0009 section 5).
#[schemars(extend("discriminator" = {"propertyName": "kind"}))]
pub enum TargetPath {
    Tenant(TenantTarget),
    Project(ProjectTarget),
    Layer(LayerTarget),
    Feature(FeatureTarget),
    Property(PropertyTarget),
}

/// Present when the write reached the queue through an agent acting for the author, absent when
/// the author wrote directly (C14).
#[derive(Debug, PartialEq, Serialize, Deserialize, JsonSchema, Tsify)]
pub struct MediationProvenance {
    pub agent: String,
}

/// What the server decided about the operation. A closed set, declared by M13 and grown
/// additively.
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(rename_all = "lowercase")]
pub enum Verdict {
    Applied,
}
