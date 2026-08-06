//! The operation envelope, defined once and read everywhere else through a generated form.
//!
//! Trace: M8 (the envelope and its two halves), M9 (one target path per operation), M10 and T9.2
//! (the four envelope-borne version axes), T5.3 (created-at against applied-at), M7 (the
//! classification in force), T8.2 and C14 (mediation), ADR-0009 (the generation toolchain).

use chrono::{DateTime, Utc};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tsify::Tsify;
use uuid::Uuid;

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
    pub mutation_number: u64,
    pub operation_type: String,
    pub operation_schema_version: u32,
    pub conflict_rule_version: u32,
    pub target: TargetPath,
    /// Opaque to the core: the operation type says how to read it, over the catalog M9 owns.
    #[tsify(type = "unknown")]
    pub payload: Value,
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
    pub feature_version: u64,
    pub applied_rule_version: u32,
    pub legal_weight_in_force: bool,
    pub verdict: Verdict,
}

/// An operation the server has applied: both halves, side by side and separately addressable.
#[derive(Serialize, Deserialize, JsonSchema, Tsify)]
pub struct AppliedOperation {
    pub client: ClientHalf,
    pub server: ServerHalf,
}

/// The one address an operation targets, at the granularity the conflict unit is measured on
/// (M9). Each variant carries its ancestors, so an address is resolvable without a lookup.
#[derive(Debug, Serialize, Deserialize, JsonSchema, Tsify)]
#[serde(tag = "kind", rename_all = "lowercase")]
// The keyword schemars does not emit on its own: without it datamodel-code-generator reads the
// `const` tag as an ordinary union member and the generated Pydantic model routes by trial
// instead of by tag (ADR-0009 section 5).
#[schemars(extend("discriminator" = {"propertyName": "kind"}))]
pub enum TargetPath {
    #[schemars(title = "TenantTarget")]
    Tenant {
        #[tsify(type = "string")]
        tenant_id: Uuid,
    },
    #[schemars(title = "ProjectTarget")]
    Project {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
    },
    #[schemars(title = "LayerTarget")]
    Layer {
        #[tsify(type = "string")]
        tenant_id: Uuid,
        #[tsify(type = "string")]
        project_id: Uuid,
        #[tsify(type = "string")]
        layer_id: Uuid,
    },
    #[schemars(title = "FeatureTarget")]
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
    #[schemars(title = "PropertyTarget")]
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
