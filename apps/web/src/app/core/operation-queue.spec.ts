import type * as MapsiftCore from '@mapsift/core';
import type {
  AuthoredOperation,
  ClientHalf,
  ConfirmOutcome,
  FlushOffer,
  MintOutcome,
  OfferOutcome,
} from '@mapsift/core';

/**
 * The queue's crossing as `apps/web` reads it, over the core-generated declaration and no other
 * (ADR-0009 sections 3 and 4, ADR-0015 decisions 6 and 7, M11 and M12). Every assertion here is
 * a compile-time one, so `ng test` is the gate that enforces it; what the same crossing does at
 * run time is `operation-queue-boundary.spec.ts`.
 */

type DataVerdict<T> = T extends string | number | boolean | null
  ? true
  : T extends readonly (infer Element)[]
    ? DataVerdict<Element>
    : T extends (...parameters: never[]) => unknown
      ? false
      : T extends object
        ? { [Key in keyof T]-?: DataVerdict<T[Key]> }[keyof T]
        : false;

/** True when every value reachable in `T` is a string, a number, a boolean or null. */
type CarriesOnlyData<T> = [DataVerdict<T>] extends [true] ? true : false;

type CrossingOf<Exported extends (...parameters: never[]) => unknown> = [
  takes: CarriesOnlyData<Parameters<Exported>>,
  returns: CarriesOnlyData<ReturnType<Exported>>,
];

type RefusalReasonOf<Outcome> =
  Extract<Outcome, { outcome: 'refused' }> extends { refusal: { reason: infer Reason } }
    ? Reason
    : never;

type SuppliedByThePlatform =
  'operation_type' | 'target' | 'payload' | 'author_session_material' | 'created_at' | 'mediation';

type StampedByTheQueue =
  | 'operation_id'
  | 'client_id'
  | 'mutation_number'
  | 'operation_schema_version'
  | 'conflict_rule_version';

describe('the operation queue as the web client reads it', () => {
  it('crosses nothing but data in either direction of the exports this task publishes (M11, M12)', () => {
    expectTypeOf<CarriesOnlyData<{ free(): void }>>().toEqualTypeOf<false>();
    expectTypeOf<CarriesOnlyData<{ geometry: unknown }>>().toEqualTypeOf<false>();

    expectTypeOf<{
      openQueue: CrossingOf<typeof MapsiftCore.openQueue>;
      appendOperation: CrossingOf<typeof MapsiftCore.appendOperation>;
      confirmWritten: CrossingOf<typeof MapsiftCore.confirmWritten>;
      offeredForFlush: CrossingOf<typeof MapsiftCore.offeredForFlush>;
      mintIdentifier: CrossingOf<typeof MapsiftCore.mintIdentifier>;
    }>().toEqualTypeOf<{
      openQueue: [true, true];
      appendOperation: [true, true];
      confirmWritten: [true, true];
      offeredForFlush: [true, true];
      mintIdentifier: [true, true];
    }>();
  });

  it('crosses an operation as its JSON, into the queue and out of it (ADR-0015 decision 6)', () => {
    expectTypeOf<Parameters<typeof MapsiftCore.appendOperation>>().toEqualTypeOf<[string]>();
    expectTypeOf<FlushOffer['operations']>().toEqualTypeOf<string[]>();
  });

  it('partitions the client half between what the platform authors and what the queue stamps (ADR-0015 decision 7, M8)', () => {
    expectTypeOf<keyof AuthoredOperation>().toEqualTypeOf<SuppliedByThePlatform>();
    expectTypeOf<keyof ClientHalf>().toEqualTypeOf<SuppliedByThePlatform | StampedByTheQueue>();
    expectTypeOf<Pick<AuthoredOperation, SuppliedByThePlatform>>().toEqualTypeOf<
      Pick<ClientHalf, SuppliedByThePlatform>
    >();
  });

  it('admits refused randomness as the only refusal a mint can answer (ADR-0015 decision 7)', () => {
    expectTypeOf<RefusalReasonOf<MintOutcome>>().toEqualTypeOf<'randomness_unavailable'>();
  });

  it('admits an instance holding no queue as the only refusal of a confirmation or a flush request (ADR-0015 decision 1)', () => {
    expectTypeOf<RefusalReasonOf<ConfirmOutcome>>().toEqualTypeOf<'no_queue_open'>();
    expectTypeOf<RefusalReasonOf<OfferOutcome>>().toEqualTypeOf<'no_queue_open'>();
  });
});
