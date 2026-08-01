# dev-workflow reference

Concrete commands and examples for the contribution workflow. The protocol is in `SKILL.md`; the project
rules are in the root `CLAUDE.md` and `specs/adr/0001-architecture-baseline.md`.

## Commit message examples

- `feat: add layer panel with search and filtering`
- `fix: keep the op queue populated when a flush fails`
- `refactor: extract polygon area math into a pure function`
- `test: cover the auth interceptor token-refresh branch`
- `docs: record the SGL metric frame decision in the log`
- `style: align the map toolbar to the spacing scale`
- `chore: bump the maplibre-gl dependency to the next patch`
- `perf: lazy-load the analysis feature route`

## Pull request flow, step by step

```bash
# Branch from an up-to-date main
git switch main && git pull
git switch -c js/MAP-12-offline-op-queue

# ...work, running /quality-gate before each commit...

# Push and open the PR against main
git push -u origin js/MAP-12-offline-op-queue
gh pr create --base main --fill

# Watch the required checks, then merge once they are green
gh pr checks --watch
gh pr merge --delete-branch   # pick the team's merge strategy (--squash / --merge / --rebase)
```

## Reproducing a failed check locally

Prefer the `justfile` recipes, which run inside the containers ADR-0001 section 3 makes authoritative:

```bash
just lint
just typecheck
just test
just contracts
```

The raw commands those recipes wrap, per language touched:

- Python (`apps/api`): `uv run ruff check apps/api`, `uv run ruff format --check apps/api`,
  `uv run mypy --strict apps/api`, `uv run pytest`.
- Web (`apps/web`, `libs/ui`): `ng lint`, `ng build` (the strict tsc), `ng test --watch=false`. Watch defaults
  to true in a TTY, hence the explicit flag; tests run in Node with jsdom unless `--browsers` opts into a
  real browser.
- Rust (`libs/core`): `cargo clippy -- -D warnings`, `cargo fmt --check`, `cargo test`.
- Contracts: regenerate both directions and confirm `git diff --exit-code` is clean.

## Worktrees

Backlog items run in parallel worktrees. Finishing one goes through the `worktree-commit-merge` skill, which
takes the branch to `main` by pull request, never by a local merge.

```bash
git worktree add ../mapsift-MAP-12 -b js/MAP-12-offline-op-queue
git worktree list
git worktree remove ../mapsift-MAP-12
```
