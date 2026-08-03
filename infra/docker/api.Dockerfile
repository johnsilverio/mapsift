# syntax=docker/dockerfile:1

# The one Django backend (ADR-0001 section 2). The base is the interpreter that
# apps/api/.python-version pins, so the resolver and the container agree by construction.
FROM python:3.13-slim-trixie AS base

# GeoDjango resolves GEOS, GDAL and PROJ from the system at import time, and the database ENGINE
# is the PostGIS backend from the first line, so these are runtime dependencies rather than build
# ones. The package list is Django 5.2's own for Debian ("Installing Geospatial libraries").
RUN apt-get update \
 && apt-get install -y --no-install-recommends binutils gdal-bin libproj-dev \
 && rm -rf /var/lib/apt/lists/*

# uv is pinned exactly, to the version the survey ratified, because it is still pre-1.0 and a
# minor release can change resolution or the lockfile format (specs/dependencies.md section 1).
# `uv lock --check` was run against apps/api/uv.lock under this version before it was pinned here.
COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /usr/local/bin/

# The environment lives OUTSIDE /app on purpose. Development bind-mounts apps/api over /app, and
# a virtualenv inside that directory would be shadowed by the host's own .venv, which is built
# against the host's libraries and is wrong here in a way nothing reports.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


# The gates of ADR-0001 section 6 run here, so this stage carries the dev group. It is also what
# development runs, which is the parity the ADR is after: CI and the developer use one image.
FROM base AS dev

# Dependencies resolve from the lockfile alone, so editing a source file does not re-resolve them.
COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-install-project --all-groups

COPY apps/api/ ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --all-groups

# uid 1000 is the developer account on this team's machines, so a file the container writes into
# the bind-mounted source belongs to the person who mounted it instead of to root. CI overrides
# the user, because a runner is not uid 1000.
RUN useradd --uid 1000 --create-home app && chown -R app:app /opt/venv /app
USER app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
