"""The append-only operation log (M15).

What makes it append-only is the grant in the migration beside this file, never a model option
(ADR-0005 section 2, addition of 2026-08-07).
"""

from typing import ClassVar
from uuid import uuid4

from django.db import models

from mapsift.common.binding import TenantOwnedManager
from mapsift.sync.envelope import Verdict


class OperationLogEntry(models.Model):
    """One operation as its client authored it, and the only record a flush produces (M15, M8).

    An operation the flush refused is an entry here too, carrying its verdict and its reason
    (ADR-0014 decision 3). Both columns are storage for contracts declared elsewhere and never a
    second declaration of them (ADR-0004 decision 4): the verdict's set is the envelope's and the
    reason's is `WhyAnOperationWasRefused`.

    An entry holds a reason exactly where its verdict refuses, and the database is what enforces
    that rather than whoever writes the next inserter (ADR-0014 decision 3's argument for the
    sibling column).
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="operation_log_entries",
        db_index=False,
    )
    operation_id = models.UUIDField()
    client_half = models.JSONField()
    project_id = models.UUIDField()
    project_version = models.BigIntegerField()
    verdict = models.CharField(max_length=32)
    refusal_reason = models.CharField(max_length=64, null=True)

    objects = TenantOwnedManager["OperationLogEntry"]()

    class Meta:
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["tenant", "operation_id"],
                name="one_entry_per_operation_within_its_tenant",
            ),
            # Negated rather than the `Verdict.applied` that reads better: the set is closed but
            # grown additively, and naming the positive member would make a third one unstorable
            # until somebody wrote a migration nobody would expect to owe.
            models.CheckConstraint(
                condition=(
                    models.Q(verdict=Verdict.refused, refusal_reason__isnull=False)
                    | (~models.Q(verdict=Verdict.refused) & models.Q(refusal_reason__isnull=True))
                ),
                name="a_reason_exactly_where_the_verdict_refuses",
            ),
        ]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["tenant", "project_id", "project_version"],
                name="log_by_project_version",
            )
        ]


class ProjectVersionCounter(models.Model):
    """The row a flush locks to allocate its range of per-project versions (ADR-0004 decision 2).

    Narrow because the width is the point: an update to a wide row with several indexes stops
    being HOT, and this one is updated once per flush of its project.
    """

    pk = models.CompositePrimaryKey("tenant", "project_id")
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="project_version_counters",
        db_index=False,
    )
    # Not a foreign key, and adding one breaks the flush: the row is created on first use, for a
    # project the tables have never seen (ADR-0004 decision 4, second addition of 2026-08-10).
    project_id = models.UUIDField()
    version = models.BigIntegerField()

    objects = TenantOwnedManager["ProjectVersionCounter"]()


class ClientCursor(models.Model):
    """How far one installation's stream has been decided inside one flush domain (M4).

    Decided rather than applied: the cursor passes an operation the flush refused as well as one
    it applied, which is what keeps a refused operation from stalling the stream (ADR-0014
    decision 5, foundation v0.19).

    The absence of the row is the only representation of an absent cursor, because zero is the
    first mutation number and therefore a legitimate decided value (M4's Shape, M10's Shape).
    """

    pk = models.CompositePrimaryKey("tenant", "client_id", "project_id")
    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.CASCADE,
        related_name="client_cursors",
        db_index=False,
    )
    client_id = models.UUIDField()
    # Not a foreign key, for the reason the counter's project_id is not one above.
    project_id = models.UUIDField()
    last_decided_mutation_number = models.BigIntegerField()

    objects = TenantOwnedManager["ClientCursor"]()
