import type { AppliedOperation, TargetPath } from '@mapsift/core';

/**
 * The envelope as `apps/web` reads it: M8's third acceptance bullet on the TypeScript side, over
 * the core-generated declaration and no other (ADR-0009 sections 3 and 4). The assertions below
 * are deliberately thin; what this file buys is the compile-time check they drag in.
 *
 * M10's other half, that no code path reads one axis as another, is **not** asserted here and its
 * absence is deliberate. tsify emits each axis as `export type X = number`, a structural alias
 * mutually assignable with the primitive, so the substitution compiles on this runtime; the
 * measurement is `specs/dependencies.md` section 2 and the only mechanism that would close it is
 * a hand-written declaration of a generated type, which ADR-0009 section 4 refuses. A
 * `@ts-expect-error` written here would go unused and fail the build.
 */
const AN_APPLIED_OPERATION: AppliedOperation = {
  client: {
    operation_id: '9f1c0d3a-6b2e-4f57-8c19-2d4a7e5b0c31',
    client_id: '1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9',
    mutation_number: 7,
    operation_type: 'feature.geometry.set',
    operation_schema_version: 3,
    conflict_rule_version: 5,
    target: {
      kind: 'property',
      tenant_id: '7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b',
      project_id: '2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70',
      layer_id: '5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19',
      feature_id: 'c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02',
      property: 'geometry',
    },
    payload: {
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [-47.9, -15.8],
            [-47.8, -15.8],
            [-47.8, -15.7],
            [-47.9, -15.8],
          ],
        ],
      },
    },
    author_session_material: { proof: 'opaque-to-the-core' },
    created_at: '2026-08-05T12:00:00Z',
    mediation: null,
  },
  server: {
    applied_at: '2026-08-05T12:00:03Z',
    feature_version: 11,
    project_version: 41,
    applied_rule_version: 6,
    legal_weight_in_force: true,
    verdict: 'applied',
  },
};

// The `never` branch is the assertion, not the fallback: it stops compiling the moment the union
// gains a variant, and it also stops compiling if the generated type degrades to `any`.
function featureAddressedBy(target: TargetPath): string | null {
  switch (target.kind) {
    case 'tenant':
    case 'project':
    case 'layer':
      return null;
    case 'feature':
    case 'property':
      return target.feature_id;
    default: {
      const outsideTheClosedSet: never = target;
      return outsideTheClosedSet;
    }
  }
}

describe('the operation envelope as the web client reads it', () => {
  it('keeps the client half and the server half separately addressable', () => {
    expect(AN_APPLIED_OPERATION.client.mutation_number).toBe(7);
    expect(AN_APPLIED_OPERATION.server.feature_version).toBe(11);
  });

  it('reads the resync cursor off the server half, beside the per-feature version', () => {
    expect(AN_APPLIED_OPERATION.server.project_version).toBe(41);
  });

  it('narrows a target path on its kind, over the closed set M9 names', () => {
    expect(featureAddressedBy(AN_APPLIED_OPERATION.client.target)).toBe(
      'c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02',
    );
  });
});
