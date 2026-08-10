# Mapsift testing spec

> **Purpose.** The canonical method document. `CLAUDE.md` requires this file to be read before any test or any code is written, and ADR-0002 assumes its shape. It says how Mapsift is built, not only how it is checked, because in a test-first project those are the same statement.
>
> **Authority.** Derives from `specs/mapsift-foundation.md` section 14 (the development method) and the invariants, `specs/PRD.md` (every acceptance criterion is the upstream of a test), and `specs/adr/0001-architecture-baseline.md` sections 6 and 7. Where this file and the foundation disagree, the foundation wins.

---

## 1. The method: Red, Green, Refactor, in two windows

Work runs in **two clean-context windows**, and the separation is the point rather than ceremony.

**Window A writes the failing tests as behaviour.** It reads the requirement (a PRD acceptance criterion, a C-test, a spec-per-task) and writes tests that fail. It does not write the implementation and it does not look at one.

**Window B implements the minimum to green**, using those tests as a contract authored by someone else. It may not edit a test to make it pass. If a test looks wrong, that is a finding reported back, not a licence to rewrite the contract it is supposed to satisfy.

**Design happens in the refactor step, under green, never while a test is red.** A red test means one thing is unknown; refactoring under red makes two things unknown at once and the pair is what makes debugging expensive.

Why two windows and not two intentions: a single context that writes both sides converges the test toward the implementation it already has in mind, and the test stops being a specification. The separation is what keeps the test honest, and it is the same reason the conflict rule is golden-tested against two runtimes instead of trusted once.

### 1.1 The window prompt contract, and why the briefing is short

**A third window opens the task, dispatches the other two and reviews what they return**, and the
`orchestrate` skill is what boots it. It does not implement, it does not touch code, and it does not write
Window B's brief before Window A's result has been reviewed, because that brief **is** the review.

**A window is opened by the orchestrator or by the owner, and nothing in this section changes either way**
(added 2026-08-10, ADR-0008 section 4). Automatic is the default and carries the same prompt;
`orchestrate-manual` is the named alternative and the condition selecting it is in the ADR. Everything below
this paragraph holds in both.

A window is opened by a briefing, and the briefing is where the separation above is most easily thrown away. **A window is given the goal, the boundary of what is out of scope, where the authority lives, and the standard its result will be held to. It is not given a step list, a file list, or a name it could have read from the canon.**

The reason is the same one that justifies the two windows at all. A window handed a list of steps stops deciding and starts transcribing, so it discovers nothing, and the review that follows can only catch transcription. Worse, an error in the briefing then rides through unchallenged, because the pass that would have questioned it was told the answer instead. **Pre-deciding the shape destroys exactly the independent check the protocol exists to buy.**

There is a second reason specific to this repository. A briefing that restates a requirement is a **second copy of it outside the fan-out**, living in a message that is not versioned and not reviewed, which is the same defect the comment discipline forbids in code and the governance rule forbids between documents.

**One thing is handed over rather than withheld, and the distinction is evidence against instruction.** What cost a measurement, a probe, or an afternoon of diagnosis is given to the window directly, because it is not a decision the window should be making and it would otherwise have to be bought twice. A version that behaves unexpectedly, a tool that rejects a configuration the documentation seems to allow, a generator that writes a file nobody wants: these belong in the briefing, with their date, exactly as they belong in `specs/log.md`.

**The test that keeps a briefing honest:** if an item can be derived by reading the documents the briefing points at, it does not belong in the briefing. Wanting to write it anyway is a signal that the canon is incomplete, and the fix is then to write the document rather than the message.

**The standing discipline is a skill, and the prompt carries only what is task-specific.** The reading protocol, the rules about what a test may assert, and the report format are identical on every task, so they live in `.claude/skills/test/` and `.claude/skills/implement/` and load when the window is dispatched. Writing them into every prompt pays for them every time and lets the copies drift. **The window is the role and the skill is the procedure**, named differently on purpose: "Window A" and "Window B" name the two clean contexts and the separation between them, while `test` and `implement` name what each does, so a session that begins "write the failing tests for M2" reaches the right procedure without anyone knowing the protocol's internal vocabulary.

**The assembly of a task is an artifact in git, not a paragraph in a prompt.** A prompt is pasted into a chat and then gone, so leaving the assembly there makes the most carefully constructed artifact of the loop the only one not under version control, not reviewable as a diff and not readable by the next person. The assembly lives at **`specs/tasks/MAP-<n>-<slug>.md`**, it cites and never restates, and it is written **at pickup rather than at backlog creation**, because task specs written twenty at a time go stale before they are read. `specs/tasks/README.md` carries the shape. The prompt then shrinks to a pointer: read that file, invoke that skill, and here is what changed since it was written.

**The shape is semantic XML**, because a block boundary is what survives a prompt without the window losing which sentence was a rule and which was context. Window A carries `<reading-protocol>`, `<role>`, `<scope>`, `<behaviours>`, `<rules>` and `<deliverable>`. Window B carries the same, with `<behaviours>` replaced by `<semantics>`: what the review of Window A ratified, including spellings the tests chose and any accessor the implementation will be forced to add, pre-authorized with its spelling so the window does not have to guess and then defend it. With the skills in place most blocks are one or two lines, and `<rules>` is usually a single sentence naming what is unusual about **this** task.

**Four things a prompt states, and the third is the one always forgotten:** the objective, the approach you prefer while leaving room for a better one, **what you explicitly do not want**, and how success is verified. The out-of-scope block is not politeness; the measured root cause of agents destroying work is vague instruction.

**The two sentences that belong in every prompt, in both directions:**

> If this prompt contradicts the foundation, the PRD or an ADR, **stop and report instead of choosing**: the canon wins. Window B additionally may not edit a test to make it pass, and a test that looks wrong is a finding reported back, never a licence to rewrite the contract it exists to satisfy.

That reflex has to be armed explicitly, because a window that quietly reconciles a contradiction produces green code over a canon that is now wrong, and nobody finds out until the next adversarial pass.

### 1.2 Task size is part of the protocol

Mature TDD practice names "write every test, then write every implementation" as an anti-pattern called **horizontal slicing**, on the argument that bulk tests verify *imagined* behaviour: the shape is pinned before the implementation has taught anything, and the tests go insensitive to real change. The remedy it offers is a **vertical slice**, one test and one implementation at a time.

The two-window protocol is horizontally sliced by construction, and its own reason is equally real: a single context that writes both sides converges the test toward the implementation it already has in mind.

**Both hold, and they resolve on task size rather than on protocol.** A window pair is safe exactly while the task is thin enough that all of Window A's tests are still **one tracer bullet**: one behaviour cluster, one seam, one requirement or a tight group of them. It stops being safe when Window A is writing tests for work it cannot picture, and the tell is visible in the prompt before anything runs, as a scope block listing several unrelated behaviours or requirements that share no seam.

**Sizing the slice is therefore the orchestrator's job and a first-class step.** A task that does not fit is split into two dispatches, which costs one extra pair of windows and buys tests that pin behaviour somebody understood. The complementary move is equally allowed: a batch of small adjacent tasks over the same material runs as **one** window pair, because the overhead of the protocol should not exceed the work it protects.

**The review that closes a window is a run, not a read of its report**, and it is the `code-review` skill. The machine gates of section 8 run **first and by the orchestrator**, and only when they are green does judgement start, over three axes in isolated contexts that are never merged into one ranked list: **Canon** (the invariants and the ADR shape, blocking), **Spec** (the requirement's criterion, missing or wrong is blocking and scope creep is advisory), and **Craft** (test quality, smells, navigability, advisory).

Two reasons the run is not optional. A test can be red for the right reason and still pin the wrong behaviour, and the requirement is the only thing that catches that. And a published coding-agent benchmark records models that build a reasonable thing and then **hallucinate their own inspection**, which is the empirical form of this project's older rule that a state claim is written only with the command that verified it.

**Language.** Every prompt is written in **English**. Windows A and B may report back in English. The orchestrator answers the owner in **Portuguese**, and every artifact either window produces stays English.

---

## 2. What a test asserts

**Behaviour, never implementation.** Assert what Mapsift guarantees: the returned value, the emitted error, the persisted state, the observable effect. Never a private shape, never an internal call order, never that a particular function was invoked.

The consequence is the rule that tells you whether a test is good: **a test changes only when a requirement changes.** A test that has to be edited because a function was renamed or a class was split was testing the wrong thing, and it will keep charging that tax on every refactor.

One behaviour per test, one test per behaviour. Arrange, act, assert, in that order and **separated by a blank line rather than labelled with `// Arrange` comments**, which say what the code already says and are the naming failure the comment discipline forbids. A test whose name needs "and" is two tests.

---

## 3. The architecture that makes this possible

Testability is not a property you add to code, it is the shape you give it. **Separate decisions from effects.**

A **decision** is pure: plain data in, plain data out, no clock, no network, no database, no filesystem. In Mapsift the decisions are also the parts that matter most, which is not a coincidence: conflict resolution by granularity, tenant and permission resolution, geometry math, the metric frames, spectral indices, config merge, geometric validation, the versioning and upcasting rules. **These carry the bulk of the test suite** and they need nothing but a function call to test.

An **effect** is I/O: PostGIS beyond the ORM, object storage, the tile servers, the imagery APIs, the sync transport, the local store. Effects sit **behind narrow interfaces** with two implementations, a real adapter and a test fake. The interface is narrow on purpose: an interface that mirrors a whole vendor SDK is not a seam, it is the vendor with extra steps.

**The rule of thumb, and it is a diagnosis rather than a preference:** if a piece of logic can only be tested with the network, a live PostGIS, or a large raster, **it was factored wrong**. Do not reach for a heavier harness. Pull the decision out of the effect and test the decision.

---

## 4. The kinds of test in this project

**Pure decision tests.** The bulk. Fast, deterministic, no fixtures beyond plain data.

**Boundary contract tests.** Every boundary validates (Pydantic on the API, the WebSocket messages, config; the generated types across the core boundary). The test asserts that invalid input is rejected at the boundary with a typed error, and that a valid payload survives the round trip unchanged.

**Cross-runtime golden tests.** The conflict rule exists in the Rust core and in the Python server by design (foundation 9.6.6). A **single canonical corpus of vectors** in the declared contract of PRD M13 runs against **both** runtimes in CI, and divergence fails the build. Two properties of this corpus are not optional. It lives in **one shared location** consumed by both suites, never copied per language, because two copies of a golden corpus is two corpora. And where the rule consults a geometric predicate, the comparison uses the **tolerance declared in metres** (M13), because the client's pure-Rust engine and the server's GEOS-via-PostGIS are structurally different implementations (`specs/dependencies.md` section 2), so bit-equality is the wrong thing to demand. **A legal-weight case that lands inside the tolerance band must resolve to flag-and-preserve on both runtimes**; that is itself a test, not an implementation detail.

**Invariant acceptance tests.** Each constraint C1 to C14 in `CLAUDE.md` carries a pass/fail test, and each is the executable form of a foundation invariant. These are the tests that may never be weakened. When one of them fails, the answer is never to adjust the test.

**Integration tests with real adapters.** Few and deliberate: the ones that prove the adapter actually speaks to the real thing. They are not where behaviour is specified; they are where the seam is validated.

**Measurements are not tests.** The N1 budgets (the per-tile budget, the editable working set, the element budget) are **recorded measurements with their device, versions, fixture, and date**, in both material modes. Do not wire them as a pass/fail CI gate on shared runners: a performance assertion on unstable hardware fails randomly, and a suite that fails randomly is a suite people learn to ignore. Measure deliberately, record, and compare against the recorded baseline.

---

## 5. Where tests live

Each ecosystem holds its own tests in its own idiom, beside the code they test (ADR-0001 section 7): pytest under `apps/api`, the Angular workspace runner under `apps/web` and `libs/ui`, Cargo tests under `libs/core`. **The exception is the golden corpus**, which lives in one shared fixture location and is consumed by both the Rust and the Python suites.

There is no root `tests/` folder for application tests. `tests/` at the repository root holds throwaway material (the prototypes), not the suite.

---

## 6. Traceability: from a requirement to a test

Every PRD acceptance criterion is the upstream of a test, and the link is written rather than remembered: **a test that implements a criterion names its ID** (a C-test, a T, M, S, N or U requirement, or the family item it comes from). The granularity follows the module (settled 2026-08-05, after the rule as first written admitted both readings): the ID is named **per test** where a module's tests differ in what they cover, and **once at the module** where the whole module serves one set. Two things follow. A requirement with no test is visible by grep. And a test with no requirement is a candidate for deletion, because it is asserting something nobody agreed to.

When a requirement changes, the test changes with it in the same pass. That is the fan-out rule applied to the suite.

---

## 7. What is not tested

- **Trivial or generated code.** A generated type is guaranteed by the generator plus the freshness check in CI (ADR-0001 section 5); asserting its shape by hand is a second copy of the contract.
- **Third-party libraries.** Test your use of them, not them.
- **Unbuilt futures.** A test for a capability that is not specified is a guess with a green checkmark.
- **The ORM.** It is a persistence detail (foundation section 10). Testing that Django saves a row tests Django.

Two anti-patterns worth naming because they look like diligence. **Mocking what you do not own**: a fake of a vendor SDK asserts your belief about the vendor, and it passes while production fails. Put the vendor behind a narrow interface and fake the interface. **Snapshot tests of markup**: they fail on every cosmetic change and are approved without reading, which converts a test suite into a rubber stamp.

---

## 8. The gate

**Pre-commit** runs the fast subset: format, lint, type check on the changed files.

**CI blocks** on the full set from ADR-0001 section 6: `mypy --strict` with django-stubs and `ruff`; `tsc` strict and the linter; the Rust check, clippy, and formatting; every ecosystem's suite; the generated-contract freshness check; and the cross-runtime golden corpus. A red build is not merged and is not overridden.

---

## 9. The two rules that survive everything else

**Never write the implementation first and the test after.** A test written after the code tests the code that exists, not the behaviour that was wanted, and it will agree with a bug.

**Never weaken a test to make it pass.** If a test blocks you and you believe it is wrong, that is a conversation about the requirement, in the requirement's document, not an edit in the suite.
