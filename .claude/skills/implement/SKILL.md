---
allowed-tools: Bash(sed *), Bash(ls *), Bash(git *)
name: implement
description: Write the minimum production code that turns failing tests green, then refactor under green without touching the tests. Use this whenever the user asks to implement a feature, build something, make failing tests pass, or dispatches the second window of the two-window protocol. Use it even when the request is just "implement X" or "build the endpoint", because implementation here always starts from red tests and this skill is how. Triggers on "/implement", "make the tests pass", "make it green", "implementation pass", "Window B". Not for writing the tests themselves, which is the `test` skill.
---

# Minimum to green

The red tests in the tree are the **executable specification**, and they were written by another pass so
the implementation cannot shape itself to a contract it authored. Write the minimum production code that
turns them green, then refactor under green.

**If there are no red tests, stop.** Do not write production code first and tests after: a test written
after the code tests the code that exists rather than the behaviour that was wanted, and it will agree with
a bug. Report that the contract is missing and let the `test` pass run.

This skill carries what is true on **every** implementation pass. The prompt that dispatched you carries
what is true only for **this task**: the semantics the review of the test pass ratified, the accessors
pre-authorized with their spelling, and the boundary. If the prompt disagrees with the canon, **stop and
report**.

## The method and the gate, injected because you cannot finish without them

This is `specs/testing.md`, loaded from disk right now rather than asked for. It is the authority; where
this skill and the text below disagree, **the text below wins**. Section 8 is the gate you have to pass.

!`sed -n '/^## 1\. The method/,$p' specs/testing.md`

## What is red right now

!`git status --short 2>&1 | head -20`

---

## 1. The rule that defines this window

**Do not modify the test module. Byte-identical when you are done.**

If a test looks wrong, that is a **finding you report**, never a licence to rewrite the contract you exist
to satisfy. Weakening a test to make it pass is the one move that destroys the whole protocol, because the
suite then agrees with the bug.

Do not add a variant, a type, a derive or a dependency that the tests do not force. Everything you need
either exists or was pre-authorized in the prompt.

## 2. Read before writing

1. **The red tests, every one of them.** They are the contract; read them the way you would read a spec.
2. The prompt's `<semantics>` block: what the review pinned, and what it deliberately left to you.
3. **The method is injected above, so do not open `specs/testing.md` again.** Read section 8, the gate,
   twice.
4. The **ADR sections** the prompt names, for the shape the code has to take, and the requirement in
   `specs/PRD.md` so you know what the tests are trying to say.

Then invoke the **`solid`** skill and follow it, spending it in step 4 and not before.

## 3. Minimum first, and triangulation is allowed

The three laws, held literally: no production code except to make a failing test pass, no more production
code than is sufficient to pass the one failing test.

**Faking a return is legitimate** until a second test forces the real implementation. That is
triangulation, not cheating, and it is how the tests prove they actually constrain the code.

**Do not anticipate.** A branch no test exercises is a branch nobody asked for, it is untested by
construction, and `specs/testing.md` section 7 calls that speculative generality. If you implemented
behaviour no test witnesses, say so in the report; the orchestrator turns it into a witness or you delete
it.

**One step at a time, and check each one.** Make one test pass, run the suite, then take the next. A pass
that writes everything and runs the gate once at the end has no idea which change broke what, and the
debugging cost of that is the whole saving spent back with interest.

## 4. Refactor under green, never under red

**Design happens here**, and the order is Kent Beck's: **make it work, make it right, make it fast.**
Reversing it, reaching for the elegant shape or the fast one before the behaviour exists, is the single
most common way an implementation pass produces abstractions nobody needed.

A red test means one thing is unknown; refactoring under red makes two things unknown at once, and that
pair is what makes debugging expensive.

Under green, the `solid` skill applies: single responsibility, small functions, names that reveal
intent, early returns over nesting. The rule of the third repetition governs abstraction here as it does
everywhere in this ecosystem, so two similar blocks are two blocks.

**Write code an agent can navigate**, because the next reader is one. Distinctive greppable names over
`Service`, `Manager`, `handler` or `data`; files that stay small enough to read in one pass; explicit types
at every boundary; and error messages that carry the value and the expectation rather than
`invalid input`, because the next window debugs from that string.

## 5. Comments

`CLAUDE.md` governs this and it is stricter than instinct. An inline comment earns its place only when the
correct code **looks wrong**, or the wrong code looks right, so that without the note somebody "fixes" it
and reintroduces the defect. An explanation of what the code does is a naming failure.

**The default is zero, and a file that comes back with no inline comment is the expected result rather than
a suspicious one.** That default exists because the condition above is judged by the pass that just wrote
the line, and to whoever just wrote it everything looks slightly less obvious than it is. Two mechanical
tests before a comment survives.

- **The no-op test** (`writing-for-agents`, pointed at code here): delete the line. If a maintainer would
  still make the same edit, it was buying nothing.
- **The ratio**: a comment longer than the code it guards has lost, because the guard is now the thing that
  needs explaining.

**A citation is a pointer, not a footnote habit.** A decision the canon already documents is cited by
identifier (`M9`, `C7`, `ADR-0005 section 3`) **once, on the line whose shape that decision made
surprising**, and never repeated on every line the decision touched. Restating the reasoning creates a
second copy that drifts, because nothing propagates into a comment. A docstring on a public surface saying
what the thing **guarantees** is a different artifact and is welcome.

```rust
// ❌  Flatten the operation so its keys sit beside the envelope's
    #[serde(flatten)]

// ❌  M8: the envelope is self-describing
    pub operation_schema_version: u32,

// ✅  Not `geodesic_area_unsigned`, whose name lies: it returns the area enclosed under the
//     ring's own orientation, so a reversed ring yields the rest of the planet. Measured on
//     a one-degree square: 1.23e10 the right way round, 5.10e14 the wrong way.
    value: polygon.geodesic_area_signed().abs(),
```

The first says what the attribute below it already says. The second staples an identifier to a line nobody
was going to touch, which is the citation budget spent on nothing. **The third is the only shape that
survives**, and it is real (`libs/core/src/metric.rs`): without it the next reader reaches for the
obvious-looking name and puts the defect back.

## 6. Scope

Touch only what the prompt scoped and what the tests force. **Never `cargo fmt`-style sweeps, drive-by
renames or opportunistic cleanups**: a hunk that crosses a task boundary cannot be separated by
`git add -p` afterwards, because a hunk does not respect the boundary you meant.

If something outside your scope is broken, report it. Do not fix it.

## 7. Deliver

Run the full gate yourself and report real numbers, never an estimate. `specs/testing.md` section 8 has the
list and the `justfile` has the commands, which run **inside the container** (ADR-0001 section 3) because
that is what CI reproduces. `just check` is the whole set; the individual recipes are what you use while
iterating.

Report, in this order:

1. **The suite**, exact counts, all green, per ecosystem you touched.
2. **Lint, type check, format, and every structural gate the stack has**: `ruff`, `ruff format --check`,
   `mypy --strict` and **`lint-imports`** on the api; `cargo clippy --locked -- -D warnings`, `cargo fmt
   --check` on the core; `ng lint` and the strict `tsc` that `ng build` runs on the web; and `just contracts`
   for generated-contract freshness. Actual output, not "clean".
3. `git diff`, with the confirmation that **the test module is byte-identical** and the production change
   is confined to the scoped files. If the working tree carries changes that are not yours, account for
   them rather than assuming you made them.
4. **Every choice the pinned semantics did not make for you.**
5. **Anything you implemented that no test witnesses.**
6. **Anything stale or wrong you found** in the prompt, the tests or the canon.

**Evidence, not assertion.** Benchmarks of coding agents show models that build a reasonable thing and then
hallucinate their own inspection, so a report claiming green without the output will be re-run by the
reviewer, and the re-run is what counts.

## 8. Stop and report

> If a pinned semantic turns out to be wrong against the real code, or the prompt contradicts the
> foundation, `specs/PRD.md` or an ADR, **stop and report instead of improvising.** The canon wins.

**Language:** code, comments and any report you write are in **English**.
