import type { ClientHalf } from '@mapsift/core';

/**
 * The catalog as `apps/web` reads it: M9's closed set over the core-generated declaration and no
 * other (ADR-0009 sections 3 and 4). Nothing below declares a catalog type of its own; the one
 * type name it needs is indexed out of the generated one, because a second declaration is the
 * defect that rule exists to catch.
 *
 * Every assertion here is a compile-time one; the runtime `expect` calls exist to give each a test
 * to live in. `ng build web` excludes spec files (`tsconfig.app.json`), so `ng test` is the gate
 * that enforces this contract and the build will stay green while it is broken.
 */
const A_WHOLE_RING = {
  type: 'Polygon',
  coordinates: [
    [
      [-47.882933418, -15.793889112],
      [-47.882102337, -15.793889112],
      [-47.882102337, -15.793055201],
      [-47.882933418, -15.793889112],
    ],
  ],
};

const A_SET_GEOMETRY_OPERATION: ClientHalf = {
  operation_id: '4e8a1c60-7b23-4d95-8f01-6a2c9d3e5b74',
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
  payload: { geometry: A_WHOLE_RING },
  author_session_material: { proof: 'opaque-to-the-core' },
  created_at: '2026-08-05T12:00:00Z',
  mediation: null,
};

const A_CREATE_FEATURE_OPERATION: ClientHalf = {
  operation_id: '0b3d5f71-2c48-4e69-a15b-7d9e0f2a4c68',
  client_id: '1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9',
  mutation_number: 6,
  operation_type: 'feature.create',
  operation_schema_version: 3,
  conflict_rule_version: 5,
  target: {
    kind: 'feature',
    tenant_id: '7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b',
    project_id: '2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70',
    layer_id: '5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19',
    feature_id: 'c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02',
  },
  payload: {},
  author_session_material: { proof: 'opaque-to-the-core' },
  created_at: '2026-08-05T11:59:58Z',
  mediation: null,
};

// The `never` branch is the assertion, not the fallback: it stops compiling the moment the catalog
// gains a member, which is what makes adding one a decision rather than a habit (M9). Reaching the
// geometry only inside the narrowed branch is the other half: it stops compiling if the payload
// ever widens back to an opaque value.
function geometryCarriedBy(operation: ClientHalf): unknown {
  switch (operation.operation_type) {
    case 'feature.create':
      return null;
    case 'feature.geometry.set':
      return operation.payload.geometry;
    default: {
      const aMemberNobodyDeclared: never = operation;
      return aMemberNobodyDeclared;
    }
  }
}

describe('the operation catalog as the web client reads it', () => {
  it('narrows a set-geometry operation to the whole ring its typed payload declares', () => {
    expect(geometryCarriedBy(A_SET_GEOMETRY_OPERATION)).toEqual(A_WHOLE_RING);
  });

  it('leaves a create-feature operation with no geometry to narrow to', () => {
    expect(geometryCarriedBy(A_CREATE_FEATURE_OPERATION)).toBeNull();
  });

  it('does not admit an operation type nobody declared', () => {
    // @ts-expect-error the catalog is closed (M9), so a type outside it is not assignable. The
    // directive is the assertion: it fails the build if this line ever compiles.
    const aTypeNobodyDeclared: ClientHalf['operation_type'] = 'basin.dredge';

    expect(aTypeNobodyDeclared).toBe('basin.dredge');
  });

  it('does not admit an operation addressed at a kind its type does not declare', () => {
    // @ts-expect-error M9 as sharpened 2026-08-06: create declares the feature, so a property
    // address is not assignable to this member. Written out rather than spread from the fixture
    // above, because a spread widens `operation_type` back to the union and the directive would
    // then fire on the tag instead of on the target it is here to guard.
    const addressedFinerThanTheCatalogFixes: ClientHalf = {
      operation_id: '2c9e4b17-5d80-4a36-9e42-7f1b0d8c6a53',
      client_id: '1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9',
      mutation_number: 8,
      operation_type: 'feature.create',
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
      payload: {},
      author_session_material: { proof: 'opaque-to-the-core' },
      created_at: '2026-08-05T11:59:59Z',
      mediation: null,
    };

    expect(addressedFinerThanTheCatalogFixes.operation_type).toBe('feature.create');
  });
});
