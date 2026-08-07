"""The API surface, and the source of the Python-to-TypeScript contract (PRD M12)."""

from ninja import NinjaAPI
from ninja.security import django_auth

from config import probes
from mapsift.sync import api as sync

api = NinjaAPI(
    title="Mapsift API",
    version="0.1.0",
    description=(
        "The one Mapsift backend: truth, auth, tenant isolation, ordering, and the "
        "authoritative conflict resolution."
    ),
    # On the instance and never on an add_router call (ADR-0010 decision 4).
    auth=django_auth,
)

api.add_router("", probes.router)
api.add_router("", sync.router)
