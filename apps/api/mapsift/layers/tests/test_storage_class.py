"""The class that decides which path a feature takes, pulled out of the queue it answers for.

Trace: M2, foundation section 3; C1; `specs/testing.md` section 3.
"""

from mapsift.layers.rules import StorageClass, enters_the_operation_queue

QUEUE_PATH_BY_CLASS = {
    StorageClass.ELEMENT: True,
    StorageClass.SERVED: False,
}


def test_a_feature_of_an_element_layer_enters_the_operation_queue() -> None:
    """M2, C1: the element path is the offline-capable surface and the queue is what carries it."""
    assert enters_the_operation_queue(StorageClass.ELEMENT) is True


def test_a_feature_of_a_served_layer_never_enters_the_operation_queue() -> None:
    """M2, foundation section 3: a served layer reaches the client as tiles, so a feature of one
    arriving in the queue is the frontier collapsing."""
    assert enters_the_operation_queue(StorageClass.SERVED) is False


def test_every_storage_class_has_a_decided_path() -> None:
    """M2: the set is closed and each member's path is written out above, so one added later fails
    here rather than passing on whatever the code returns when it falls through."""
    answered = {
        storage_class: enters_the_operation_queue(storage_class) for storage_class in StorageClass
    }

    assert answered == QUEUE_PATH_BY_CLASS
