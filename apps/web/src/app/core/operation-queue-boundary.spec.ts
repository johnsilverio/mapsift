import type * as MapsiftCore from '@mapsift/core';
import type {
  AppendOutcome,
  AuthoredOperation,
  ClientHalf,
  ConfirmOutcome,
  FlushOffer,
  MintOutcome,
  OfferOutcome,
  OpenOutcome,
  QueueRecord,
} from '@mapsift/core';

import wasmBytes from '../../../../../libs/core/pkg/mapsift_core_bg.wasm' with { loader: 'binary' };

/**
 * The operation queue across the WASM boundary, executed against the module `libs/core` builds:
 * the instance that holds the queue and the refusals it answers as values (ADR-0015 decisions 1,
 * 2 and 5 to 7), the reopen half of T1.2 and M3 from a restarted core, M4's client half, and the
 * client half of the collision clause of T1.3, M3 and C3, minted from the real source of
 * randomness. The queue's decisions themselves are pinned in `libs/core/tests/queue.rs`.
 */

type Core = typeof MapsiftCore;

/** The platform's store as the record contract sees it: writing a key again replaces it. */
type Store = Map<string, string>;

const TENANT = '7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b';
const THE_FIELD_PROJECT = '2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70';
const THE_RESERVE_LAYER = '5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19';
const FEATURE_ONE = 'c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02';
const FEATURE_TWO = '8d2f6a04-7b19-4c53-ae86-0f5d3b1c9e47';
const FEATURE_THREE = '3f5b7d9e-1a2c-4e4f-8b6d-7c9e0a1b2d35';

/** A version 4 identifier in its canonical textual form (M3, ADR-0006 decision 1, RFC 9562). */
const A_RANDOM_IDENTIFIER = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

/** What the platform composes when a feature is created in the field project (ADR-0015 decision 7). */
function aFeatureCreated(featureId: string): AuthoredOperation {
  return {
    operation_type: 'feature.create',
    target: {
      kind: 'feature',
      tenant_id: TENANT,
      project_id: THE_FIELD_PROJECT,
      layer_id: THE_RESERVE_LAYER,
      feature_id: featureId,
    },
    payload: {},
    author_session_material: { proof: 'opaque-to-the-core' },
    created_at: '2026-10-14T10:00:00Z',
    mediation: null,
  };
}

/** A core instantiated afresh from its bytes, as starting the application gives one. */
async function aFreshCore(): Promise<Core> {
  vi.resetModules();
  const core = await import('@mapsift/core');
  core.initSync({ module: wasmBytes });
  return core;
}

function refuseRandomness(): void {
  vi.spyOn(globalThis.crypto, 'getRandomValues').mockImplementation(() => {
    throw new DOMException('The operation is not supported.', 'NotSupportedError');
  });
}

function opened(outcome: OpenOutcome): QueueRecord[] {
  if (outcome.outcome === 'refused') {
    throw new Error(
      `the queue was expected to open, and refused: ${JSON.stringify(outcome.refusal)}`,
    );
  }
  return outcome.records;
}

function appended(outcome: AppendOutcome): QueueRecord[] {
  if (outcome.outcome === 'refused') {
    throw new Error(
      `the operation was expected to append, and refused: ${JSON.stringify(outcome.refusal)}`,
    );
  }
  return outcome.records;
}

function refusedToAppend(outcome: AppendOutcome): void {
  if (outcome.outcome === 'appended') {
    throw new Error(
      `the operation was expected to be refused, and appended ${outcome.records.length} records`,
    );
  }
}

function confirmed(outcome: ConfirmOutcome): void {
  if (outcome.outcome === 'refused') {
    throw new Error(`the write was expected to confirm, and refused: ${outcome.refusal.reason}`);
  }
}

function offered(outcome: OfferOutcome): FlushOffer[] {
  if (outcome.outcome === 'refused') {
    throw new Error(`the queue was expected to offer, and refused: ${outcome.refusal.reason}`);
  }
  return outcome.offers;
}

function minted(outcome: MintOutcome): string {
  if (outcome.outcome === 'refused') {
    throw new Error(`an identifier was expected, and the mint refused: ${outcome.refusal.reason}`);
  }
  return outcome.identifier;
}

/** The one record a new installation writes, which carries its clientID (ADR-0015 decision 2). */
function theInstallationRecord(records: readonly QueueRecord[]): QueueRecord {
  const [installation, ...others] = records;
  if (installation === undefined || others.length > 0) {
    throw new Error(`one installation record was expected, and opening returned ${records.length}`);
  }
  return installation;
}

function held(store: Store): QueueRecord[] {
  return [...store].map(([key, value]) => ({ key, value }));
}

/**
 * The platform's whole part in a transition: it writes the unit the core returned and, once its
 * store has, says so (ADR-0015 decisions 3 and 4).
 */
function persist(core: Core, store: Store, records: readonly QueueRecord[]): void {
  records.forEach(({ key, value }) => store.set(key, value));
  confirmed(core.confirmWritten(records.map(({ key }) => key)));
}

function openFrom(core: Core, store: Store): void {
  persist(core, store, opened(core.openQueue(held(store))));
}

function recordTheEdit(core: Core, store: Store, operation: AuthoredOperation): void {
  persist(core, store, appended(core.appendOperation(JSON.stringify(operation))));
}

/**
 * An edit the core appended and the store failed to write, so the platform confirms nothing and
 * writes nothing after it (ADR-0015 decision 4).
 */
function appendWithAFailedWrite(core: Core, operation: AuthoredOperation): void {
  appended(core.appendOperation(JSON.stringify(operation)));
}

/** What the core offers for the field project, each operation parsed from its JSON. */
function offeredInTheFieldProject(core: Core): ClientHalf[] {
  return offered(core.offeredForFlush())
    .filter(({ tenant_id, project_id }) => tenant_id === TENANT && project_id === THE_FIELD_PROJECT)
    .flatMap(({ operations }) =>
      operations.map((operation) => JSON.parse(operation) as ClientHalf),
    );
}

function theOperationOffered(core: Core): ClientHalf {
  const offeredOperations = offeredInTheFieldProject(core);
  const [operation] = offeredOperations;
  if (operation === undefined || offeredOperations.length > 1) {
    throw new Error(
      `one operation was expected on offer, and ${offeredOperations.length} were offered`,
    );
  }
  return operation;
}

/** Each offered operation as the feature it addresses and its mutation number, in order. */
function featuresAndNumbersOffered(core: Core): [string, number][] {
  return offeredInTheFieldProject(core).map(({ target, mutation_number }) => [
    target.feature_id,
    mutation_number,
  ]);
}

/** An installation of its own, on a core of its own, that recorded one edit. */
async function anInstallationThatRecorded(operation: AuthoredOperation): Promise<ClientHalf> {
  const core = await aFreshCore();
  const store: Store = new Map();
  openFrom(core, store);
  recordTheEdit(core, store, operation);
  return theOperationOffered(core);
}

describe('the operation queue across the WASM boundary', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('opens a store holding no record as a new installation, with its installation record to write (M4, ADR-0015 decision 2)', async () => {
    const core = await aFreshCore();

    const outcome = core.openQueue([]);

    expect(outcome).toStrictEqual({
      outcome: 'opened',
      records: [{ key: expect.any(String), value: expect.any(String) }],
    });
  });

  it('offers an operation composed from the generated types as the JSON of its stamped client half (ADR-0015 decisions 6 and 7, M8)', async () => {
    const core = await aFreshCore();
    const store: Store = new Map();
    openFrom(core, store);
    const authored = aFeatureCreated(FEATURE_ONE);

    recordTheEdit(core, store, authored);

    expect(offeredInTheFieldProject(core)).toStrictEqual([
      {
        ...authored,
        operation_id: expect.stringMatching(A_RANDOM_IDENTIFIER),
        client_id: expect.stringMatching(A_RANDOM_IDENTIFIER),
        mutation_number: 0,
        operation_schema_version: 1,
        conflict_rule_version: 0,
      },
    ]);
  });

  it('offers, from a restarted core opened on its records, what the core before the restart offered (T1.2, M3, M4)', async () => {
    const before = await aFreshCore();
    const store: Store = new Map();
    openFrom(before, store);
    recordTheEdit(before, store, aFeatureCreated(FEATURE_ONE));
    recordTheEdit(before, store, aFeatureCreated(FEATURE_TWO));
    const [first, second] = offeredInTheFieldProject(before);
    const restarted = await aFreshCore();

    openFrom(restarted, store);

    expect(offeredInTheFieldProject(restarted)).toStrictEqual([first, second]);
  });

  it('replaces the queue it held when reopened after a failed write, numbering on from what the store held (ADR-0015 decisions 1 and 4)', async () => {
    const core = await aFreshCore();
    const store: Store = new Map();
    openFrom(core, store);
    recordTheEdit(core, store, aFeatureCreated(FEATURE_ONE));
    appendWithAFailedWrite(core, aFeatureCreated(FEATURE_TWO));
    openFrom(core, store);

    recordTheEdit(core, store, aFeatureCreated(FEATURE_THREE));

    expect(featuresAndNumbersOffered(core)).toStrictEqual([
      [FEATURE_ONE, 0],
      [FEATURE_THREE, 1],
    ]);
  });

  it('starts a new installation at the first mutation number when an empty store is opened in place of its queue (M4, ADR-0015 decision 1)', async () => {
    const core = await aFreshCore();
    const firstStore: Store = new Map();
    openFrom(core, firstStore);
    recordTheEdit(core, firstStore, aFeatureCreated(FEATURE_ONE));
    const beforeTheReinstall = theOperationOffered(core);
    const reinstalledStore: Store = new Map();
    openFrom(core, reinstalledStore);

    recordTheEdit(core, reinstalledStore, aFeatureCreated(FEATURE_TWO));

    const afterTheReinstall = theOperationOffered(core);
    expect(afterTheReinstall.mutation_number).toBe(0);
    expect(afterTheReinstall.client_id).not.toBe(beforeTheReinstall.client_id);
  });

  it('refuses records holding no installation record rather than giving them a new clientID (ADR-0015 decision 2)', async () => {
    const before = await aFreshCore();
    const store: Store = new Map();
    const installation = theInstallationRecord(opened(before.openQueue([])));
    persist(before, store, [installation]);
    recordTheEdit(before, store, aFeatureCreated(FEATURE_ONE));
    store.delete(installation.key);
    const restarted = await aFreshCore();

    const outcome = restarted.openQueue(held(store));

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'no_installation_record' },
    });
  });

  it('refuses an installation record it cannot read rather than opening a new installation (ADR-0015 decisions 2 and 5)', async () => {
    const before = await aFreshCore();
    const store: Store = new Map();
    const installation = theInstallationRecord(opened(before.openQueue([])));
    persist(before, store, [installation]);
    store.set(installation.key, 'a value no core ever wrote');
    const restarted = await aFreshCore();

    const outcome = restarted.openQueue(held(store));

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'unreadable_record', key: installation.key },
    });
  });

  it('refuses an operation outside the closed catalog as a value (M9, ADR-0015 decision 6)', async () => {
    const core = await aFreshCore();
    openFrom(core, new Map());
    const typedAtAnOperationNobodyDeclared = {
      ...aFeatureCreated(FEATURE_ONE),
      operation_type: 'basin.dredge',
    };

    const outcome = core.appendOperation(JSON.stringify(typedAtAnOperationNobodyDeclared));

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'unparsable_operation' },
    });
  });

  it('refuses an append made before any queue is open, as a value (ADR-0015 decision 1)', async () => {
    const core = await aFreshCore();

    const outcome = core.appendOperation(JSON.stringify(aFeatureCreated(FEATURE_ONE)));

    expect(outcome).toStrictEqual({ outcome: 'refused', refusal: { reason: 'no_queue_open' } });
  });

  it('refuses a confirmation made before any queue is open, as a value (ADR-0015 decision 1)', async () => {
    const core = await aFreshCore();

    const outcome = core.confirmWritten(['a key no queue returned']);

    expect(outcome).toStrictEqual({ outcome: 'refused', refusal: { reason: 'no_queue_open' } });
  });

  it('refuses a request for what to flush made before any queue is open, as a value (ADR-0015 decision 1)', async () => {
    const core = await aFreshCore();

    const outcome = core.offeredForFlush();

    expect(outcome).toStrictEqual({ outcome: 'refused', refusal: { reason: 'no_queue_open' } });
  });

  it('refuses to open a store holding no record while randomness is refused, rather than minting a clientID without it (ADR-0015 decision 7)', async () => {
    const core = await aFreshCore();
    refuseRandomness();

    const outcome = core.openQueue([]);

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'randomness_unavailable' },
    });
  });

  it('refuses an append while randomness is refused, as a value (ADR-0015 decision 7)', async () => {
    const core = await aFreshCore();
    openFrom(core, new Map());
    refuseRandomness();

    const outcome = core.appendOperation(JSON.stringify(aFeatureCreated(FEATURE_ONE)));

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'randomness_unavailable' },
    });
  });

  it('gives no mutation number to an append refused for randomness (M10, ADR-0015 decision 7)', async () => {
    const core = await aFreshCore();
    const store: Store = new Map();
    openFrom(core, store);
    refuseRandomness();
    refusedToAppend(core.appendOperation(JSON.stringify(aFeatureCreated(FEATURE_ONE))));
    vi.restoreAllMocks();

    recordTheEdit(core, store, aFeatureCreated(FEATURE_TWO));

    expect(featuresAndNumbersOffered(core)).toStrictEqual([[FEATURE_TWO, 0]]);
  });

  it('refuses to mint while randomness is refused, as a value (ADR-0015 decision 7)', async () => {
    const core = await aFreshCore();
    refuseRandomness();

    const outcome = core.mintIdentifier();

    expect(outcome).toStrictEqual({
      outcome: 'refused',
      refusal: { reason: 'randomness_unavailable' },
    });
  });

  it('mints a random identifier in its canonical textual form (M3, ADR-0006 decision 1)', async () => {
    const core = await aFreshCore();

    const identifier = minted(core.mintIdentifier());

    expect(identifier).toMatch(A_RANDOM_IDENTIFIER);
  });

  it('mints different identifiers on two installations (T1.3, M3, C3)', async () => {
    const onTheTablet = await aFreshCore();
    const onTheDesktop = await aFreshCore();

    const mintedOnTheTablet = minted(onTheTablet.mintIdentifier());
    const mintedOnTheDesktop = minted(onTheDesktop.mintIdentifier());

    expect(mintedOnTheTablet).not.toBe(mintedOnTheDesktop);
  });

  it('gives two installations of one user two clientIDs (M4, C3)', async () => {
    const onTheTablet = await anInstallationThatRecorded(aFeatureCreated(FEATURE_ONE));

    const onTheDesktop = await anInstallationThatRecorded(aFeatureCreated(FEATURE_ONE));

    expect(onTheTablet.client_id).not.toBe(onTheDesktop.client_id);
  });

  it('stamps the operations of two installations with different identifiers (M3, C3)', async () => {
    const onTheTablet = await anInstallationThatRecorded(aFeatureCreated(FEATURE_ONE));

    const onTheDesktop = await anInstallationThatRecorded(aFeatureCreated(FEATURE_ONE));

    expect(onTheTablet.operation_id).not.toBe(onTheDesktop.operation_id);
  });
});
