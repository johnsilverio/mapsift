---
allowed-tools: Bash(sed *), Bash(ls *), Bash(grep *)
name: test
description: Write the failing tests for a Mapsift task, as behaviour, implementing nothing. Use this whenever the user asks for tests, mentions TDD, red tests, test-first, a PRD requirement identifier, an invariant, a C-test, or dispatches the first window of the two-window protocol. Use it even when the request is just "write tests for X" or "add a test for this bug", because in this ecosystem the test is written before the code and this skill is how. Triggers on "/test", "write the failing tests", "red tests", "test-first pass", "Window A". Not for running an existing suite, which is the quality gate, and not for making tests pass, which is the `implement` skill.
---

# Write the failing tests

Write **tests that fail**, plus the minimum production signatures for them to compile and fail. Implement
nothing. The `implement` pass makes them green using these tests as a contract it may not edit, which only
works if the contract came from the requirement rather than from an implementation you had in mind.

This skill carries what is true on **every** test-writing pass. The prompt that dispatched you carries what
is true only for **this task**: the requirement, the boundary, what is out of scope, and anything the
orchestrator ratified. If the two disagree, the prompt is more specific and wins; if the prompt disagrees
with the canon, neither wins and you **stop and report** (see the last section).

## The method, injected because you cannot write a test here without it

This is `specs/testing.md`, loaded from disk right now rather than asked for. It is the authority; where
this skill and the text below disagree, **the text below wins**.

!`sed -n '/^## 1\. The method/,$p' specs/testing.md`

## The task specs on disk

!`ls specs/tasks/MAP-*.md 2>/dev/null || echo "(none picked up yet)"`

---

## 1. Read before writing, and read from disk

Read completely, in this order. Do not skim and do not answer from another session's memory.

1. The **task spec** the prompt names, at `specs/tasks/MAP-<n>-<slug>.md`. It is the assembled contract and
   it cites the rest; where it and a cited document disagree, the cited document wins.
2. The **requirement** it cites, in `specs/PRD.md`: the statement, its acceptance criterion, the citation
   upward. **The criterion is your test.** A requirement whose Open/ADR field is unresolved has a gap, and a
   gap is reported rather than guessed.
3. **The method is injected above, so do not open `specs/testing.md` again.** Section 2 is what a test may
   assert, section 3 the shape the code must have, section 7 what not to write.
4. The **invariants** the prompt names (`specs/mapsift-foundation.md` section 11, I1 to I11), the
   **constraints** (`CLAUDE.md`, C1 to C14) and the **ADR sections** it names. These carry the shape you must
   not invent around.
5. The code you build on, in full. Not the parts you expect to need.

Then invoke the **`solid`** skill and follow it.

**Read what the prompt points at, and nothing it did not point at "just in case".** An unscoped read fills
the window with material that competes for attention with the requirement you are implementing.

## 2. What a test asserts

**Behaviour, never implementation.** The returned value, the emitted error, the persisted state, the
observable effect. Never a private shape, never an internal call order, never that a particular function was
invoked. The litmus test is in `specs/testing.md` section 2: a test changes only when a **requirement**
changes, and one that goes red on a refactor that introduced no bug was testing implementation and will
charge that tax forever.

**Name the behaviour as a domain sentence.** `a_served_layers_features_never_enter_the_operation_queue`,
never `test_layer_2`. A name that needs "and" is two tests.

**Name the identifier.** Every test that carries an invariant, a constraint or a requirement puts `I4`, `C7`
or `M9` in its name, its docstring or a single comment (`specs/testing.md` section 6). A requirement with no
test naming it is invisible to grep, which is the property that section exists to buy.

**One behaviour per test, one test per behaviour.** Arrange, act, assert, visibly.

### The three ways a red test still pins the wrong thing

Red for the right reason is not the same as correct. These are the failure modes to check your own work
against before reporting.

- **Implementation-coupled.** It mocks an internal collaborator, reaches a private, or verifies through a
  side channel (querying the table instead of asking the interface). The tell: it breaks on a refactor while
  behaviour is unchanged.
- **Tautological.** The expected value is recomputed the way the code computes it, so it passes by
  construction and can never disagree with the implementation. Expected values come from an **independent**
  source: a literal, a worked example, the acceptance criterion, the norm, the domain expert. The canonical
  case in this system is geodesic area, where `geodesic_area_unsigned` returns the area the ring encloses
  under its own orientation, so a reversed ring yields the rest of the planet: measured, 1.23e10 square
  metres the right way round and 5.10e14 the wrong way. A test that computed its expectation the way the
  function does would have agreed with that.
- **Unwitnessed happy path.** You tested that the rule fires and never that it stays quiet, so an
  implementation that always fires stays green. Every conditional rule needs both sides.

**And one that is specific to this system: the silent-empty trap.** The isolation wall denies by returning
**nothing** (ADR-0005 section 4), so an assertion that a query came back empty may be asserting the policy,
the application guard, or a genuine absence, and those are three different behaviours. Distinguish which
mechanism refused, the way the existing suite does by asserting the SQLSTATE rather than that something
raised.

## 3. Seams: where the tests go, and what may be faked

A **seam** is the public boundary you observe behaviour at without reaching inside. Tests live at seams,
never against internals. **Name the seams before writing anything**, and if the prompt did not pin them,
state the ones you chose in your report so the orchestrator ratifies them. You cannot test everything;
agreeing the seams up front is how the effort lands on the decisions that carry risk instead of on every edge
case.

`specs/testing.md` sections 3 and 4 decide which seams this ecosystem has and what may be faked, and this
skill does not restate them. The one rule worth carrying at the point of writing: **if a piece of logic can
only be tested with the network up, a large raster on disk, or a live PostGIS, it was factored wrong.** Do
not reach for a heavier harness. Pull the decision out of the effect and test the decision, and say so in
your report, because that is a design finding.

**If the scope you were handed does not fit one tracer bullet, say so before writing.** The pass is safe
while the task is one behaviour cluster around one seam; the tell that it is not is a scope listing unrelated
behaviours or requirements that share no seam. Writing tests for work nobody can picture yet produces tests
that pin an imagined shape and go insensitive to real changes. Report it and let the orchestrator split the
dispatch (`specs/testing.md` section 1.2).

The exceptions are real and named: row-level security and its FORCE state, the database roles and their
GRANTs, the composite keys that close the referential-integrity channel, PostGIS geometry and its type
modifier, and the WebAssembly boundary cannot be faked and run against the real thing.

## 4. Mechanics

- **No logic in a test.** No loops, no conditionals, no computed expectations. Literal expected values. A
  test must be obviously correct without needing a test of its own.
- **DAMP over DRY.** A little duplication that keeps a test readable top to bottom beats a shared helper the
  reader has to scroll away to understand. Hide boilerplate, keep the field the test is about visible in the
  body.
- **Do not test** trivial code with no logic, generated code, a third-party library, or a future that does
  not exist. Bloat is liability: every redundant test breaks on a refactor for no reason.
- **Signatures only.** Write the minimum production surface for the test to compile and fail. Not the body.
- **A test importing a name that does not exist yet is a type-check error before it is the runtime red it
  asserts.** Two cases, and they resolve differently (revised 2026-08-05, the MAP-7 review). An import the
  implementation window will create is **left red**: that red is part of the deliverable, and an anchored
  ignore on it becomes an error the moment the module exists (strict mypy warns on unused ignores), forcing
  the implementing window to edit a test it may not touch. A static error with **no production fix coming**
  keeps the resolution this project already paid for: the narrowest anchored ignore on that line, or the
  import moved inside the test function so the module still collects, never a module-wide exemption.

## 5. Touching a test that already exists

You may, and only for a **mechanical** ripple: a signature gained a parameter, a constructor gained a field.
**No existing assertion may be weakened, reworded or deleted, and every existing test must still be there
under the same name.** Report the before and after counts per file.

If making an existing test compile seems to require changing what it asserts, **stop and report**. That is a
requirement change, and a requirement changes in `specs/PRD.md` first.

## 6. Scope

**Build only what the prompt scoped.** A behaviour that is genuinely unwitnessed and would let a wrong
implementation stay green is worth adding, so add it **and report it explicitly**. Never expand scope in
silence, and never invent a requirement: a behaviour nobody wrote down is a **PRD change**, which is a commit
and a fan-out, not a line you author inside a test file.

## 7. Deliver

Run these yourself and report the real numbers, never an estimate. The gate is `specs/testing.md` section 8,
and every command runs **inside the container** (ADR-0001 section 3), which is what CI reproduces.

Report, in this order:

1. **The tally**, with where each red lands and the failure message. Your new tests fail; every existing test
   stays green.
2. **Before and after test counts** per file touched, with the confirmation that no existing assertion was
   weakened.
3. **Lint, type check and format**: the actual output, not "clean".
4. `git diff --stat`.
5. **Every choice the prompt did not pin**: helper names, fixture shapes, the spelling of anything new. The
   orchestrator ratifies these, and an unratified spelling becomes two spellings.
6. **Anything you believe is wrong** in the prompt, the requirement or the canon.

**Show the evidence, do not assert success.** A window that reports "all green" without the output is asking
to be re-run by the reviewer, and it will be.

## 8. Stop and report

> If this prompt contradicts `specs/mapsift-foundation.md`, `specs/PRD.md` or an ADR, **stop and report
> instead of choosing.** The canon wins, and the orchestrator records the correction before you continue.

A window that quietly reconciles a contradiction produces green tests over a canon that is now wrong, and
nobody finds out until the next adversarial pass. That reflex has caught real defects in this project in both
directions, including in a task spec the orchestrator had just written.

**Language:** code, test names, comments and any report you write are in **English**.
