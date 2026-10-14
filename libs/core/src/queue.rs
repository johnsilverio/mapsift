//! The client's operation queue, durable as the records the platform writes and hands back.
//!
//! Trace: T1.2 (the queue survives a restart behind one storage interface), M3 and M4 (the
//! identifiers it stamps), M10 (the mutation number, per flush domain, from zero), ADR-0015 (the
//! record contract, decisions 1 to 7).

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tsify::Tsify;
use uuid::Uuid;

use crate::catalog::Operation;
use crate::envelope::MediationProvenance;

/// One record the platform stores under its key and hands back on open, never reading its value
/// (ADR-0015 decision 6).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Clone, PartialEq, Eq, Serialize, Deserialize, Tsify)]
pub struct QueueRecord {
    pub key: String,
    pub value: String,
}

/// The pending operations of one flush domain, as the JSON of their client halves in
/// mutation-number order (ADR-0015 decisions 4 and 6).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Clone, PartialEq, Eq, Serialize, Deserialize, Tsify)]
pub struct FlushOffer {
    #[tsify(type = "string")]
    pub tenant_id: Uuid,
    #[tsify(type = "string")]
    pub project_id: Uuid,
    pub operations: Vec<String>,
}

/// What the platform authored and only it knows, which the queue stamps into a client half
/// (ADR-0015 decision 7).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Serialize, Deserialize, Tsify)]
#[tsify(missing_as_null)]
pub struct AuthoredOperation {
    /// The catalog member, with the target and payload that member declares (M9).
    #[serde(flatten)]
    #[tsify(type = "Operation")]
    pub operation: Operation,
    /// Opaque to the core: the proof mechanism is OQ-18's and the server is what verifies it.
    #[tsify(type = "unknown")]
    pub author_session_material: Value,
    #[tsify(type = "string")]
    pub created_at: DateTime<Utc>,
    pub mediation: Option<MediationProvenance>,
}

/// Why the queue refused a transition. It is a value, never a panic (ADR-0015 decision 6).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Tsify)]
#[serde(tag = "reason", rename_all = "snake_case")]
pub enum QueueRefusal {
    /// A record the core cannot read, which fails the open rather than yielding a queue without
    /// it (ADR-0015 decision 5).
    UnreadableRecord { key: String },
    /// An operation the core cannot parse, a member outside the closed catalog included
    /// (ADR-0015 decision 6, M9).
    UnparsableOperation,
    /// Records with no installation record among them, which are never given a new clientID
    /// (ADR-0015 decision 2).
    NoInstallationRecord,
}

/// The queue of one installation. It holds no store: every transition returns the records the
/// platform writes, and randomness reaches it as arguments (ADR-0015 decision 1).
pub struct OperationQueue {}

impl OperationQueue {
    /// The queue of a new installation, under the clientID minted for it, with the installation
    /// record the platform writes (M4, ADR-0015 decision 2).
    pub fn install(client_id: Uuid) -> (Self, Vec<QueueRecord>) {
        let _ = client_id;
        todo!()
    }

    /// The queue the records describe, whatever order they come back in. A record the core cannot
    /// read fails the open, and so do records holding no installation record (ADR-0015
    /// decisions 1, 2 and 5).
    pub fn open(records: Vec<QueueRecord>) -> Result<Self, QueueRefusal> {
        let _ = records;
        todo!()
    }

    /// Stamps the operation the platform authored, numbers it within its flush domain, and returns
    /// the records of the append, which are one unit (ADR-0015 decisions 2, 3, 6 and 7).
    pub fn append(
        &mut self,
        operation: &str,
        operation_id: Uuid,
    ) -> Result<Vec<QueueRecord>, QueueRefusal> {
        let _ = (operation, operation_id);
        todo!()
    }

    /// Takes the platform's word that its store wrote the records under these keys (ADR-0015
    /// decision 4).
    pub fn confirm_written(&mut self, keys: &[String]) {
        let _ = keys;
        todo!()
    }

    /// Per flush domain, the confirmed operations up to the first one that is not confirmed, in
    /// mutation-number order (ADR-0015 decision 4).
    pub fn offered_for_flush(&self) -> Vec<FlushOffer> {
        todo!()
    }
}
