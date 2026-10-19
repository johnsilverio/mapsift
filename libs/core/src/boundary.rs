//! The serializable boundary to the UI. Data only, never a live reference (C11, M11).

use std::cell::RefCell;

use serde::Serialize;
use tsify::{Ts, Tsify};
use uuid::Uuid;
use wasm_bindgen::prelude::*;

use crate::metric::{self, Metric, MetricUnit};
use crate::queue::{FlushOffer, OperationQueue, QueueRecord, QueueRefusal};

/// A measurement as it crosses to the UI.
#[wasm_bindgen(getter_with_clone)]
pub struct MeasuredValue {
    pub value: f64,
    pub unit: String,
    pub frame: String,
    pub authority: String,
}

impl From<Metric> for MeasuredValue {
    fn from(metric: Metric) -> Self {
        Self {
            value: metric.value,
            unit: match metric.unit {
                MetricUnit::Metres => "m".to_owned(),
                MetricUnit::SquareMetres => "m2".to_owned(),
            },
            frame: "geodesic:SIRGAS2000".to_owned(),
            authority: "client-preview".to_owned(),
        }
    }
}

/// Geodesic distance in metres. Longitude precedes latitude in both pairs, matching the stored
/// axis order (M5); swapping them yields a confident and completely wrong number.
#[wasm_bindgen(js_name = geodesicDistance)]
pub fn geodesic_distance(
    from_longitude: f64,
    from_latitude: f64,
    to_longitude: f64,
    to_latitude: f64,
) -> MeasuredValue {
    metric::distance(
        geo::Point::new(from_longitude, from_latitude),
        geo::Point::new(to_longitude, to_latitude),
    )
    .into()
}

/// Why minting refused: the platform's source of randomness was unavailable (ADR-0015
/// decision 7).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(tag = "reason", rename_all = "snake_case")]
pub enum MintRefusal {
    RandomnessUnavailable,
}

/// Why a transition was refused by an instance holding no queue: none was opened yet (ADR-0015
/// decision 1).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(tag = "reason", rename_all = "snake_case")]
pub enum UnopenedRefusal {
    NoQueueOpen,
}

/// Why opening refused: what the store held, or the randomness a new installation's clientID is
/// minted from (ADR-0015 decisions 2, 5 and 7).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(untagged)]
pub enum OpenRefusal {
    Queue(QueueRefusal),
    Mint(MintRefusal),
}

/// Why appending refused: the operation, the randomness its identifier is minted from, or an
/// instance holding no queue (ADR-0015 decisions 1, 6 and 7).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(untagged)]
pub enum AppendRefusal {
    Queue(QueueRefusal),
    Mint(MintRefusal),
    Unopened(UnopenedRefusal),
}

/// What opening answers: the records to write, the installation record among them when the
/// store held none, or why nothing was opened (ADR-0015 decisions 1, 2 and 5).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Serialize, Tsify)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum OpenOutcome {
    Opened { records: Vec<QueueRecord> },
    Refused { refusal: OpenRefusal },
}

/// What appending answers: the records of the append, which are one unit, or why nothing was
/// queued (ADR-0015 decisions 3, 6 and 7).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Serialize, Tsify)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum AppendOutcome {
    Appended { records: Vec<QueueRecord> },
    Refused { refusal: AppendRefusal },
}

/// What a confirmation answers (ADR-0015 decisions 1 and 4).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum ConfirmOutcome {
    Confirmed,
    Refused { refusal: UnopenedRefusal },
}

/// What a request for the flush answers: per flush domain, what may leave for the server
/// (ADR-0015 decisions 1 and 4).
// Debug is absent, and no payload-bearing type in this contract derives it (N5); the note on
// `ClientHalf` carries the reasoning.
#[derive(Serialize, Tsify)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum OfferOutcome {
    Offered { offers: Vec<FlushOffer> },
    Refused { refusal: UnopenedRefusal },
}

/// What the generator answers: a random identifier in its canonical form, or the refused
/// randomness (M3, ADR-0006 decision 1, ADR-0015 decision 7).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Tsify)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum MintOutcome {
    Minted {
        #[tsify(type = "string")]
        identifier: Uuid,
    },
    Refused {
        refusal: MintRefusal,
    },
}

/// Opens this instance's queue from every record the platform holds, in any order, in place of
/// any queue it held before; a store holding no record is a new installation (M4, ADR-0015
/// decisions 1 and 2).
#[wasm_bindgen(js_name = openQueue)]
pub fn open_queue(records: Vec<Ts<QueueRecord>>) -> Ts<OpenOutcome> {
    let (opened, outcome) = match open_or_install(&records) {
        Ok((queue, records)) => (Some(queue), OpenOutcome::Opened { records }),
        Err(refusal) => (None, OpenOutcome::Refused { refusal }),
    };
    OPENED_QUEUE.set(opened);
    crossing(&outcome)
}

/// Appends the operation the platform authored, handed over as its JSON (ADR-0015 decisions 6
/// and 7).
#[wasm_bindgen(js_name = appendOperation)]
pub fn append_operation(operation: String) -> Ts<AppendOutcome> {
    let appended = with_opened_queue(|queue| {
        let operation_id = mint().map_err(AppendRefusal::Mint)?;
        queue
            .append(&operation, operation_id)
            .map_err(AppendRefusal::Queue)
    })
    .map_err(AppendRefusal::Unopened)
    .flatten();
    let outcome = match appended {
        Ok(records) => AppendOutcome::Appended { records },
        Err(refusal) => AppendOutcome::Refused { refusal },
    };
    crossing(&outcome)
}

/// Takes the platform's word that its store wrote the records under these keys (ADR-0015
/// decision 4).
#[wasm_bindgen(js_name = confirmWritten)]
pub fn confirm_written(keys: Vec<String>) -> Ts<ConfirmOutcome> {
    let outcome = match with_opened_queue(|queue| queue.confirm_written(&keys)) {
        Ok(()) => ConfirmOutcome::Confirmed,
        Err(refusal) => ConfirmOutcome::Refused { refusal },
    };
    crossing(&outcome)
}

/// Per flush domain, the confirmed operations up to the first one that is not confirmed, in
/// mutation-number order (ADR-0015 decision 4).
#[wasm_bindgen(js_name = offeredForFlush)]
pub fn offered_for_flush() -> Ts<OfferOutcome> {
    let outcome = match with_opened_queue(|queue| queue.offered_for_flush()) {
        Ok(offers) => OfferOutcome::Offered { offers },
        Err(refusal) => OfferOutcome::Refused { refusal },
    };
    crossing(&outcome)
}

/// Mints an identifier the platform needs before it composes an operation, a new feature's above
/// all, from the generator the queue mints with (T1.3, ADR-0015 decision 7).
#[wasm_bindgen(js_name = mintIdentifier)]
pub fn mint_identifier() -> Ts<MintOutcome> {
    let outcome = match mint() {
        Ok(identifier) => MintOutcome::Minted { identifier },
        Err(refusal) => MintOutcome::Refused { refusal },
    };
    crossing(&outcome)
}

thread_local! {
    static OPENED_QUEUE: RefCell<Option<OperationQueue>> = const { RefCell::new(None) };
}

fn with_opened_queue<T>(
    transition: impl FnOnce(&mut OperationQueue) -> T,
) -> Result<T, UnopenedRefusal> {
    OPENED_QUEUE.with_borrow_mut(|opened| {
        opened
            .as_mut()
            .map(transition)
            .ok_or(UnopenedRefusal::NoQueueOpen)
    })
}

fn open_or_install(
    records: &[Ts<QueueRecord>],
) -> Result<(OperationQueue, Vec<QueueRecord>), OpenRefusal> {
    if records.is_empty() {
        let client_id = mint().map_err(OpenRefusal::Mint)?;
        return Ok(OperationQueue::install(client_id));
    }
    let records = records
        .iter()
        .map(record_from_the_platform)
        .collect::<Result<Vec<_>, _>>()
        .map_err(OpenRefusal::Queue)?;
    let queue = OperationQueue::open(records).map_err(OpenRefusal::Queue)?;
    Ok((queue, Vec::new()))
}

/// The record as the platform handed it over. One that is not a `QueueRecord` at all has no key
/// the core can read, so its refusal names the empty key.
fn record_from_the_platform(record: &Ts<QueueRecord>) -> Result<QueueRecord, QueueRefusal> {
    record
        .to_rust()
        .map_err(|_| QueueRefusal::UnreadableRecord { key: String::new() })
}

fn mint() -> Result<Uuid, MintRefusal> {
    let mut random_bytes = [0; 16];
    getrandom::fill(&mut random_bytes).map_err(|_| MintRefusal::RandomnessUnavailable)?;
    Ok(uuid::Builder::from_random_bytes(random_bytes).into_uuid())
}

fn crossing<T: Tsify + Serialize>(outcome: &T) -> Ts<T> {
    Ts::from_rust(outcome).expect("an outcome of strings, numbers and tags converts to JS")
}
