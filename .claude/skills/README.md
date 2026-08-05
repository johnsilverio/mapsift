# Claude Code toolkit

Toolkit for **Mapsift**, a collaborative multi-platform GIS for environmental analysis. One repository,
organised by unit of deploy, with **four ecosystems in non-overlapping roles**: Rust in `libs/core` (the
shared client logic core, compiled to WASM and to FFI, and it does not run on the server), Python in
`apps/api` (the one Django plus django-ninja backend), TypeScript in `apps/web` and `libs/ui`
(`@mapsift/ui`), and Dart in `apps/mobile` when it exists. **No monorepo tool spans them**: each keeps its
native toolchain, and the `justfile` plus docker-compose orchestrate across.

Start from `CLAUDE.md`, `specs/mapsift-foundation.md` and `specs/index.md`.

**If the session being opened is an orchestrator session, the boot is the `orchestrate` skill**, and the
contract for the prompts it writes is `specs/testing.md` section 1.1. Nothing in this folder duplicates
either: a skill restating the window protocol would be the second copy that drifts.

## The discipline that governs this folder

Everything under `.claude/` is an authority Claude Code obeys. **A file here that contradicts the canon is
worse than an absent one**, because the agent follows it and cannot tell which authority is stale. So:

- **Audit by contradiction** whenever a file is added or changed. The chain is foundation → `specs/PRD.md`
  and `CLAUDE.md` → ADRs → the spec per task, and where a derived document disagrees with the foundation,
  the foundation wins.
- A closed decision **fans out** in one pass, and this folder is one of its targets when it changes
  something enforceable. The procedure is the `fan-out` skill.
- **Do not assert a dependency version from memory.** `specs/dependencies.md` is the survey and the
  lockfiles are what is installed.

## What lives where, and which mechanism carries what

Two questions, and they are different: **when is this paid for** (the tier) and **who fires it, and is it a
request or a guarantee** (the mechanism). The tier model is ADR-0002 section 5, which fixes the split
between the ADR that decides, the path-scoped rule that enforces, and the per-stack `CLAUDE.md` that carries
only operational residue.

| Tier | What | Fires | Paid |
| --- | --- | --- | --- |
| 0, always | the root `CLAUDE.md` | every session, again after a compaction | every turn |
| 1, path | `rules/*.md` with a `paths` frontmatter | when a file it governs is opened | per stack |
| 2, task | `skills/*/SKILL.md` | when the task matches the `description`, or on `/name` | per task |
| 3, cited | `specs/`, the ADR set | when a pointer names file plus section | per citation |

**Choosing the mechanism.** The four sentences that decide almost every case:

- **A skill is content; a subagent is a context.** Not alternatives on one axis: a skill can run inside a
  subagent. Reach for a **subagent only when isolation is the point**, which here means the three axes of
  `code-review` and exploration that would otherwise flood the window. Reach for a **skill when the output
  belongs in the main session**, which is most work.
- **A prompt instruction is a request; a hook or a CI gate is enforcement.** "Never do X" in prose is
  advisory no matter how bold the type. If it must hold every time and a script can decide it, it belongs in
  CI. Everything this project already made a gate is that insight arrived at earlier: `lint-imports` for the
  dependency direction, the catalogue test for row-level security, the golden vectors for the conflict rule.
- **A side-effecting skill declares `disable-model-invocation: true`**, so it costs nothing until the owner
  types it and the model cannot fire it alone. That is right for anything that commits, pushes, opens a pull
  request or rewrites the live state of the canon.
- **A command is the older form of a user-invoked skill.** Both surface as `/name`. New procedures are
  written as skills, so there is one place to look.

## The two-window protocol, and the skills that carry it

The protocol is `specs/testing.md` section 1 and it is not restated here. What this folder holds is the
procedure each role runs:

| Skill | Fires when | What it carries |
| --- | --- | --- |
| **`orchestrate`** | opening a session with no task picked up | the role, the boot state measured from disk, the rules, the register. **The orchestrator does not implement and does not touch code** |
| **`test`** | "write the failing tests", TDD, red, Window A | how a test is named, what it may assert, the three ways a red test still pins the wrong thing, seams, the report format |
| **`implement`** | "make it green", Window B | minimum to pass, triangulation, tests byte-identical, refactor under green |
| **`code-review`** | reviewing **your own** diff, before committing | machine gates first, then three isolated axes |
| **`pr-review`** | reviewing **somebody else's** pull request | reconstructing the intention you do not have |
| **`backlog`** | turning a problem into issues | outcome decomposition, sizing, dependency edges, vertical sequencing |
| **`fan-out`** | any closed decision | propagate by grep, never from memory, with the target table |
| **`writing-for-agents`** | writing or editing anything an agent reads | the loading tiers, pointer wording, the no-op test |
| **`onboard`** | you have **a task** and need **its** context | the per-task reading order, the trace to the authority |
| **`solid`** | in the refactor step, under green | SOLID, clean code, patterns, smells |
| **`docs-sync`** | auditing whether the documents are still true | walks the authority chain against disk |
| **`dev-workflow`** | branching, committing, opening a pull request | the single source of the branch convention, the commit format and the PR flow; `commit`, `pr` and `github-workflow` execute it and inject it rather than restating it |
| **`ticket`**, **`linear-workflow`**, **`quality-gate`**, **`commit`**, **`pr`**, **`github-workflow`**, **`pr-summary`**, **`session-handoff`**, **`plan`**, **`fix`**, **`systematic-debugging`**, **`worktree-commit-merge`** | the name says it | |

Beside them sit the **stack skills**, which are reference rather than procedure: the Angular set
(`angular-component`, `angular-di`, `angular-directives`, `angular-forms`, `angular-http`, `angular-routing`,
`angular-signals`, `angular-testing`, `angular-tooling`), and the backend set (`django-models`,
`celery-patterns`, `pytest-django-patterns`).

**`orchestrate` is not `onboard`, and the difference is worth knowing.** `onboard` runs when **a task
exists** and you need its context. `orchestrate` opens a session when there is **no task yet**: it loads the
role and the measured state, and it sends you to `onboard` the moment a task appears.

## The three consequences that bind anything added here

**A fact lives at exactly one tier and a higher tier points rather than restates**, so a skill carrying its
own copy of the method is the copy that goes stale.

**A pointer states where and when.** Its wording is what makes the agent reach through it, and an unreached
pointer is worse than an absent one: the material is then both unread and believed covered.

**The no-op test is the pruning gate**, applied line by line: delete the line, and if the agent's behaviour
does not change, it was paying context and buying nothing. When a sentence fails that test, delete the whole
sentence rather than shortening it, because a model told to trim optimises for length and cuts function with
it.

**What repeats across window prompts belongs here, not in the prompts.** That is why `test` and `implement`
exist: the standing discipline is identical every time, so writing it into each prompt pays for it every
time and lets the copies drift.

## `rules/`, the enforcement layer

Four path-scoped rules live at `.claude/rules/`: `angular.md`, `python-django.md`, `rust-core.md` and
`design-system.md`. A path-scoped rule fires **before** the agent writes its first file in a stack, which is
what makes it the right layer and also what makes a wrong one the most expensive kind of stale authority in
the tree.

**A rules file restates an ADR and decides nothing.** If a rule needs to change, the ADR is superseded and
the rule follows, never the reverse (ADR-0002 section 5). The Angular rule is ratified by ADR-0002 and
ADR-0003; the Python and Rust rules are not ratified by an ADR yet and remain candidates for one when they
stop restating the canon and start deciding.

## What this folder does not have, and why

**No `hooks/`.** The one layer that is a guarantee rather than a request does not exist here yet. The prose
rule (no em dash, no double hyphen) is therefore checked on the Craft axis of `code-review` rather than
enforced at write time, and that is a known gap rather than a decision.
