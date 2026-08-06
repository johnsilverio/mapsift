//! The Mapsift client logic core: offline operation queue, optimistic apply, optimistic conflict
//! detection, and client-side geometry.
//!
//! Compiled to WebAssembly for the web and desktop clients and to a native FFI library for
//! mobile. It runs on clients only; everything it decides is a preview the server reconciles.
//! See `specs/mapsift-foundation.md` section 9.6.

pub mod boundary;
pub mod envelope;
pub mod metric;
