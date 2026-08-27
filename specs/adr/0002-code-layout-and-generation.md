# ADR-0002: Code layout and generation conventions

- **Status:** accepted (2026-07-30)
- **Deciders:** the owner, with the planning window
- **Authority:** derives from `specs/mapsift-foundation.md` v0.11.1 (sections 9.6.5, 14 and the external-dependency rule), `specs/PRD.md` v0.8 (U10, U12), and ADR-0001. Where this ADR and the foundation disagree, the foundation wins.
- **Supersedes:** nothing. **Superseded by:** nothing.

---

## Context

ADR-0001 fixed the repository skeleton, the language roles, containerisation, the gates, and what must not be scaffolded yet. It deliberately said nothing about **code shape inside a stack**: how a component is laid out on disk, when a folder splits, and how a file comes into existence in the first place.

Those conventions were written during the 2026-07-30 `.claude` audit into `.claude/rules/*.md`, which is the right **enforcement** layer and the wrong **authority** layer. A decision that lives only in tooling is outside the authority chain: it is not fanned out when something related changes, it is not reviewable as a decision, and it evaporates the day the tooling is trimmed or regenerated. That is the same class of drift as a derived document deciding what the authority left open, which the governance rule already forbids.

The audit also settled, by research against the current Claude Code documentation rather than from memory, how these files actually load, and the answer changes the plan that preceded it. A `CLAUDE.md` in a subdirectory loads **on demand**, only when a file in that directory is read, and is **not re-injected after compaction**, while the root one is. A file in `.claude/rules/` with a `paths` frontmatter loads when a matching file is read. The consequence is direct: **a per-stack `CLAUDE.md` is strictly weaker than a path-scoped rule for anything that must hold before the first file in that stack is written**, because it may not be loaded yet.

So the layering this ADR fixes is three levels, each with one job:

1. **The ADR (here):** the decision, in the authority chain, edited in place with a dated note when it changes (convention revised 2026-08-05, ADR-0001).
2. **`.claude/rules/*.md`, path-scoped:** the enforceable restatement the agent obeys while editing a matching file. It reflects this ADR and never invents.
3. **The per-stack `CLAUDE.md`:** reserved for the **operational residue** (real commands, real paths, pinned versions) and written only after the scaffold exists.

---

## Decision

### 1. Generation is CLI-first, in every stack

A framework artifact is created by that framework's official generator and then edited. It is not hand-written. Angular uses `ng generate`; Django uses its management commands; Rust uses Cargo's own commands.

**Why this is a rule and not a preference:** a model writes such a file from memory of whatever version it saw during training, so a hand-written file silently reproduces an older shape. The v22 Angular defaults are the proof: `changeDetection` is already `OnPush`, `ChangeDetectionStrategy.Default` is deprecated in favour of `Eager`, guards and interceptors are functional, `standalone` is implied, and the type suffix is gone. Anything written from memory reproduces the shape of several versions ago. This is the foundation's external-dependency rule applied to the framework itself: confirm against the version actually installed, never against memory.

The only exception is a file no generator produces (a pure function module, a fixture), and even there a generator often exists. **Verification is mechanical:** the diff of a newly created artifact matches what the generator prints with `--dry-run` for the same name.

### 2. Angular component file layout

- Keep the CLI default: **one folder per component**, holding the class, the template, the stylesheet, and the spec as separate files. `--inline-template` and `--inline-style` are never passed, and a template is never moved into the decorator afterwards.
- **The single exception** is a shared primitive whose template is at most **5 lines of markup**, **and** has no control flow (`@if`, `@for`, `@switch`), **and** has no bindings beyond content projection and host bindings. The typical case is a `libs/ui` primitive that renders a content slot and nothing else. If any of the three conditions fails, the template goes in its own file whatever its length.
- **One component per folder.** A folder holding two components is two folders.

The three-condition exception is deliberate: "small" is not a rule and never fires. Every part of it is checkable by reading the template.

### 3. Folder organisation

- Organise by **feature, not by type**. In `apps/web/src/app` that is `core/` for singleton infrastructure with no UI, `features/<feature>/` for a lazy route with its own components inside, and `shared/` for application UI built on top of the library. Type-grouped folders (`components/`, `services/`) are not used.
- **A folder that exceeds 8 direct children splits** into subfolders by sub-feature. The number is countable on purpose, for the same reason as the 5-line rule: a threshold that depends on judgement never fires.
- Files are named with hyphens, one concept per file. No `utils.ts`, `helpers.ts`, or `common.ts` grab-bags.

### 4. Naming follows the installed schematic

File and class naming follow what the current schematic emits, which on Angular v22 means no type suffix and no `--type` flag passed to reintroduce one. The component library may keep its own library naming convention where it has one (PRD U10 consumes it by package name, so its internals do not leak).

### 5. Where each level lives, and what may not move

The decision is here. The enforceable restatement is in `.claude/rules/*.md` with a `paths` frontmatter so it loads when a matching file is read. The per-stack `CLAUDE.md` is written after the scaffold and carries only operational residue. **A rules file may not decide anything this ADR does not say**; if a rule needs to change, this ADR is amended first and the rules file follows, never the reverse.

> **Added 2026-08-10 (MAP-40), and the way it was added is the reason it is written here at all.** A fourth
> mechanism now exists: **`.claude/hooks/`, a script that refuses a tool call**. It sits below the three
> levels above and outranks all of them, because they are read while it is executed: a rule asks and a hook
> terminates the call. **It was built before this amendment existed**, which is the inversion the paragraph
> above forbids in the rules file's own case, and the same branch got it right one level up by amending
> ADR-0008 before touching a skill. Recorded rather than quietly corrected, because the standard was known
> and applied unevenly in one sitting.
>
> **Three rules govern it, and the first two are the ones that keep it alive.**
>
> **A hook is proven by a committed suite that trips it, never by prose.** A guard nobody has defeated on
> purpose is a guard nobody has tested, and the first three here shipped with five real defects that twenty
> minutes of adversarial probing found: a guard that blocked the recovery procedure `dev-workflow` section 5
> prescribes, one that blocked every edit to `README.md` over a shields.io escape, an exemption wrong in both
> directions, a branch read from the wrong repository under the worktrees ADR-0008 section 8 mandates, and
> silent non-enforcement when a dependency is missing.
>
> **A guard wider than its rule gets switched off, which is worse than not having it.** So a pattern matches
> at a command position and per token, never anywhere in a string, and the refusal message never offers
> working around it as a routine option.
>
> **A hook states the guarantee it actually gives.** A `PostToolUse` check runs after the write lands and
> hands the violation back to the model; calling that "enforced at write time" is a claim the mechanism does
> not support, and the harm is not the wording. It was used in the same commit to narrow the `code-review`
> Craft axis, which removed the only reader that would have caught what the hook cannot see: a file written
> through `Bash`, and a turn that ends before the model acts on the message.
>
> **The same amendment covers one promotion in `code-review`**, which had the same defect and is corrected
> with it: the three judgement axes moved from "separate contexts where available" to **three parallel
> subagents** with a fixed subagent type and model. That is a mechanism decision and it lives here, with the
> measurements behind it in ADR-0008 section 4.
>
> **Amended 2026-08-19, at the close of MAP-47, on the same mechanism.** Two things moved. **The fixed subagent
> type is `window`**, a delegated worker pinned to Opus and committed at `.claude/agents/window.md` so the type
> the skills name exists on every clone and not only where a developer's user-level agents happen to carry it
> (the owner's decision of 2026-08-18, measured rather than assumed: every subagent request of the MAP-47
> rounds recorded `claude-opus-5`, 1418 of 1418); the `CLAUDE_CODE_SUBAGENT_MODEL=opus` project setting of the
> same date stays as the floor for any dispatch that names another type. **And a review axis reads the tree and
> never writes to it, and never shares the test database**: a mutant runs only through a scratch copy mounted
> read-only over the container path, and `pytest` runs with `--create-db` or against a database of the axis's
> own. Measured at MAP-47's Window B review (`specs/log.md` trap of 2026-08-19): one axis ran mutants by editing
> the working tree and restoring it, another read the mutated file, and three axes sharing `test_mapsift`
> dropped it under each other's runs. The three axis prompts and the `code-review`, `orchestrate` and
> spec-read procedures restate this and decide nothing.

> **Amended 2026-08-25, at the MAP-51 implementation round's research, on three things the 2026-08-19 clause
> got right for a mutant and wrong or silent for everything else.**
>
> **A mutant goes in the artifact that carries the guarantee.** A guarantee expressed in Python source is
> mutated through a scratch copy mounted read-only over its container path, which is unchanged and remains
> the common case. **A guarantee that lives in the database** (a catalogue row, a policy, a grant, an index)
> is mutated by a statement against a database created for that run and dropped after it, and no source
> mutant substitutes: for a case reading `pg_proc`, corrupting the enumeration query turns it red for the
> wrong reason. Where the statement is beyond every role the product runs as, it is issued as the compose
> superuser; `ALTER FUNCTION ... LEAKPROOF` is superuser-only, measured, so an in-suite positive control that
> marks and rolls back is impossible. The run ends by proving the mutant is gone.
>
> **A database of the run's own is reached with the role the suite normally connects as, and that is a
> second thing rather than a restatement.** Overriding `DATABASE_URL` wholesale to repoint the database
> silently repoints the **role** too, and the obvious value to paste is the compose bootstrap superuser,
> which carries `rolsuper` and `rolbypassrls`. Every row-level-security case then passes or fails for the
> wrong reason with the wall off entirely, and the tables still report `relrowsecurity` and
> `relforcerowsecurity` true, because `FORCE` addresses the owner and not a superuser. Change the database
> name and keep the user and password. Measured 2026-08-26, where a window scoped a probe run to one module,
> read a mutant's behaviour out of an environment with no wall, and inferred a mechanism that did not exist;
> `test_the_suite_runs_as_a_role_the_wall_applies_to` fires immediately on such an environment and is the
> first case ADR-0005 section 2 asks for, but a run narrowed to another module never reaches it.

> **How the value is supplied, corrected 2026-08-26 the same day it was first written, because the first
> wording named a mechanism that does not work.** It said to pass `-e DATABASE_URL` with no `=` and supply it
> "from an env file the run already has". **Neither env file this repository ships carries that key**:
> `infra/.env` has none, so Docker drops the unset passthrough and `infra/compose.yaml`'s own `api`
> `environment:` block stands, and the run lands on the shared database the paragraph above exists to keep it
> out of, with no error and no warning. What works is **an env file written for the run**, carrying that
> run's own database name, or the value **exported in the calling shell** and picked up by the bare
> `-e DATABASE_URL` passthrough. Verify what actually reached the container before trusting the run.
>
> **The command is written here rather than described, because this clause has now been imprecise three
> times** (2026-08-26 twice, 2026-08-27 once) and each time an agent followed the prose into something that
> did not work. `--env-file` is a **top-level** compose option: after the subcommand it answers
> `unknown flag: --env-file`, and without `-f` compose finds no configuration file from the repository root.
>
> ```
> export DATABASE_URL=postgresql://mapsift_owner:mapsift_owner@db:5432/<your_db>
> docker compose -f infra/compose.yaml --env-file infra/.env run --rm --no-deps \
>   -e CI=1 -e DATABASE_URL api pytest --reuse-db
> ```
>
> **A command that can be pasted is a fact; a description of one is a memory.** Prefer the first in any clause
> that tells an agent how to run something.
>
> **And it is never written inline.** `-e DATABASE_URL=postgresql://user:password@...` puts a credential on
> the command line and is refused by the permission classifier (measured 2026-08-26 at a review axis; this is
> a separate finding from the role measurement above and shares only its date).
>
> **A database mutant requires `--reuse-db`, and the sentence above saying `--create-db` silently defeats
> one.** Measured 2026-08-25: with a marking in place in an isolated test database, the same case run with
> `--create-db` reports green, because `--create-db` drops and rebuilds from migrations and takes the mutant
> with it. The rule is therefore **a database of the run's own**, never the shared `test_mapsift`, with
> `--reuse-db` when a database mutant is in play.
>
> **A mount creates its own destination, so a probe never names a container path that does not already
> exist.** `-v` and `--mount` alike hand the runtime a bind whose mount point must exist, and the runtime
> creates it: an empty file when the source is a file, the whole directory chain otherwise. Because `/app` is
> a bind of `apps/api`, a destination invented under it is written into the repository as root, and where the
> runtime also created the parent directory the host user cannot remove it without a container.
> **`--mount`, `--tmpfs` and a named volume do not change this**, measured; they govern the source, which was
> never the failure. Two shapes are allowed. A **mutant** goes over a path that already exists. A **probe**
> whose destination does not exist is mounted outside every bind (`/probe/x.py`, never under `/app`) and
> invoked by that path, with `-c /app/pyproject.toml` when it needs the project's pytest configuration; it
> does not see `apps/api/conftest.py`, and `-p conftest` does not recover it, because pytest-django calls
> `django.setup()` after a `-p` plugin is imported, so **a probe needing a shared fixture is a mutant over an
> existing path rather than a probe**. If a stub is created anyway, remove it from inside a container:
> `docker run --rm -v "$PWD":/w alpine:3 rm -rf /w/<path>`.
>
> This supersedes the clause proposed in `specs/log.md` on 2026-08-20 and never applied, whose second half
> ("lives outside the repository") named the **host source** when what must not exist is the **container
> destination**: in all ten recorded stubs the host source existed.

---

## Consequences

**What this buys.** The conventions become reviewable decisions with a reason attached, instead of lines in a tooling file that nobody can trace. The three thresholds that were chosen (5 lines, the three-condition template exception, 8 direct children) are ratified, so changing one is a dated amendment that leaves a record rather than an edit nobody notices. And the layering resolves the loading problem the research exposed: the rule that must fire before the first file is written lives where it actually loads in time.

**What this costs.** Two artifacts to keep aligned per stack (the ADR and its rules file), and the discipline that the rules file restates rather than invents. Generating with the CLI is also marginally slower than typing a file, which is the point.

**What this forecloses.** Nothing the foundation left open. Per-stack conventions beyond layout and generation are not ratified here. The Angular ones are ratified in **ADR-0003**, which also draws the line between restating the official style guide (no ADR needed, the authority is external and cited) and a project decision (ADR needed). The Python and Rust ones, carried by `.claude/rules/python-django.md` and `.claude/rules/rust-core.md`, remain candidates for their own ADR when they stop being restatements of the canon and start being decisions.

**Reversibility.** All three thresholds are cheap to change and expensive to change silently. Amend this ADR rather than editing the rules file.
