import { geodesicDistance } from '@mapsift/core';

import type { MapsiftCore, Measurement, Position } from './mapsift-core';

/**
 * The only module in the application that touches the WebAssembly core, so a change in how it is
 * loaded lands in one file (`specs/dependencies.md` section 2). Importing it pulls the module in,
 * which needs a real browser; anything that only needs the contract imports `MAPSIFT_CORE`.
 */
export const wasmMapsiftCore: MapsiftCore = {
  measureDistance(from: Position, to: Position): Measurement {
    const measured = geodesicDistance(from[0], from[1], to[0], to[1]);
    try {
      return {
        value: measured.value,
        unit: measured.unit,
        frame: measured.frame,
        authority: measured.authority,
      };
    } finally {
      // A wasm-bindgen object owns memory on the WebAssembly heap that no JavaScript collector
      // reclaims. Dropping the reference without this leaks it on every call.
      measured.free();
    }
  },
};
