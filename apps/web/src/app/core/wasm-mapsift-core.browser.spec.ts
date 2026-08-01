import { wasmMapsiftCore } from './wasm-mapsift-core';

/**
 * Proves the WebAssembly core is genuinely loaded and executing, which a green build does not:
 * a build only shows that the types resolved. It needs a real browser, because the module is
 * fetched and jsdom does not implement that.
 */
describe('the client core across the WASM boundary', () => {
  const BRASILIA = [-47.8825, -15.7942] as const;
  const SAO_PAULO = [-46.6333, -23.5505] as const;

  it('measures a distance in metres, matching the value the Rust suite computes', () => {
    const measured = wasmMapsiftCore.measureDistance(BRASILIA, SAO_PAULO);

    expect(measured.unit).toBe('m');
    expect(measured.value).toBeCloseTo(868548, -1);
  });

  it('marks its result as a preview, never as authoritative', () => {
    const measured = wasmMapsiftCore.measureDistance(BRASILIA, SAO_PAULO);

    expect(measured.frame).toBe('geodesic:SIRGAS2000');
    expect(measured.authority).toBe('client-preview');
  });
});
