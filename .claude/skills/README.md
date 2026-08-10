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

## A day of work, and where each skill falls in it

The protocol is `specs/testing.md` section 1 and it is not restated here. This section answers the question
an index usually does not: **at which moment do I reach for this, and what does typing it actually do.**

**You open a session and type `/orchestrate`.** It injects the measured tree, the tracker and the live state
before the model says anything, so the first answer is the divergence between disk and document rather than
a greeting. You pick the issue. The orchestrator runs **`onboard`** for that issue's context, writes the task
spec at `specs/tasks/MAP-<n>-<slug>.md`, and brings you the boundary decisions with a recommendation and a
cost each. You rule. It **registers your verdict in the canon before dispatching anything**, because a
decision that exists only in a chat message is invisible to the next clean window.

**Then the two windows, one at a time, dispatched by the orchestrator on your go** (ADR-0008 section 4;
`orchestrate-manual` if you would rather open them yourself). Window A runs **`test`** and writes the
failing tests. The orchestrator closes it by **running** `code-review`, never by reading its report. Only then does Window B's
brief exist, because that brief is the review; Window B runs **`implement`** and reaches green without
touching a test. The gate runs again, and you get a verdict plus a suggested commit message.

**Closing:** `/quality-gate` if you want the checks alone, `/commit`, `/pr`, and `/session-handoff` at the
end of a session that changed the live state.

If a decision was closed anywhere in that day, **`/fan-out`** is what finishes it, and the decision is not
closed until it has run.

### The procedure skills

| Skill | The moment you reach for it | What typing it does |
| --- | --- | --- |
| **`orchestrate`** | opening a session with no task chosen, or asking "what is next" | injects the tree, the tracker and the live state, then takes the orchestrator role. **Dispatches each window itself** on the owner's go, showing the prompt first. **It does not implement and does not touch code**: a finding goes back to a window, never into your own edit |
| **`orchestrate-manual`** | the same, while the task is **still being understood** | identical in every respect except that the owner opens the windows |
| **`onboard`** | a task exists and you need **its** context | directs the reading for that task, traces it to the requirement and the invariants, explores the code that will change |
| **`test`** | Window A, or any "write the tests for X" | writes failing tests as behaviour and nothing else; carries naming, what a test may assert, the three ways a red test still pins the wrong thing, and the report format |
| **`implement`** | Window B, or "make it green" | minimum to pass, triangulation, refactor under green, and the rule it will not break: **the test module ends byte-identical** |
| **`code-review`** | before committing **your own** diff, and to close a window you dispatched | runs the machine gates first, then three axes in isolated contexts (Canon blocks, Spec blocks, Craft advises) and never merges them into one ranked list |
| **`pr-review`** | a pull request **somebody else** wrote | reconstructs the intent you do not have before judging it, and separates what blocks a merge from what is a request to the author |
| **`quality-gate`** | before any commit or PR, or "do the checks pass" | runs what CI runs, for the ecosystems the diff actually touched, inside the container |
| **`fix`** | the lint or the types are red | reads what the checks report and fixes that, rather than guessing |
| **`plan`** | thinking through a change before any code exists | grounds an approach in the canon and the codebase, then stops and waits |
| **`backlog`** | "break this down", "create the issues", filling or grooming | acts as product owner and scrum master: decomposes into outcomes rather than task lists, sizes against the tracer-bullet rule, sequences vertically, and **refuses** to invent a requirement the canon does not carry |
| **`ticket`** | you have an issue ID and want it worked end to end | reads it, checks that it traces to the canon, branches, drives both windows, gates, and opens the PR |
| **`linear-workflow`** | before touching any issue, project or milestone | the git and tracker boundary, when an issue may exist at all, the status automation, the MCP isolation |
| **`fan-out`** | the instant any decision is closed, changed or refused | propagates by grep across every document that names it, with the target table, so the canon cannot contradict itself |
| **`writing-for-agents`** | writing or editing anything an agent reads, or when an agent ignored a written rule | the loading tiers, how to word a pointer so it fires, the no-op test, and how to prune duplication |
| **`docs-sync`** | "are the specs still true" | walks the authority chain and compares it against disk |
| **`solid`** | in the refactor step, under green, never while red | SOLID, clean code, patterns and smells, spent where design belongs. **Vendorized and stack-agnostic, so it decides nothing**: its precedence block names the five places it collides with the canon, comments and value objects among them |
| **`systematic-debugging`** | a bug, a failing test, something unexplained | root cause before any fix, in four phases |
| **`dev-workflow`** | the single source for branch, commit and PR conventions | `commit`, `pr` and `github-workflow` **inject** it rather than restating it, so there is one copy |
| **`commit`**, **`pr`**, **`github-workflow`**, **`pr-summary`**, **`worktree-commit-merge`**, **`session-handoff`** | closing work out | the last four write history, push, or rewrite the live state, so they stay yours to type |

### The stack skills, which are reference rather than procedure

The Angular set (`angular-component`, `angular-di`, `angular-directives`, `angular-forms`, `angular-http`,
`angular-routing`, `angular-signals`, `angular-testing`, `angular-tooling`) and the backend set
(`django-models`, `celery-patterns`, `pytest-django-patterns`).

**They are deliberately many and deliberately small.** A task about routing should pay for routing and not
for forms, which is the whole point of tier 2: the description matches, one payload loads. Consolidating them
into one `angular` skill would hand every task all nine payloads, which is the attention-budget failure this
folder is organised against. If one of them fails to fire when it should, **the defect is its description**,
and the fix is `writing-for-agents` rather than a router on top.

What they do **not** carry, and what therefore has to come from elsewhere: the build order (`libs/core` then
`libs/ui` then `apps/web`, a requirement rather than a convention), generating with the CLI before editing
(ADR-0002), importing the library from its barrel only (ADR-0003), and the rule that client logic belongs in
the shared core rather than in the Angular layer (C11). Those live in `.claude/rules/`, which fires when a
file in that stack is opened.

### Two pairs that are easy to confuse

**`orchestrate` is not `onboard`.** `onboard` runs when **a task exists** and you need its context.
`orchestrate` opens a session when there is **no task yet**: it loads the role and the measured state, and it
sends you to `onboard` the moment a task appears.

**`code-review` is not `pr-review`.** The first reviews work **you commissioned**, where the requirement, the
task spec and the canon were all in the window's reading protocol, so "they could not have known" is not
available as an explanation and the standard is higher. The second reviews code from outside that loop, so it
reconstructs the intent first and marks explicitly what it cannot know.

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

**A rules file restates an ADR and decides nothing.** If a rule needs to change, the ADR is amended first
and the rule follows, never the reverse (ADR-0002 section 5). The Angular rule is ratified by ADR-0002 and
ADR-0003; the Python and Rust rules are not ratified by an ADR yet and remain candidates for one when they
stop restating the canon and start deciding.

## `hooks/`, the enforcement layer

Three scripts at `.claude/hooks/`, wired in `.claude/settings.json`, added 2026-08-10 under **MAP-40**.
Until then this section said the layer did not exist and called that "a known gap rather than a decision",
which was true for as long as a human sat between every instruction and every file.

| Hook | Fires | Refuses |
| --- | --- | --- |
| `check-prose.sh` | `PostToolUse` on `Write`, `Edit` | an em dash, en dash or double hyphen in prose in any `.md` (`writing-for-agents`) |
| `block-main-push.sh` | `PreToolUse` on `Bash` | a push touching `main` (`dev-workflow` section 5) |
| `block-production-secrets.sh` | `PreToolUse` on `Bash`, `Write`, `Edit` | a credential written or staged, and `git add -A` (C6, I7) |

**What a subagent inherits was measured rather than assumed, and it lives in ADR-0008 section 4** with the
decision that rests on it. The hooks also fire **without a session restart**, learned when the first secrets
hook blocked its own test command minutes after being written.

**The suite is `.claude/hooks/hooks-test.sh` and it is the rule** (ADR-0002 section 5): a hook is proven by
tripping it, never by prose. Thirty cases, and the ones marked REGRESSION are the five defects the first
three hooks shipped with, each of which **passed** before the fix.

**A guard wider than its rule gets switched off, which is worse than not having it.** That is not a maxim
here, it is what happened: one version refused the rebase recovery `dev-workflow` section 5 prescribes, and
another refused every edit to `README.md` over a shields.io escaped hyphen. Match at a command position and
per token, and honour the exemptions the canon has already written.

`settings.json` also carries the allow list that stops a session prompting on the ordinary `git` and `gh`
verbs, `add` and `commit` included. **The hooks are what make that list defensible**, since staging a
credential or staging everything, and a push touching `main`, are refused by rule regardless of the
permission.

## What this folder does not have, and why

**No `agents/`.** A subagent is dispatched with a prompt rather than defined as a type, which is what the
three `code-review` axes do. A definition earns its place when the same role is dispatched often enough that
its prompt is a file rather than a paragraph.
