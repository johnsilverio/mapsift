//! Covers PRD M5 (no metric in degrees, every metric declares its frame) and T4.2 (the client
//! produces previews, never authoritative values).

use geo::{Coord, LineString, Point, Polygon};
use mapsift_core::metric::{self, MetricAuthority, MetricFrame, MetricUnit};

/// One degree of longitude on the equator is an exact arc of the equatorial circle, so this is
/// checkable by hand rather than copied from a previous run of the code under test.
const ONE_DEGREE_ON_THE_EQUATOR_METRES: f64 = 6_378_137.0 * std::f64::consts::PI / 180.0;

fn square_degree_at_the_equator() -> Polygon<f64> {
    Polygon::new(
        LineString::from(vec![
            Coord { x: 0.0, y: 0.0 },
            Coord { x: 1.0, y: 0.0 },
            Coord { x: 1.0, y: 1.0 },
            Coord { x: 0.0, y: 1.0 },
            Coord { x: 0.0, y: 0.0 },
        ]),
        vec![],
    )
}

#[test]
fn a_distance_comes_back_in_metres_and_never_in_degrees() {
    let measured = metric::distance(Point::new(0.0, 0.0), Point::new(1.0, 0.0));

    assert_eq!(measured.unit, MetricUnit::Metres);
    assert!(
        (measured.value - ONE_DEGREE_ON_THE_EQUATOR_METRES).abs() < 0.001,
        "expected about {ONE_DEGREE_ON_THE_EQUATOR_METRES} m, got {}",
        measured.value
    );
}

#[test]
fn the_earth_is_measured_as_an_ellipsoid_rather_than_a_sphere() {
    let along_the_equator = metric::distance(Point::new(0.0, 0.0), Point::new(1.0, 0.0));
    let along_a_meridian = metric::distance(Point::new(0.0, 0.0), Point::new(0.0, 1.0));

    assert!(
        along_a_meridian.value < along_the_equator.value,
        "a meridian degree ({}) should be shorter than an equatorial one ({})",
        along_a_meridian.value,
        along_the_equator.value
    );
    assert!(
        (along_a_meridian.value - 110_574.0).abs() < 50.0,
        "expected about 110 574 m, got {}",
        along_a_meridian.value
    );
}

#[test]
fn every_metric_declares_its_frame_and_its_authority() {
    let measured = metric::distance(Point::new(-47.9, -15.8), Point::new(-46.6, -23.5));

    assert_eq!(measured.frame, MetricFrame::GeodesicSirgas2000);
    assert_eq!(measured.authority, MetricAuthority::ClientPreview);
}

#[test]
fn an_area_comes_back_in_square_metres() {
    let measured = metric::area(&square_degree_at_the_equator());

    assert_eq!(measured.unit, MetricUnit::SquareMetres);
    assert_eq!(measured.frame, MetricFrame::GeodesicSirgas2000);
    assert!(
        measured.value > 1.2e10 && measured.value < 1.3e10,
        "expected roughly 1.23e10 square metres, got {}",
        measured.value
    );
}

#[test]
fn area_ignores_the_winding_order_of_the_ring() {
    let clockwise = square_degree_at_the_equator();
    let mut reversed_coords: Vec<Coord<f64>> = clockwise.exterior().coords().copied().collect();
    reversed_coords.reverse();
    let counter_clockwise = Polygon::new(LineString::from(reversed_coords), vec![]);

    assert!((metric::area(&clockwise).value - metric::area(&counter_clockwise).value).abs() < 1.0);

    // A reversed ring measured with `geodesic_area_unsigned` returns the rest of the planet, an
    // enormous wrong number that looks like a number rather than like an error.
    const SURFACE_OF_THE_EARTH_SQUARE_METRES: f64 = 5.1e14;
    assert!(
        metric::area(&clockwise).value < SURFACE_OF_THE_EARTH_SQUARE_METRES / 1000.0,
        "the area came back planetary, so the complement was measured: {}",
        metric::area(&clockwise).value
    );
}

#[test]
fn a_perimeter_comes_back_in_metres() {
    let measured = metric::perimeter(&square_degree_at_the_equator());

    assert_eq!(measured.unit, MetricUnit::Metres);
    assert!(
        measured.value > 400_000.0 && measured.value < 450_000.0,
        "expected roughly 443 km, got {}",
        measured.value
    );
}
