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

---

## Consequences

**What this buys.** The conventions become reviewable decisions with a reason attached, instead of lines in a tooling file that nobody can trace. The three thresholds that were chosen (5 lines, the three-condition template exception, 8 direct children) are ratified, so changing one is a dated amendment that leaves a record rather than an edit nobody notices. And the layering resolves the loading problem the research exposed: the rule that must fire before the first file is written lives where it actually loads in time.

**What this costs.** Two artifacts to keep aligned per stack (the ADR and its rules file), and the discipline that the rules file restates rather than invents. Generating with the CLI is also marginally slower than typing a file, which is the point.

**What this forecloses.** Nothing the foundation left open. Per-stack conventions beyond layout and generation are not ratified here. The Angular ones are ratified in **ADR-0003**, which also draws the line between restating the official style guide (no ADR needed, the authority is external and cited) and a project decision (ADR needed). The Python and Rust ones, carried by `.claude/rules/python-django.md` and `.claude/rules/rust-core.md`, remain candidates for their own ADR when they stop being restatements of the canon and start being decisions.

**Reversibility.** All three thresholds are cheap to change and expensive to change silently. Amend this ADR rather than editing the rules file.
