# Mapsift top-level orchestration across the four ecosystems (ADR-0001 section 1).
#
# The container is the source of truth for RUNNING, in development as well as in deployment; the
# host toolchain exists for AUTHORING, which is the editor, the language servers and the
# formatters (ADR-0001 section 3). So every recipe here runs inside a container, and a green
# `just check` means the same image CI uses agreed.
#
# `--env-file` is passed explicitly because compose looks for `.env` relative to the working
# directory, and every recipe here runs from the repository root while the file lives in infra/.

set shell := ["bash", "-euo", "pipefail", "-c"]

compose := "docker compose -f infra/compose.yaml --env-file infra/.env"

# Every one-shot run carries CI=1, and it is load-bearing rather than cosmetic. The Angular
# persistent cache is an LMDB store whose readers coordinate through a process-shared mutex in
# shared memory, and two containers do not share an IPC namespace, so a gate run against the same
# cache directory while `just dev` holds it crashes on a null read transaction, every time.
# Angular reads CI to disable that cache, which is what makes a gate safe to run beside the dev
# server. Measured on this workspace: the cache saves about two seconds, so isolating it in its
# own volume would buy nothing for the complexity. Forcing the SQLite store instead is not the
# fix; it trades the crash for a cache that returns malformed load results.
run := compose + " run --rm --no-deps -e CI=1"

# Show the recipes.
default:
    @just --list --unsorted

# Create the local environment files from their templates. Safe to re-run; it never overwrites.
setup:
    @test -f infra/.env || (cp infra/.env.example infra/.env && echo "created infra/.env")
    @test -f apps/api/.env || (cp apps/api/.env.example apps/api/.env && echo "created apps/api/.env, fill in SECRET_KEY")
    @echo "ready. next: just dev"

# Build the images. A lockfile change is what makes this necessary.
build *ARGS:
    {{compose}} build {{ARGS}}

# The two generated inputs come first, because apps/web cannot compile without them.

# Bring the whole system up in the background: the database, the API and the web client.
dev: core-build ui-build
    {{compose}} up -d
    @echo "web http://localhost:${WEB_PORT:-4200}   api http://localhost:${API_PORT:-8000}"

up:
    {{compose}} up -d

down:
    {{compose}} down

# Stop everything and drop the volumes, which includes the database. Destructive on purpose.
reset:
    {{compose}} down --volumes

# Only node_modules: a named volume is seeded from the image once and then never refreshed, which
# is what makes it stale after a rebuild. Cargo needs no equivalent, because it resolves against
# Cargo.lock on every invocation rather than trusting what is already in its registry.

# Drop node_modules after a package-lock change, so the volume stops serving the old resolution.
reset-deps:
    {{compose}} down
    docker volume rm -f mapsift_web-node-modules

logs *ARGS:
    {{compose}} logs -f {{ARGS}}

ps:
    {{compose}} ps

# ---------------------------------------------------------------------------
# Generated inputs. apps/web resolves @mapsift/core to libs/core/pkg and @mapsift/ui to
# dist/libs/ui (tsconfig.json paths), so neither is optional before a web build or a web test.
# ---------------------------------------------------------------------------

# Compile the Rust core to WebAssembly, with the TypeScript definitions generated from its types.
core-build:
    {{run}} core wasm-pack build --target web --out-dir pkg

# Package the component library to dist/libs/ui, which is what @mapsift/ui resolves to.
ui-build:
    {{run}} web npx ng build ui

# ---------------------------------------------------------------------------
# The gates of ADR-0001 section 6. `just check` is the whole set; the rest are the pieces.
# ---------------------------------------------------------------------------

check: lint typecheck test contracts

lint:
    {{run}} api ruff check .
    {{run}} api ruff format --check .
    {{run}} core cargo clippy --locked --all-targets -- -D warnings
    {{run}} core cargo fmt --check
    {{run}} web npx ng lint

# `ng build` is the strict tsc pass, which is why the type check and the build are one command on
# the TypeScript side, and why `ng lint` is still not optional (ADR-0001 section 6).

# Type check every ecosystem.
typecheck: core-build ui-build
    {{run}} api mypy --strict .
    {{run}} core cargo check --locked --all-targets
    {{run}} web npx ng build web

test: core-build ui-build
    {{run}} api pytest
    {{run}} core cargo test --locked
    {{run}} web npx ng test --watch=false

# Two directions (ADR-0001 section 5, PRD M12), and only one of them has an artifact today.

# Regenerate the cross-language contracts and fail on any drift.
contracts: core-build
    @test -s libs/core/pkg/mapsift_core.d.ts
    @echo "rust to typescript: regenerated above by wasm-pack, with the definitions emitted from the Rust types"
    @echo "  built reproducibly and untracked, so no committed copy exists to drift from it"
    @echo "openapi to typescript: no generated artifact yet, apps/api has a schema and no consumer"
    @echo "a scoped 'git diff --exit-code' over the generated paths lands here the day one is committed"

fmt:
    {{run}} api ruff format .
    {{run}} core cargo fmt

# ---------------------------------------------------------------------------
# The backend, day to day
# ---------------------------------------------------------------------------

# Run a Django management command against the running database: `just manage createsuperuser`.
manage +ARGS:
    {{compose}} run --rm api python manage.py {{ARGS}}

migrate:
    @just manage migrate

# A psql session inside the database container.
psql:
    {{compose}} exec db psql -U "${POSTGRES_USER:-mapsift}" -d "${POSTGRES_DB:-mapsift}"
