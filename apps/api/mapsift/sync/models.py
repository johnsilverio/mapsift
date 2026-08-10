"""The append-only operation log (M15).

What makes it append-only is the grant in the migration beside this file, never a model option
(ADR-0005 section 2, addition of 2026-08-07).
"""

from typing import ClassVar
from uuid import uuid4

from django.db import models

from mapsift.common.binding import TenantOwnedManager


class OperationLogEntry(models.Model):
    """One operation as its client authored it, and the only record a flush produces (M15, M8)."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="operation_log_entries",
        db_index=False,
    )
    operation_id = models.UUIDField()
    client_half = models.JSONField()

    objects = TenantOwnedManager["OperationLogEntry"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["tenant", "operation_id"],
                name="one_entry_per_operation_within_its_tenant",
            )
        ]
