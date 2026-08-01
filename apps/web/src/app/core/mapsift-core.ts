import { InjectionToken } from '@angular/core';

/** A measurement produced by the client core, with the frame and authority that made it (M5). */
export interface Measurement {
  readonly value: number;
  readonly unit: string;
  readonly frame: string;
  readonly authority: string;
}

/** Longitude precedes latitude, matching the stored axis order (M5). */
export type Position = readonly [longitude: number, latitude: number];

/** What the client core offers the UI. Serializable data only, never a live handle (C11, M11). */
export interface MapsiftCore {
  measureDistance(from: Position, to: Position): Measurement;
}

/**
 * Injected rather than imported, so a component test supplies a fake and never loads
 * WebAssembly. Without this seam every test that touches a consuming component drags the module
 * in, and the module needs a real browser to fetch it.
 */
export const MAPSIFT_CORE = new InjectionToken<MapsiftCore>('MapsiftCore');
