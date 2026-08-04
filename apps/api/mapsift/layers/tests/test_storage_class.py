"""The class that decides which path a feature takes, as a decision over plain data.

Trace: M2 (the storage class as the carrier of the elements-and-layers frontier), foundation
section 3; C1.

The decision is pulled out of the effect deliberately (`specs/testing.md` section 3): M2's
acceptance is written in terms of an operation queue that MAP-7 to MAP-14 have not built, and what
this task owns is the rule underneath it. The flush issues consume this function later instead of
re-deriving it.
"""

from mapsift.layers.rules import StorageClass, enters_the_operation_queue

QUEUE_PATH_BY_CLASS = {
    StorageClass.ELEMENT: True,
    StorageClass.SERVED: False,
}


def test_a_feature_of_an_element_layer_enters_the_operation_queue() -> None:
    """M2, C1: the element path is the light, live, offline-capable surface, and the queue is what
    carries it."""
    assert enters_the_operation_queue(StorageClass.ELEMENT) is True


def test_a_feature_of_a_served_layer_never_enters_the_operation_queue() -> None:
    """M2, foundation section 3: a served layer is heavy and server-authoritative and reaches the
    client as tiles, so a feature of one arriving in the queue is the frontier collapsing."""
    assert enters_the_operation_queue(StorageClass.SERVED) is False


def test_every_storage_class_has_a_decided_path() -> None:
    """M2: the set of classes is closed and each member's side of the frontier is written out
    above, so one added to the enum later fails here until somebody decides its path, rather than
    passing on whichever answer the code returns when it falls through."""
    answered = {
        storage_class: enters_the_operation_queue(storage_class) for storage_class in StorageClass
    }

    assert answered == QUEUE_PATH_BY_CLASS
