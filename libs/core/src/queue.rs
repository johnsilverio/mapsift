//! The client's operation queue, durable as the records the platform writes and hands back.
//!
//! Trace: T1.2 (the queue survives a restart behind one storage interface), M3 and M4 (the
//! identifiers it stamps), M10 (the mutation number, per flush domain, from zero), ADR-0015 (the
//! record contract, decisions 1 to 7).

mod record;

use std::collections::{BTreeMap, HashMap};

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tsify::Tsify;
use uuid::Uuid;

use crate::catalog::Operation;
use crate::envelope::{
    ClientHalf, ConflictRuleVersion, FeatureTarget, MediationProvenance, MutationNumber,
    OperationSchemaVersion, PropertyTarget,
};
use record::{RecordContent, entry_record, installation_record, read_record, stream_record};

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
pub struct OperationQueue {
    client_id: Uuid,
    streams: BTreeMap<FlushDomain, Stream>,
    unconfirmed: HashMap<String, (FlushDomain, u64)>,
}

impl OperationQueue {
    /// The queue of a new installation, under the clientID minted for it, with the installation
    /// record the platform writes (M4, ADR-0015 decision 2).
    pub fn install(client_id: Uuid) -> (Self, Vec<QueueRecord>) {
        let queue = Self {
            client_id,
            streams: BTreeMap::new(),
            unconfirmed: HashMap::new(),
        };
        (queue, vec![installation_record(client_id)])
    }

    /// The queue the records describe, whatever order they come back in. A record the core cannot
    /// read fails the open, and so do records holding no installation record (ADR-0015
    /// decisions 1, 2 and 5).
    pub fn open(records: Vec<QueueRecord>) -> Result<Self, QueueRefusal> {
        let mut client_id = None;
        let mut streams: BTreeMap<FlushDomain, Stream> = BTreeMap::new();
        for record in &records {
            match read_record(record)? {
                RecordContent::Installation {
                    client_id: installed,
                } => client_id = Some(installed),
                RecordContent::Stream {
                    tenant_id,
                    project_id,
                    next_mutation_number,
                } => {
                    let domain = FlushDomain {
                        tenant_id,
                        project_id,
                    };
                    streams.entry(domain).or_default().next_mutation_number = next_mutation_number;
                }
                RecordContent::Entry(half) => {
                    let stream = streams.entry(FlushDomain::of(&half.operation)).or_default();
                    stream.entries.insert(
                        half.mutation_number.0,
                        Entry {
                            half,
                            confirmed: true,
                        },
                    );
                }
            }
        }
        Ok(Self {
            client_id: client_id.ok_or(QueueRefusal::NoInstallationRecord)?,
            streams,
            unconfirmed: HashMap::new(),
        })
    }

    /// Stamps the operation the platform authored, numbers it within its flush domain, and returns
    /// the records of the append, which are one unit (ADR-0015 decisions 2, 3, 6 and 7).
    pub fn append(
        &mut self,
        operation: &str,
        operation_id: Uuid,
    ) -> Result<Vec<QueueRecord>, QueueRefusal> {
        let authored: AuthoredOperation =
            serde_json::from_str(operation).map_err(|_| QueueRefusal::UnparsableOperation)?;
        let domain = FlushDomain::of(&authored.operation);
        let stream = self.streams.entry(domain).or_default();
        let mutation_number = stream.next_mutation_number;
        stream.next_mutation_number += 1;
        let half = authored.stamped(operation_id, self.client_id, mutation_number);
        let entry = entry_record(&half);
        self.unconfirmed
            .insert(entry.key.clone(), (domain, mutation_number));
        stream.entries.insert(
            mutation_number,
            Entry {
                half,
                confirmed: false,
            },
        );
        Ok(vec![
            entry,
            stream_record(domain, stream.next_mutation_number),
        ])
    }

    /// Takes the platform's word that its store wrote the records under these keys (ADR-0015
    /// decision 4).
    pub fn confirm_written(&mut self, keys: &[String]) {
        for (domain, mutation_number) in keys.iter().filter_map(|key| self.unconfirmed.remove(key))
        {
            let entry = self
                .streams
                .get_mut(&domain)
                .and_then(|stream| stream.entries.get_mut(&mutation_number));
            if let Some(entry) = entry {
                entry.confirmed = true;
            }
        }
    }

    /// Per flush domain, the confirmed operations up to the first one that is not confirmed, in
    /// mutation-number order (ADR-0015 decision 4).
    pub fn offered_for_flush(&self) -> Vec<FlushOffer> {
        self.streams
            .iter()
            .filter_map(|(domain, stream)| stream.offer(*domain))
            .collect()
    }
}

const CONFLICT_RULE_VERSION: ConflictRuleVersion = ConflictRuleVersion(0);

impl AuthoredOperation {
    fn stamped(self, operation_id: Uuid, client_id: Uuid, mutation_number: u64) -> ClientHalf {
        let Self {
            operation,
            author_session_material,
            created_at,
            mediation,
        } = self;
        ClientHalf {
            operation_id,
            client_id,
            mutation_number: MutationNumber(mutation_number),
            operation_schema_version: operation_schema_version_of(&operation),
            conflict_rule_version: CONFLICT_RULE_VERSION,
            operation,
            author_session_material,
            created_at,
            mediation,
        }
    }
}

fn operation_schema_version_of(operation: &Operation) -> OperationSchemaVersion {
    match operation {
        Operation::FeatureCreate { .. } | Operation::FeatureGeometrySet { .. } => {
            OperationSchemaVersion(1)
        }
    }
}

/// One tenant and one project, the domain a stream of mutation numbers belongs to (M10).
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct FlushDomain {
    tenant_id: Uuid,
    project_id: Uuid,
}

impl FlushDomain {
    fn of(operation: &Operation) -> Self {
        match operation {
            Operation::FeatureCreate {
                target:
                    FeatureTarget::Feature {
                        tenant_id,
                        project_id,
                        ..
                    },
                ..
            }
            | Operation::FeatureGeometrySet {
                target:
                    PropertyTarget::Property {
                        tenant_id,
                        project_id,
                        ..
                    },
                ..
            } => Self {
                tenant_id: *tenant_id,
                project_id: *project_id,
            },
        }
    }
}

#[derive(Default)]
struct Stream {
    next_mutation_number: u64,
    entries: BTreeMap<u64, Entry>,
}

impl Stream {
    fn offer(&self, domain: FlushDomain) -> Option<FlushOffer> {
        let operations: Vec<String> = self
            .entries
            .values()
            .take_while(|entry| entry.confirmed)
            .map(|entry| to_json(&entry.half))
            .collect();
        (!operations.is_empty()).then_some(FlushOffer {
            tenant_id: domain.tenant_id,
            project_id: domain.project_id,
            operations,
        })
    }
}

struct Entry {
    half: ClientHalf,
    confirmed: bool,
}

fn to_json<T: Serialize>(value: &T) -> String {
    serde_json::to_string(value).expect("a queue type has string keys and serializes infallibly")
}
