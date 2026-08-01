# Claude Code skills

Project skills for **Mapsift**, a collaborative multi-platform GIS for environmental analysis. The codebase
is a polyglot monorepo: Python (`apps/api`, the one Django plus django-ninja backend), TypeScript
(`apps/web` Angular and `libs/ui` `@mapsift/ui`), Rust (`libs/core`, the shared client logic core). See the
root `CLAUDE.md`, `specs/mapsift-foundation.md` and `specs/adr/0001-architecture-baseline.md`.

## The discipline that governs this folder

Everything under `.claude/` is an authority Claude Code obeys. **A skill that contradicts the canon is worse
than an absent one**, because the agent follows the skill and cannot tell which authority is stale. So:

- Audit by contradiction whenever a skill or rule is added or changed. The authority chain is
  foundation → PRD and `CLAUDE.md` → ADRs → per-task spec, and where a derived document disagrees with the
  foundation, the foundation wins.
- A closed decision fans out (session-handoff section 7). If it changes an enforceable rule, `.claude/rules/`
  is one of the fan-out targets.
- Do not assert a dependency version from memory. `specs/dependencies.md` is the canonical home and does not
  exist yet.

Last full audit: 2026-07-30, against foundation v0.11.1, PRD v0.8 and ADR-0001.

## What lives where

- **`rules/`**: path-scoped rules that load when Claude reads a matching file. This is where an enforceable
  per-language or per-path restriction belongs.
- **`skills/`**: procedures that load when the work matches their `description`.
- **`agents/`**: subagents with their own context (review, implementation).
- **`commands/`**: explicit slash commands.
- **`settings.json`**: shared permissions. **`settings.local.json`**: per-machine, gitignored.

## Rules

| Rule | Scope | Covers |
|------|-------|--------|
| [angular.md](../rules/angular.md) | `apps/web/**`, `libs/ui/**` | CLI-first generation, component file layout, folder organization, signals and control flow, the core boundary |
| [python-django.md](../rules/python-django.md) | `apps/api/**/*.py` | CLI-first generation, decisions versus effects, tenant isolation, queries, Celery, test placement |
| [rust-core.md](../rules/rust-core.md) | `libs/core/**` | The serializable boundary, the conflict rule, the operation queue, Rust hygiene |
| [design-system.md](../rules/design-system.md) | `apps/web/**`, `libs/ui/**` styles and templates | PRD section 9 (U1 to U12): tokens, the single material, shell, panels, icons, states, the library, accessibility |

## Skills by category

### Workflow and tracking

| Skill | Description |
|-------|-------------|
| [dev-workflow](./dev-workflow/SKILL.md) | **The source of truth** for the branch convention, the pre-commit gate, commits and the PR flow |
| [linear-workflow](./linear-workflow/SKILL.md) | The git versus Linear boundary and the Workspace/Team/Project/Milestone/Issue structure |
| [ticket](./ticket/SKILL.md) | Work a Linear ticket end to end (trace to the canon, branch, test-first, gate, PR) |
| [worktree-commit-merge](./worktree-commit-merge/SKILL.md) | Finish a worktree: commit, then to `main` by pull request, never a local merge |
| [pr-review](./pr-review/SKILL.md) | Review a pull request against the project standards |
| [pr-summary](./pr-summary/SKILL.md) | Write a PR body when the commits do not say enough |
| [onboard](./onboard/SKILL.md) | Read the canon and the code before starting a task |
| [docs-sync](./docs-sync/SKILL.md) | Check the specs against each other along the authority chain, and against disk |

### Backend (`apps/api`: Django, django-ninja, Pydantic, Celery)

| Skill | Description |
|-------|-------------|
| [django-models](./django-models/SKILL.md) | Models, chainable QuerySets, query optimization, PostGIS, migrations, and why decisions stay off the ORM |
| [celery-patterns](./celery-patterns/SKILL.md) | Task design, retries, idempotency, and what Celery carries in Mapsift |
| [pytest-django-patterns](./pytest-django-patterns/SKILL.md) | pytest-django, Factory Boy, the two-window cycle, the golden vectors |

### Frontend (`apps/web` Angular, `libs/ui` `@mapsift/ui`)

Verified against Angular v22 and the toolchain in `tests/prototypes/editor`.

| Skill | Description |
|-------|-------------|
| [angular-tooling](./angular-tooling/SKILL.md) | The CLI: what the v22 schematics actually emit, workspace and library commands, build, test, lint |
| [angular-component](./angular-component/SKILL.md) | Standalone components, signal inputs and outputs, OnPush, host bindings |
| [angular-signals](./angular-signals/SKILL.md) | signal, computed, linkedSignal, effect, and zoneless |
| [angular-di](./angular-di/SKILL.md) | inject(), injection tokens, provider configuration |
| [angular-directives](./angular-directives/SKILL.md) | Attribute, structural and host directives |
| [angular-forms](./angular-forms/SKILL.md) | Signal Forms (stable since v22.0), with Reactive Forms as the interop path |
| [angular-http](./angular-http/SKILL.md) | resource(), httpResource(), HttpClient, functional interceptors |
| [angular-routing](./angular-routing/SKILL.md) | Routing, lazy loading, functional guards and resolvers |
| [angular-testing](./angular-testing/SKILL.md) | Vitest through `@angular/build:unit-test`, Testing Library, user-centric tests |

### Debugging

| Skill | Description |
|-------|-------------|
| [systematic-debugging](./systematic-debugging/SKILL.md) | Four phases, root cause first, aimed at this system's real failure modes (sync, conflict, isolation, CRS, boundary) |

## Deliberate absences

- **No Rust skill yet.** `.claude/rules/rust-core.md` carries the rules; a full skill comes when `libs/core`
  exists. Until then follow foundation section 9.6 and PRD M8 to M15.
- **No SSR skill.** The product is an SPA plus a Tauri shell (foundation 9.6.1, PRD S1 to S3). There is no
  SSR surface in the canon.
- **No document skills** (docx, pdf, pptx, xlsx) and **no skill-creator**. Claude Code ships them, and the
  project copies were 3.7 MB of vendored scripts for a deliverable format nobody has decided (PRD J2 is open
  and owned by the engineer). They live at user scope now.
- **No skill router.** `.claude/hooks/` held a keyword router that was never registered as a
  `UserPromptSubmit` hook, so it never ran. Skills trigger by description. If a router is ever wanted, it
  needs the hook registered and its directory mappings corrected first (the old ones pointed `tests/` at the
  Django testing skill, which is the prototype folder, and `tasks/` at Celery, which does not exist).

## Adding a skill

1. Create `.claude/skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name              # lowercase, hyphens, max 64 chars
description: What it does and when to use it, with the words a user would actually say.
---
```

2. Include: when to use, the core patterns, the anti-patterns, and how it integrates with the other skills.
3. Check it against the canon before adding it, not after.
4. Add it to this README.

The `description` is what Claude matches on, so it carries the trigger words. If the instruction is really a
per-path restriction rather than a procedure, it belongs in `rules/`, not here.
