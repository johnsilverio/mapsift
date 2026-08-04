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
gh pr merge --rebase --delete-branch   # squash only for a branch full of noise commits
```

## Repository protection

The PR flow in SKILL.md section 5 is a rule until a ruleset makes it a wall. This is the configuration, so
applying it is a checklist rather than a design session. **Nothing here is applied yet**; the state at the
time of writing (2026-08-04) was no ruleset and no branch protection, verified with
`gh api repos/johnsilverio/mapsift/rulesets` returning `[]`.

**The ruleset.** `Settings` → `Rules` → `Rulesets` → `New branch ruleset`. Name it `main`, set **Enforcement
status to Active** (a ruleset left disabled is decoration), and target **Include default branch**, so it
follows the default branch rather than a name. Enable:

| Rule | What it buys |
|---|---|
| Restrict deletions | `main` cannot be deleted |
| Block force pushes | the rule `dev-workflow` already states, now enforced |
| Require linear history | blocks merge commits, which is what makes the rebase strategy the only path |
| Require a pull request before merging | closes the "no branch reaches `main` without a PR" rule |
| Require status checks to pass | the CI gates of ADR-0001 section 6 stop being advisory |

Inside the pull-request rule: **Required approvals `0`**, restrict merge types to **rebase and squash**, and
require conversation resolution. Inside the status-check rule, the three checks by their exact job names,
`apps/api`, `libs/core` and `apps/web and libs/ui`, plus **Require branches to be up to date before
merging**.

**The two settings that depart from the obvious one, with the reason, because the obvious one is wrong here.**

- **Required approvals is 0, not 1.** GitHub does not let an author approve their own pull request, so on a
  one-person repository a requirement of 1 locks the only developer out of their own `main`. It becomes 1
  when the second developer arrives, and the change is one field.
- **The bypass list stays empty**, and being the repository owner does **not** grant a bypass by itself.
  That is the point rather than an oversight: a permanent bypass is a permanent hole, while editing the
  ruleset in an emergency takes thirty seconds and leaves a record of having been done.

**Require signed commits is deliberately off.** It obliges every machine that commits to carry a configured
signing key and rejects anything unsigned, which is friction nobody asked for; revisit when the team grows
past the people who set up their own machines.

**Repository settings** (`Settings` → `General` → Pull Requests): turn **off** allow merge commits, keep
rebase and squash, and turn **on** automatically delete head branches, because parallel worktrees leave
branches behind.

**Code security** (`Settings` → `Code security`): Dependabot **alerts** and **security updates** on;
Dependabot **version updates off**, because it would open routine upgrade pull requests across four
ecosystems and fight `specs/dependencies.md`, where a version is a researched decision rather than an
automatic bump. Secret scanning and push protection are on by default on a public repository and are what
would catch a credential before it leaves the machine.

**Actions** (`Settings` → `Actions` → `General`): workflow permissions set to read-only. The CI workflow
already declares `permissions: contents: read`, and the repository default should match it.

**The caveat that outweighs the rest.** On a free plan, rulesets and branch protection are enforced on
**public** repositories only. This repository is public today, so all of the above is free. The canon says
the product stays private until it matures, and **the day this repository is made private on a free plan the
protection stops being enforced** while still being visible in the settings, which is the worst way for a
guarantee to disappear. A paid individual plan covers private repositories.

Verify what is actually in force rather than what was clicked:

```bash
gh api repos/johnsilverio/mapsift/rulesets --jq '.[] | {name, enforcement}'
gh api repos/johnsilverio/mapsift/rules/branches/main --jq '[.[].type]'
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
