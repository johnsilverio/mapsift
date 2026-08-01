//! Client-side measurements, always carrying the frame and authority that produced them (M5).

use geo::algorithm::GeodesicArea;
use geo::algorithm::line_measures::Distance;
use geo::{Geodesic, Point, Polygon};

/// The frame a measurement was computed in.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MetricFrame {
    GeodesicSirgas2000,
}

/// Who produced a measurement, which decides what it may be used for. The single variant is the
/// point: this crate cannot construct an authoritative value, only a preview (T4.2).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MetricAuthority {
    ClientPreview,
}

/// The unit a measurement is expressed in. Degrees are absent by construction (M5).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MetricUnit {
    Metres,
    SquareMetres,
}

/// A measurement together with everything needed to judge it.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Metric {
    pub value: f64,
    pub unit: MetricUnit,
    pub frame: MetricFrame,
    pub authority: MetricAuthority,
}

/// Geodesic distance in metres between two positions given in degrees, longitude first.
pub fn distance(from: Point<f64>, to: Point<f64>) -> Metric {
    Metric {
        value: Geodesic.distance(from, to),
        unit: MetricUnit::Metres,
        frame: MetricFrame::GeodesicSirgas2000,
        authority: MetricAuthority::ClientPreview,
    }
}

/// Geodesic area in square metres, positive whatever the ring's orientation.
pub fn area(polygon: &Polygon<f64>) -> Metric {
    Metric {
        // Not `geodesic_area_unsigned`, whose name lies: it returns the area enclosed under the
        // ring's own orientation, so a reversed ring yields the rest of the planet. Measured on
        // a one-degree square: 1.23e10 the right way round, 5.10e14 the wrong way.
        value: polygon.geodesic_area_signed().abs(),
        unit: MetricUnit::SquareMetres,
        frame: MetricFrame::GeodesicSirgas2000,
        authority: MetricAuthority::ClientPreview,
    }
}

/// Geodesic perimeter in metres.
pub fn perimeter(polygon: &Polygon<f64>) -> Metric {
    Metric {
        value: polygon.geodesic_perimeter(),
        unit: MetricUnit::Metres,
        frame: MetricFrame::GeodesicSirgas2000,
        authority: MetricAuthority::ClientPreview,
    }
}
