# syntax=docker/dockerfile:1

# The client side in one file: the Rust core and the Angular web client. They share a file
# because they share a build order that must exist in exactly one place. apps/web resolves
# `@mapsift/core` to libs/core/pkg and `@mapsift/ui` to dist/libs/ui (tsconfig.json paths), so
# the web build cannot start until wasm-pack and ng-packagr have run. Splitting this in two would
# put that ordering in two Dockerfiles and in the justfile, and the copies would drift.


# ---------------------------------------------------------------------------
# The Rust client core toolchain (libs/core). No Rust ever runs on the server (foundation 9.6.6).
# ---------------------------------------------------------------------------
FROM rust:1.95-slim-trixie AS core

# The official Rust image installs the minimal rustup profile, so clippy and rustfmt are absent
# and `cargo clippy` fails with a message about an unknown subcommand rather than about a missing
# component. Both are gates in ADR-0001 section 6.
RUN rustup component add clippy rustfmt \
 && rustup target add wasm32-unknown-unknown

ARG WASM_PACK_VERSION=0.15.0
# wasm-pack publishes a prebuilt binary, and at this release the only linux x86_64 asset is the
# musl one; the gnu URL that the naming convention suggests returns 404.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -fsSL "https://github.com/wasm-bindgen/wasm-pack/releases/download/v${WASM_PACK_VERSION}/wasm-pack-v${WASM_PACK_VERSION}-x86_64-unknown-linux-musl.tar.gz" \
    | tar -xz -C /usr/local/bin --strip-components=1 --wildcards '*/wasm-pack' \
 && rm -rf /var/lib/apt/lists/*

# The crate directory, not the repository root: cargo looks for a Cargo.toml in the working
# directory and there is none at the root of a polyglot monorepo, so every cargo command would
# need a --manifest-path it should not have to carry. Development mounts the whole repository at
# /workspace, so this path is the same one on both sides.
WORKDIR /workspace/libs/core

# CARGO_HOME and the target directory are written by the build, so they belong to the user the
# development container runs as rather than to root. Both are created here while empty, and that
# is the load-bearing part: compose mounts a named volume over each, Docker only seeds a volume
# from the image when the path already exists, and otherwise it creates the mount point owned by
# root, so every write from the non-root user fails. The registry path is the one that catches
# people, because a fresh Rust image has no registry directory until something fetches a crate.
RUN useradd --uid 1000 --create-home app \
 && mkdir -p /workspace/libs/core/target "$CARGO_HOME/registry" \
 && chown -R app:app "$CARGO_HOME" /workspace
USER app


# The core with its source in the image: what CI runs its gates against, and what produces the
# wasm package the web build consumes.
FROM core AS core-build

COPY --chown=app:app libs/core/ ./
# --target web is what apps/web consumes, and the TypeScript definitions wasm-pack generates from
# the Rust types are the core half of the generated-contract rule (ADR-0001 section 5, PRD M12).
RUN wasm-pack build --target web --out-dir pkg


# ---------------------------------------------------------------------------
# The Angular workspace: apps/web and libs/ui
# ---------------------------------------------------------------------------
# Angular 22 requires node ^22.22.3 || ^24.15.0 || >=26, which is why the tag is not "lts".
FROM node:24-slim AS web-deps

WORKDIR /workspace

# The CLI otherwise prompts for usage analytics on its first interactive run and writes the answer
# into angular.json, which is tracked, so a tracking identifier reaches the repository and every
# later run reports from it. It happened once here before this line existed.
ENV NG_CLI_ANALYTICS=false

# npm ci reads only these two, so a source edit never reinstalls the dependency tree.
COPY package.json package-lock.json ./
RUN npm ci

# node:24-slim already ships a `node` user at uid 1000, so there is nothing to create here. The
# Angular cache directory is created for the same reason as the Rust target directory above: a
# named volume over a path the image does not have is a root-owned mount point.
RUN mkdir -p /workspace/.angular \
 && chown -R node:node /workspace
USER node

EXPOSE 4200
CMD ["npx", "ng", "serve", "web", "--host", "0.0.0.0", "--port", "4200"]


# The workspace with its source and both generated inputs in place: what CI lints, builds and
# tests. The build itself is the tsc-strict gate (ADR-0001 section 6, C5).
FROM web-deps AS web

COPY --chown=node:node angular.json tsconfig.json eslint.config.js .prettierrc ./
COPY --chown=node:node libs/ui/ libs/ui/
COPY --chown=node:node apps/web/ apps/web/
COPY --from=core-build --chown=node:node /workspace/libs/core/pkg/ libs/core/pkg/

# The order is the requirement, not a preference: apps/web imports @mapsift/ui by package name
# (PRD U10) and that alias resolves to ng-packagr's output, which does not exist until now.
RUN npx ng build ui && npx ng build web
