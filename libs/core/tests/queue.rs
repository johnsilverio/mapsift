//! The operation queue where its decisions are made: what an append stamps and numbers, and what a
//! queue opened from the records the platform handed back offers for flush.
//!
//! Trace: T1.2 (the reopen half; a real store surviving a real restart is MAP-19's), M3 (an
//! identifier is unchanged by a reopen), M4 (the clientID is persisted in the store), M9 (the
//! closed catalog at the append), M10 (the mutation number, from zero and contiguous per flush
//! domain), ADR-0015 decisions 1 to 7, each named on the case that carries it. Every identifier
//! here is injected, as decision 1 requires of the queue's logic, so none of these cases says
//! anything about minting from a real source of randomness.
//!
//! The queue's crossing, the instance that holds it and the minting layer are pinned where they
//! are read: `apps/web/src/app/core`.

use std::collections::BTreeMap;

use mapsift_core::queue::{OperationQueue, QueueRecord, QueueRefusal};
use serde_json::{Value, json};
use uuid::{Uuid, uuid};

const TENANT: Uuid = uuid!("7c0e2b81-9d4f-4a63-b5e8-0c1d2e3f4a5b");
const THE_FIELD_PROJECT: Uuid = uuid!("2b6d4f19-3a8c-4e50-9f27-6d8b1c3a5e70");
const THE_OFFICE_PROJECT: Uuid = uuid!("e3a1c5d7-2b4f-4e68-9a0c-1d3f5b7e9a24");
const THE_RESERVE_LAYER: Uuid = uuid!("5e9a7c30-1f4b-4d82-a63e-8b0c2d4f6a19");
const THE_SPRINGS_LAYER: Uuid = uuid!("b7d2e4f6-8a1c-4b3e-9d5f-0a2c4e6b8d13");
const FEATURE_ONE: Uuid = uuid!("c4a1e7b2-8d36-4f09-95c7-1e3a5b7d9f02");
const FEATURE_TWO: Uuid = uuid!("8d2f6a04-7b19-4c53-ae86-0f5d3b1c9e47");
const FEATURE_THREE: Uuid = uuid!("3f5b7d9e-1a2c-4e4f-8b6d-7c9e0a1b2d35");

/// The clientID minted for the installation every case here opens.
const THE_TABLET: Uuid = uuid!("1a2b3c4d-5e6f-4071-8293-a4b5c6d7e8f9");

// ONE, TWO and THREE sort as ONE, THREE, TWO on purpose, so an order read off the identifiers
// themselves is never the order of the append (M3).
const OPERATION_ONE: Uuid = uuid!("0b3d5f71-2c48-4e69-a15b-7d9e0f2a4c68");
const OPERATION_TWO: Uuid = uuid!("4e8a1c60-7b23-4d95-8f01-6a2c9d3e5b74");
const OPERATION_THREE: Uuid = uuid!("2c9e4b17-5d80-4a36-9e42-7f1b0d8c6a53");
const OPERATION_FOUR: Uuid = uuid!("9f1c0d3a-6b2e-4f57-8c19-2d4a7e5b0c31");
const OPERATION_FIVE: Uuid = uuid!("6a8c0e2f-4b5d-4f71-9c3e-5a7b9d1f3e86");
const OPERATION_SIX: Uuid = uuid!("d5e7f9a1-3b4c-4d6e-8f0a-2b4c6d8e0f13");
const OPERATION_SEVEN: Uuid = uuid!("71a3c5e7-9b0d-4f2a-b4c6-d8e0f2a4b6c8");
const OPERATION_EIGHT: Uuid = uuid!("a2c4e6f8-0b1d-4e3f-9a5b-7c9d1e3f5a7b");
const OPERATION_NINE: Uuid = uuid!("5b7d9f1a-2c3e-4a5b-8d7e-9f1a3b5c7d9e");
const OPERATION_TEN: Uuid = uuid!("e8f0a2b4-c6d8-4e0f-a2b4-c6d8e0f2a4b6");
const OPERATION_ELEVEN: Uuid = uuid!("13579bdf-2468-4ace-9bdf-13579bdf2468");

/// The platform's store as the record contract sees it: a key names one record, and writing a key
/// again replaces what was there.
type Store = BTreeMap<String, String>;

/// What the platform hands the queue for creating a feature: the catalog member with its target
/// and payload, and what only the platform knows (ADR-0015 decision 7).
fn a_feature_created(project: Uuid, layer: Uuid, feature: Uuid) -> String {
    json!({
        "operation_type": "feature.create",
        "target": {
            "kind": "feature",
            "tenant_id": TENANT,
            "project_id": project,
            "layer_id": layer,
            "feature_id": feature
        },
        "payload": {},
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-09-29T10:00:00Z",
        "mediation": null
    })
    .to_string()
}

fn a_geometry_set(project: Uuid, layer: Uuid, feature: Uuid) -> String {
    json!({
        "operation_type": "feature.geometry.set",
        "target": {
            "kind": "property",
            "tenant_id": TENANT,
            "project_id": project,
            "layer_id": layer,
            "feature_id": feature,
            "property": "geometry"
        },
        "payload": {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-47.9, -15.8], [-47.8, -15.8], [-47.8, -15.7], [-47.9, -15.8]]]
            }
        },
        "author_session_material": {"proof": "opaque-to-the-core"},
        "created_at": "2026-09-29T10:00:05Z",
        "mediation": null
    })
    .to_string()
}

/// The operation with only its catalog member's name replaced, every other field as composed.
fn with_operation_type(operation: &str, operation_type: &str) -> String {
    let mut retyped: Value = serde_json::from_str(operation).expect("the fixture is JSON");
    retyped["operation_type"] = json!(operation_type);
    retyped.to_string()
}

fn keys_of(records: &[QueueRecord]) -> Vec<String> {
    records.iter().map(|record| record.key.clone()).collect()
}

fn write(store: &mut Store, records: &[QueueRecord]) {
    for record in records {
        store.insert(record.key.clone(), record.value.clone());
    }
}

/// The platform's whole part in a transition: it writes the records as one unit and, once its
/// store confirms them, says so (ADR-0015 decisions 3 and 4).
fn persist(queue: &mut OperationQueue, store: &mut Store, records: &[QueueRecord]) {
    write(store, records);
    queue.confirm_written(&keys_of(records));
}

/// A new installation's queue, with its installation record already persisted.
fn installed_queue(store: &mut Store) -> OperationQueue {
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, store, &installed);
    queue
}

/// What the platform does with every edit: append it, then persist what the append returned.
fn append_and_persist(
    queue: &mut OperationQueue,
    store: &mut Store,
    operation: &str,
    operation_id: Uuid,
) -> Vec<QueueRecord> {
    let records = queue
        .append(operation, operation_id)
        .expect("a declared catalog member is appended");
    persist(queue, store, &records);
    records
}

fn held(store: &Store) -> Vec<QueueRecord> {
    store
        .iter()
        .map(|(key, value)| QueueRecord {
            key: key.clone(),
            value: value.clone(),
        })
        .collect()
}

fn reopen(store: &Store) -> OperationQueue {
    OperationQueue::open(held(store)).expect("a queue opens from the records it wrote")
}

/// What the queue offers for one project of the tenant, read across every offer naming that
/// domain so a stream offered in pieces is read whole, each operation parsed from its JSON.
fn offered_in(queue: &OperationQueue, project: Uuid) -> Vec<Value> {
    queue
        .offered_for_flush()
        .into_iter()
        .filter(|offer| offer.tenant_id == TENANT && offer.project_id == project)
        .flat_map(|offer| offer.operations)
        .map(|operation| serde_json::from_str(&operation).expect("an offered operation is JSON"))
        .collect()
}

/// What the queue offers for one project of the tenant when that is exactly `N` operations,
/// failing with how many it offered otherwise.
fn the_operations_offered_in<const N: usize>(queue: &OperationQueue, project: Uuid) -> [Value; N] {
    offered_in(queue, project)
        .try_into()
        .unwrap_or_else(|offered: Vec<Value>| {
            panic!(
                "the queue offered {} operations for the project, and the case expects {N}",
                offered.len()
            )
        })
}

/// Each offered operation as its identifier and its mutation number, in the order offered.
fn stream_of(offered: &[Value]) -> Vec<(Value, Value)> {
    offered
        .iter()
        .map(|operation| {
            (
                operation["operation_id"].clone(),
                operation["mutation_number"].clone(),
            )
        })
        .collect()
}

/// The entry an append wrote: the one record no other append in its flush domain writes again,
/// since an entry is keyed by its domain and its mutation number (ADR-0015 decision 2).
fn the_entry_written_by(
    append: &[QueueRecord],
    another_append_in_its_domain: &[QueueRecord],
) -> QueueRecord {
    let written_again = keys_of(another_append_in_its_domain);
    let mut entries = append
        .iter()
        .filter(|record| !written_again.contains(&record.key));
    let entry = entries.next().expect("an append writes its entry");
    assert!(
        entries.next().is_none(),
        "an append writes one entry record (ADR-0015 decision 2)"
    );
    entry.clone()
}

/// A domain's stream record: the one every append in the domain writes again, whatever the
/// installation wrote beside it (ADR-0015 decision 2).
fn the_stream_record_rewritten_by(
    first: &[QueueRecord],
    second: &[QueueRecord],
    installed: &[QueueRecord],
) -> QueueRecord {
    let written_by_first = keys_of(first);
    let written_at_install = keys_of(installed);
    let mut streams = second.iter().filter(|record| {
        written_by_first.contains(&record.key) && !written_at_install.contains(&record.key)
    });
    let stream = streams
        .next()
        .expect("an append rewrites its domain's stream record");
    assert!(
        streams.next().is_none(),
        "a flush domain has one stream record (ADR-0015 decision 2)"
    );
    stream.clone()
}

/// The record as a core newer than this one would have written it: the same value under the
/// next version of the record contract (ADR-0015 decision 5).
fn written_under_the_next_contract_version(record: &QueueRecord) -> String {
    let mut value: Value = serde_json::from_str(&record.value)
        .expect("a record's value is JSON (ADR-0015 decision 6)");
    let version = value["contract_version"].as_u64().expect(
        "a record carries its contract_version, a number, at the top level of its value \
         (ADR-0015 decision 5)",
    );
    value["contract_version"] = json!(version + 1);
    value.to_string()
}

/// The one record a new installation writes, which carries its clientID (ADR-0015 decision 2).
fn the_installation_record(installed: &[QueueRecord]) -> QueueRecord {
    match installed {
        [installation] => installation.clone(),
        _ => panic!(
            "one installation record carries the clientID (ADR-0015 decision 2), and installing \
             returned {}",
            installed.len()
        ),
    }
}

/// The records a store holds once the keys a transition wrote are gone from it.
fn held_without(store: &Store, removed: &[QueueRecord]) -> Vec<QueueRecord> {
    let removed_keys = keys_of(removed);
    held(store)
        .into_iter()
        .filter(|record| !removed_keys.contains(&record.key))
        .collect()
}

/// M10 and ADR-0015 decision 2: a stream is numbered from zero and contiguously, in the order of
/// the append and never an order read off the identifiers (M3).
#[test]
fn a_flush_domain_numbers_its_operations_from_zero_in_the_order_they_were_appended() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
            (json!(OPERATION_THREE), json!(2)),
        ]
    );
}

/// M10 and ADR-0015 decision 2: no stream spans two flush domains, so each project's starts at
/// zero whatever the other one holds.
#[test]
fn each_project_numbers_its_own_stream_from_zero() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_OFFICE_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_THREE), json!(1)),
        ]
    );
    assert_eq!(
        stream_of(&offered_in(&queue, THE_OFFICE_PROJECT)),
        [(json!(OPERATION_TWO), json!(0))]
    );
}

/// M10: the flush domain is one tenant and one project, nothing finer, so the layers of a project
/// share its stream.
#[test]
fn operations_on_two_layers_of_one_project_share_the_projects_stream() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_SPRINGS_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
        ]
    );
}

/// ADR-0015 decision 7 and M3: the operation identifier is the one minted for its append.
#[test]
fn an_operation_is_stamped_with_the_identifier_minted_for_its_append() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    let [offered] = the_operations_offered_in(&queue, THE_FIELD_PROJECT);
    assert_eq!(offered["operation_id"], json!(OPERATION_ONE));
}

/// ADR-0015 decision 7 and M4: every operation carries the clientID of the installation.
#[test]
fn an_operation_is_stamped_with_its_installations_client_id() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    let [offered] = the_operations_offered_in(&queue, THE_FIELD_PROJECT);
    assert_eq!(offered["client_id"], json!(THE_TABLET));
}

/// M4: the clientID is persisted in the local store and stable across restarts.
#[test]
fn a_reopened_queue_stamps_its_next_operation_with_the_same_client_id() {
    let mut store = Store::new();
    installed_queue(&mut store);
    let mut reopened = reopen(&store);

    append_and_persist(
        &mut reopened,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    let [offered] = the_operations_offered_in(&reopened, THE_FIELD_PROJECT);
    assert_eq!(offered["client_id"], json!(THE_TABLET));
}

/// M10 Shape, settled 2026-09-29, and ADR-0015 decision 7: every catalog member as it stands is
/// at operation-schema version 1.
#[test]
fn every_catalog_member_is_stamped_with_operation_schema_version_one() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_geometry_set(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_TWO,
    );

    let [created, geometry_set] = the_operations_offered_in(&queue, THE_FIELD_PROJECT);
    assert_eq!(created["operation_schema_version"], json!(1));
    assert_eq!(geometry_set["operation_schema_version"], json!(1));
}

/// M10 Shape, settled 2026-09-29, and ADR-0015 decision 7: a runtime that carries no conflict rule
/// stamps version 0, which the first rule either runtime carries can never share (T4.3).
#[test]
fn an_operation_is_stamped_with_conflict_rule_version_zero_while_this_runtime_carries_no_rule() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    let [offered] = the_operations_offered_in(&queue, THE_FIELD_PROJECT);
    assert_eq!(offered["conflict_rule_version"], json!(0));
}

/// ADR-0015 decision 7: what the platform supplied reaches the flush as given, the claimed
/// creation time among it (T5.3), since the queue stamps only what the core owns.
#[test]
fn what_the_platform_authored_is_carried_as_given() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let authored = json!({
        "operation_type": "feature.geometry.set",
        "target": {
            "kind": "property",
            "tenant_id": TENANT,
            "project_id": THE_FIELD_PROJECT,
            "layer_id": THE_RESERVE_LAYER,
            "feature_id": FEATURE_ONE,
            "property": "geometry"
        },
        "payload": {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-47.882933418, -15.793889112],
                    [-47.882102337, -15.793889112],
                    [-47.882102337, -15.793055201],
                    [-47.882933418, -15.793889112]
                ]]
            }
        },
        "author_session_material": {"proof": "eyJhbGciOiJFZERTQSJ9", "scopes": ["write"]},
        "created_at": "2026-09-28T23:59:58Z",
        "mediation": {"agent": "mapsift-agent"}
    });

    append_and_persist(&mut queue, &mut store, &authored.to_string(), OPERATION_ONE);

    let [offered] = the_operations_offered_in(&queue, THE_FIELD_PROJECT);
    assert_eq!(offered["operation_type"], authored["operation_type"]);
    assert_eq!(offered["target"], authored["target"]);
    assert_eq!(offered["payload"], authored["payload"]);
    assert_eq!(
        offered["author_session_material"],
        authored["author_session_material"]
    );
    assert_eq!(offered["created_at"], authored["created_at"]);
    assert_eq!(offered["mediation"], authored["mediation"]);
}

/// ADR-0015 decision 4: an operation is offered only once its own records are confirmed written,
/// so a number whose local write failed is never one the server has already decided.
#[test]
fn an_operation_whose_records_are_not_yet_confirmed_is_not_offered_for_flush() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    queue
        .append(
            &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
            OPERATION_TWO,
        )
        .expect("a declared catalog member is appended");

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [(json!(OPERATION_ONE), json!(0))]
    );
}

/// T1.2, M3 and ADR-0015 decision 4: the queue opened from its records is the same queue, every
/// operation under the identifier and number it was appended with, and what the platform read
/// back is confirmed by that fact.
#[test]
fn a_queue_reopened_from_its_records_offers_the_same_operations_under_the_same_identifiers() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_geometry_set(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_TWO,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_OFFICE_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_THREE,
    );
    let offered_in_the_field_project_before =
        the_operations_offered_in::<2>(&queue, THE_FIELD_PROJECT);
    let offered_in_the_office_project_before =
        the_operations_offered_in::<1>(&queue, THE_OFFICE_PROJECT);

    let reopened = reopen(&store);

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
        ]
    );
    assert_eq!(
        the_operations_offered_in::<2>(&reopened, THE_FIELD_PROJECT),
        offered_in_the_field_project_before
    );
    assert_eq!(
        the_operations_offered_in::<1>(&reopened, THE_OFFICE_PROJECT),
        offered_in_the_office_project_before
    );
}

/// T1.2 and ADR-0015 decisions 2 and 3: each append's own records carry its domain's next number,
/// so a queue reopened from them continues every stream where it stopped and never issues a
/// number twice (C12).
#[test]
fn a_queue_reopened_from_its_records_continues_each_stream_where_it_stopped() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_OFFICE_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );
    let mut reopened = reopen(&store);

    append_and_persist(
        &mut reopened,
        &mut store,
        &a_geometry_set(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_FOUR,
    );
    append_and_persist(
        &mut reopened,
        &mut store,
        &a_geometry_set(THE_OFFICE_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_FIVE,
    );

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
            (json!(OPERATION_FOUR), json!(2)),
        ]
    );
    assert_eq!(
        stream_of(&offered_in(&reopened, THE_OFFICE_PROJECT)),
        [
            (json!(OPERATION_THREE), json!(0)),
            (json!(OPERATION_FIVE), json!(1)),
        ]
    );
}

/// ADR-0015 decision 1: opening takes every record the platform holds, in any order.
#[test]
fn a_queue_opens_the_same_from_its_records_handed_back_in_reverse_order() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_OFFICE_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );
    let in_reverse: Vec<QueueRecord> = held(&store).into_iter().rev().collect();

    let reopened =
        OperationQueue::open(in_reverse).expect("the order records come back in is free");

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
        ]
    );
    assert_eq!(
        stream_of(&offered_in(&reopened, THE_OFFICE_PROJECT)),
        [(json!(OPERATION_THREE), json!(0))]
    );
}

/// ADR-0015 decision 2: the next number lives on the stream record, so a stream whose decided
/// entries have left the store numbers on rather than restarting at zero, which the server would
/// deduplicate as operations it already decided (C12). The entries are removed by hand because
/// the transition that removes a decided entry is MAP-77's.
#[test]
fn a_stream_whose_entries_have_left_the_store_numbers_on_from_its_stream_record() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let first = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let second = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    store.remove(&the_entry_written_by(&first, &second).key);
    store.remove(&the_entry_written_by(&second, &first).key);
    let mut reopened = reopen(&store);

    append_and_persist(
        &mut reopened,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [(json!(OPERATION_THREE), json!(2))]
    );
}

/// ADR-0015 decision 5: a record the core cannot read fails the open with a typed refusal and
/// never yields a queue with that entry missing, since closing the app never loses unsynced work
/// (T1.2).
#[test]
fn an_entry_the_core_cannot_read_fails_the_open_rather_than_opening_without_it() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let first = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let second = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    let entry = the_entry_written_by(&first, &second);
    store.insert(entry.key.clone(), "a value no core ever wrote".to_owned());

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord { key: entry.key })
    );
}

/// ADR-0015 decisions 2 and 5: an unreadable stream record fails the open too, rather than
/// restarting its stream from what the entries alone would say.
#[test]
fn a_stream_record_the_core_cannot_read_fails_the_open_rather_than_restarting_the_stream() {
    let mut store = Store::new();
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, &mut store, &installed);
    let first = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let second = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    let stream = the_stream_record_rewritten_by(&first, &second, &installed);
    store.insert(stream.key.clone(), "a value no core ever wrote".to_owned());

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord { key: stream.key })
    );
}

/// ADR-0015 decision 5: every record carries the version of the contract it was written under, and
/// one written under a version this core does not know is refused rather than misread, which is
/// the local form of foundation 9.6.7's temporal skew.
#[test]
fn an_entry_written_under_a_contract_version_this_core_does_not_know_fails_the_open() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let first = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let second = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    let entry = the_entry_written_by(&first, &second);
    store.insert(
        entry.key.clone(),
        written_under_the_next_contract_version(&entry),
    );

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord { key: entry.key })
    );
}

/// ADR-0015 decision 6 and M9: an operation outside the closed catalog is refused at the append.
#[test]
fn an_operation_outside_the_closed_catalog_is_refused_at_the_append() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let typed_at_an_operation_nobody_declared = with_operation_type(
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        "basin.dredge",
    );

    let outcome = queue.append(&typed_at_an_operation_nobody_declared, OPERATION_ONE);

    assert_eq!(outcome.err(), Some(QueueRefusal::UnparsableOperation));
}

/// ADR-0015 decisions 3 and 6: a refused operation is never queued and takes no mutation number,
/// since a number it burned would be a gap its stream could never fill (M10, I2).
#[test]
fn a_refused_operation_takes_no_mutation_number() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let addressed_to_the_field_project = with_operation_type(
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        "basin.dredge",
    );
    let _refusal = queue
        .append(&addressed_to_the_field_project, OPERATION_ONE)
        .err()
        .expect("an operation outside the closed catalog is refused (M9)");

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_TWO,
    );

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [(json!(OPERATION_TWO), json!(0))]
    );
}

/// ADR-0015 decision 4: a confirmation is the platform's word about the records it names, so a
/// later append whose write has not been confirmed stays off the flush.
#[test]
fn a_confirmation_confirms_only_the_operation_whose_records_it_names() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let first = queue
        .append(
            &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
            OPERATION_ONE,
        )
        .expect("a declared catalog member is appended");
    let second = queue
        .append(
            &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
            OPERATION_TWO,
        )
        .expect("a declared catalog member is appended");
    write(&mut store, &first);
    write(&mut store, &second);

    queue.confirm_written(&keys_of(&first));

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [(json!(OPERATION_ONE), json!(0))]
    );
}

/// ADR-0015 decision 4, added 2026-10-14: a stream is offered up to its first unconfirmed
/// operation and never beyond it, even past a platform that confirmed a later write, since a
/// confirmed operation behind an unconfirmed one would reach the server as a gap (M10).
#[test]
fn a_stream_is_offered_up_to_its_first_unconfirmed_operation_and_never_beyond_it() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let _whose_write_failed = queue
        .append(
            &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
            OPERATION_TWO,
        )
        .expect("a declared catalog member is appended");

    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_THREE),
        OPERATION_THREE,
    );

    assert_eq!(
        stream_of(&offered_in(&queue, THE_FIELD_PROJECT)),
        [(json!(OPERATION_ONE), json!(0))]
    );
}

/// ADR-0015 decision 4: a record the platform read back from its store when the queue was opened
/// is confirmed by that fact, with no confirmation of its own.
#[test]
fn an_operation_read_back_on_open_is_offered_without_a_further_confirmation() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let never_confirmed = queue
        .append(
            &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
            OPERATION_ONE,
        )
        .expect("a declared catalog member is appended");
    write(&mut store, &never_confirmed);

    let reopened = reopen(&store);

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [(json!(OPERATION_ONE), json!(0))]
    );
}

/// M10 and ADR-0015 decisions 1 and 2: a stream reopens in mutation-number order from records
/// handed back in the text order of their keys, the order this store keeps. Eleven is the
/// shortest stream holding a two-digit number, an entry is keyed by its number (decision 2), and
/// as text "10" sorts before "2".
#[test]
fn a_reopened_stream_of_eleven_operations_is_offered_in_mutation_number_order() {
    let mut store = Store::new();
    let mut queue = installed_queue(&mut store);
    let a_vertex_moved = a_geometry_set(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE);
    let mut record_the_edit = |operation_id| {
        append_and_persist(&mut queue, &mut store, &a_vertex_moved, operation_id);
    };
    record_the_edit(OPERATION_ONE);
    record_the_edit(OPERATION_TWO);
    record_the_edit(OPERATION_THREE);
    record_the_edit(OPERATION_FOUR);
    record_the_edit(OPERATION_FIVE);
    record_the_edit(OPERATION_SIX);
    record_the_edit(OPERATION_SEVEN);
    record_the_edit(OPERATION_EIGHT);
    record_the_edit(OPERATION_NINE);
    record_the_edit(OPERATION_TEN);
    record_the_edit(OPERATION_ELEVEN);

    let reopened = reopen(&store);

    assert_eq!(
        stream_of(&offered_in(&reopened, THE_FIELD_PROJECT)),
        [
            (json!(OPERATION_ONE), json!(0)),
            (json!(OPERATION_TWO), json!(1)),
            (json!(OPERATION_THREE), json!(2)),
            (json!(OPERATION_FOUR), json!(3)),
            (json!(OPERATION_FIVE), json!(4)),
            (json!(OPERATION_SIX), json!(5)),
            (json!(OPERATION_SEVEN), json!(6)),
            (json!(OPERATION_EIGHT), json!(7)),
            (json!(OPERATION_NINE), json!(8)),
            (json!(OPERATION_TEN), json!(9)),
            (json!(OPERATION_ELEVEN), json!(10)),
        ]
    );
}

/// ADR-0015 decisions 2 and 5: an unreadable installation record fails the open rather than being
/// read as absent, which would give the installation a second clientID (M4).
#[test]
fn an_installation_record_the_core_cannot_read_fails_the_open_rather_than_installing_afresh() {
    let mut store = Store::new();
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, &mut store, &installed);
    let installation = the_installation_record(&installed);
    store.insert(
        installation.key.clone(),
        "a value no core ever wrote".to_owned(),
    );

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord {
            key: installation.key
        })
    );
}

/// ADR-0015 decision 5: the installation record carries its contract version like every other
/// record, and one written under a version this core does not know fails the open.
#[test]
fn an_installation_record_written_under_a_contract_version_this_core_does_not_know_fails_the_open()
{
    let mut store = Store::new();
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, &mut store, &installed);
    let installation = the_installation_record(&installed);
    store.insert(
        installation.key.clone(),
        written_under_the_next_contract_version(&installation),
    );

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord {
            key: installation.key
        })
    );
}

/// ADR-0015 decision 5: a stream record carries its contract version like every other record, and
/// one written under a version this core does not know fails the open.
#[test]
fn a_stream_record_written_under_a_contract_version_this_core_does_not_know_fails_the_open() {
    let mut store = Store::new();
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, &mut store, &installed);
    let first = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );
    let second = append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_TWO),
        OPERATION_TWO,
    );
    let stream = the_stream_record_rewritten_by(&first, &second, &installed);
    store.insert(
        stream.key.clone(),
        written_under_the_next_contract_version(&stream),
    );

    let outcome = OperationQueue::open(held(&store));

    assert_eq!(
        outcome.err(),
        Some(QueueRefusal::UnreadableRecord { key: stream.key })
    );
}

/// ADR-0015 decision 2, added 2026-10-14: records with no installation record among them are
/// refused at the open and never given a new clientID, which would number over another clientID's
/// streams (M4).
#[test]
fn a_store_holding_records_but_no_installation_record_is_refused_at_the_open() {
    let mut store = Store::new();
    let (mut queue, installed) = OperationQueue::install(THE_TABLET);
    persist(&mut queue, &mut store, &installed);
    append_and_persist(
        &mut queue,
        &mut store,
        &a_feature_created(THE_FIELD_PROJECT, THE_RESERVE_LAYER, FEATURE_ONE),
        OPERATION_ONE,
    );

    let outcome = OperationQueue::open(held_without(&store, &installed));

    assert_eq!(outcome.err(), Some(QueueRefusal::NoInstallationRecord));
}
