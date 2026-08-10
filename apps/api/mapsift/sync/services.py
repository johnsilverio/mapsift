"""Writes on the operation log, which is the only place an operation reaches it (M15)."""

from mapsift.sync.envelope import ClientHalf
from mapsift.sync.models import OperationLogEntry
from mapsift.sync.rules import the_address_of


def append_to_the_operation_log(operations: list[ClientHalf]) -> None:
    """Append a batch to the log in one statement, each entry inside the tenant it addresses."""
    OperationLogEntry.objects.bulk_create(
        OperationLogEntry(
            tenant_id=the_address_of(operation).tenant_id,
            operation_id=operation.root.operation_id,
            client_half=operation.model_dump(mode="json"),
        )
        for operation in operations
    )
