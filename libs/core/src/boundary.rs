//! The serializable boundary to the UI. Data only, never a live reference (C11, M11).

use wasm_bindgen::prelude::*;

use crate::metric::{self, Metric, MetricUnit};

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
