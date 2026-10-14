//! The serializable boundary to the UI. Data only, never a live reference (C11, M11).

use serde::Serialize;
use tsify::{Ts, Tsify};
use uuid::Uuid;
use wasm_bindgen::prelude::*;

use crate::metric::{self, Metric, MetricUnit};
use crate::queue::{FlushOffer, QueueRecord, QueueRefusal};

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
    let _ = records;
    todo!()
}

/// Appends the operation the platform authored, handed over as its JSON (ADR-0015 decisions 6
/// and 7).
#[wasm_bindgen(js_name = appendOperation)]
pub fn append_operation(operation: String) -> Ts<AppendOutcome> {
    let _ = operation;
    todo!()
}

/// Takes the platform's word that its store wrote the records under these keys (ADR-0015
/// decision 4).
#[wasm_bindgen(js_name = confirmWritten)]
pub fn confirm_written(keys: Vec<String>) -> Ts<ConfirmOutcome> {
    let _ = keys;
    todo!()
}

/// Per flush domain, the confirmed operations up to the first one that is not confirmed, in
/// mutation-number order (ADR-0015 decision 4).
#[wasm_bindgen(js_name = offeredForFlush)]
pub fn offered_for_flush() -> Ts<OfferOutcome> {
    todo!()
}

/// Mints an identifier the platform needs before it composes an operation, a new feature's above
/// all, from the generator the queue mints with (T1.3, ADR-0015 decision 7).
#[wasm_bindgen(js_name = mintIdentifier)]
pub fn mint_identifier() -> Ts<MintOutcome> {
    todo!()
}
