//! What the queue's records hold, keyed and versioned as ADR-0015 decisions 2, 5 and 6 fix.

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use super::{FlushDomain, QueueRecord, QueueRefusal, to_json};
use crate::envelope::ClientHalf;

/// The version of the record contract this core writes and the only one it reads.
const CONTRACT_VERSION: u32 = 1;

/// What one record holds: an operation's client half borrowed when written, owned when read.
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub(super) enum RecordContent<Half> {
    Installation {
        client_id: Uuid,
    },
    Stream {
        tenant_id: Uuid,
        project_id: Uuid,
        next_mutation_number: u64,
    },
    Entry(Half),
}

#[derive(Serialize, Deserialize)]
struct RecordValue<Half> {
    contract_version: u32,
    #[serde(flatten)]
    content: RecordContent<Half>,
}

pub(super) fn installation_record(client_id: Uuid) -> QueueRecord {
    written(
        "installation".to_owned(),
        RecordContent::Installation { client_id },
    )
}

pub(super) fn stream_record(domain: FlushDomain, next_mutation_number: u64) -> QueueRecord {
    written(
        format!("stream/{}/{}", domain.tenant_id, domain.project_id),
        RecordContent::Stream {
            tenant_id: domain.tenant_id,
            project_id: domain.project_id,
            next_mutation_number,
        },
    )
}

pub(super) fn entry_record(half: &ClientHalf) -> QueueRecord {
    let domain = FlushDomain::of(&half.operation);
    written(
        format!(
            "entry/{}/{}/{}",
            domain.tenant_id, domain.project_id, half.mutation_number.0
        ),
        RecordContent::Entry(half),
    )
}

/// What the record holds, or its refusal when its value is not this contract version's.
pub(super) fn read_record(record: &QueueRecord) -> Result<RecordContent<ClientHalf>, QueueRefusal> {
    serde_json::from_str::<RecordValue<ClientHalf>>(&record.value)
        .ok()
        .filter(|value| value.contract_version == CONTRACT_VERSION)
        .map(|value| value.content)
        .ok_or_else(|| QueueRefusal::UnreadableRecord {
            key: record.key.clone(),
        })
}

fn written(key: String, content: RecordContent<&ClientHalf>) -> QueueRecord {
    QueueRecord {
        key,
        value: to_json(&RecordValue {
            contract_version: CONTRACT_VERSION,
            content,
        }),
    }
}
