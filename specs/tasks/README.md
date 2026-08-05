# The spec per task

> **What this folder is.** One file per Linear issue that needs one, at `MAP-<n>-<slug>.md`. It is where the
> authority chain ends: foundation, then PRD and `CLAUDE.md`, then the ADRs, then **this**, which is what a
> window actually reads to implement.
>
> **Authority.** It is the lowest tier and it wins over nothing. Where this file and a document it cites
> disagree, **the cited document wins and this file is the one that is wrong**.

---

## Why it exists rather than living in the prompt

A window needs the task **assembled**: which requirement, which invariants, which ADR sections, what is out
of scope, what the previous task already proved. That assembly used to live in the window prompt, and a
prompt is pasted into a chat and then gone. It made the most carefully constructed artifact in the loop the
only one not under version control, not reviewable as a diff, and not readable by the next person.

The identifier in the filename is the same one in the issue, the branch and the commit, and that is the whole
bridge between the tracker and the contract.

## The two rules that make it worth having

**It cites and never restates.** The entire value is that a window reads one file instead of five; the entire
risk is that the file becomes a fifth copy of four documents. A pointer says **where to read** and **under
what condition you go there**. "The geometry family rule is M2" is a pointer. "A layer's declared kind is a
contract on its features, so a geometry of another family is refused" is a second copy of M2 wearing a
citation, and it is the copy that will go stale.

**It is written at pickup, never at backlog creation.** Twenty task specs written at once go stale before
anybody reads them. The evidence is in this repository: the specs on disk are the ones that were worked.

## The shape

```markdown
# MAP-<n>: <the outcome, in one line>

## Trace
The requirement (a T, M, S, N or U item of the PRD), the invariants (I1 to I11), the constraints
(C1 to C14) and the ADR sections this task carries. Cited, never restated.

## What this task owns
The behaviour, as an outcome. If it needs an "and", it is two tasks.

## Out of scope
Named explicitly, with the owner of each deferred piece. This block is not politeness: a vague boundary
is the measured root cause of an agent doing work nobody asked for.

## Boundary decisions the owner closed
Only what was decided for this task, with the date. Each one also went into the document that owns it
before this file was written, per the fan-out rule; this is the pointer, not the record.

## Evidence handed over
What cost a measurement, a probe or an afternoon of diagnosis, with its date. This is the one thing that
is transcribed rather than cited, because it exists nowhere else yet. Anything here that turns out to be
general belongs in `specs/log.md` instead.

## Acceptance
Copied from the requirement, never invented. If you are writing new criteria here, the requirement is
soft, and the fix is to sharpen it in `specs/PRD.md` first.
```

## What a review fails this file for

A section that restates a decision instead of citing it. An acceptance criterion that appears here and
nowhere upstream. An enumeration of artifacts (a file list, an index, a column list) where the rule already
answers it, which is how a spec ends up asking for something the rule does not want. A boundary decision
recorded here and nowhere else, which means the fan-out never finished.
