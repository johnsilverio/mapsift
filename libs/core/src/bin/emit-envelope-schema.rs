//! Prints the envelope's JSON Schema to stdout, from which `apps/api` generates its Pydantic
//! reader. The committed artifact is `libs/core/schema/envelope.schema.json` and `just contracts`
//! is what fails when the two diverge (ADR-0009 section 2).

use std::io::Write;

use mapsift_core::envelope::AppliedOperation;
use schemars::generate::SchemaSettings;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // The dialect is pinned rather than defaulted: schemars documents its default as liable to
    // change, and a dialect that moves under the generator moves the generated model with it.
    //
    // The serialize contract is what makes an Option field a required nullable key rather than an
    // absent one, which is the wire form M8 fixes. `#[schemars(required)]` per field looks like
    // the same fix and is not: it also strips the null and inlines the definition.
    let schema = SchemaSettings::draft2020_12()
        .for_serialize()
        .into_generator()
        .into_root_schema_for::<AppliedOperation>();

    let mut out = std::io::stdout().lock();
    serde_json::to_writer_pretty(&mut out, &schema)?;
    out.write_all(b"\n")?;
    Ok(())
}
