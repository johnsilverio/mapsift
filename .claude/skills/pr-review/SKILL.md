---
name: pr-review
description: Review a pull request written by someone else, where you do not have the author's intent and did not see the session that produced it. Reconstructs what the change claims to do, checks the claim against the diff, judges it against the canon, and separates what blocks a merge from what is a request to the author. Use whenever the user gives a PR number or URL, mentions reviewing someone's code, or asks whether a contribution is safe to merge. Triggers on "/pr-review 123", "review PR 123", "review this contribution", "should we merge this". For your own diff from your own windows, use `code-review` instead, which can assume the canon was followed.
---

# Review someone else's pull request

**The defining difference from `code-review`: you do not have the author's context and you cannot assume
they had yours.** They did not read this canon, or read part of it, or read a version of it. Their agent's
session held reasoning you will never see. **So this review reconstructs intent before judging it**, and it
is explicit about what it could not know.

That cuts both ways, and getting it wrong in either direction is expensive. Treating an external change
like your own produces a review that quotes ADR sections at somebody who had no way to know they existed.
Treating it as untrusted produces a review that rejects good work over house style. **The line: what the
project documents is enforceable; what it merely prefers is a request.**

Volume is the other difference. An agent can produce a plausible pull request faster than a human can read
one, so the reviewer's time is now the scarce resource. Use the machine for triage, keep the judgement:
**the agent investigates, the maintainer decides.**

## 1. Fetch, and read the claim before the code

```bash
gh pr view <n>
gh pr diff <n>
gh pr checks <n>
git log <base>..<head> --oneline
```

**Read the description first and write down, in one sentence, what this claims to do.** That sentence is
what everything below is checked against, and forming it before reading the diff is what keeps the code
from talking you into its own version of the goal.

Then say which stack it touches. Since ADR-0001 section 1 this is one repository, so a change crossing the api and
the web is **one pull request** carrying the serializer, the regenerated schema, the regenerated types and
the component. **Reviewing half of that is reviewing half a contract.**

## 2. The five disqualifiers, checked before anything else

Each one is a blocker on its own, each is cheap to check, and each is a way a well-meaning contribution
does real damage:

1. **The description does not match the diff.** The single most important check on an external change, and
   the one a skimming reviewer misses. If the body describes something the code does not do, or the code
   does something the body never mentions, stop here and ask.
2. **A schema change with no migration.**
3. **A change to public behaviour with no test covering the compatibility.**
4. **A bulk addition nobody reviewed**, typically a large generated or vendored blob inside a change that
   claims to be small.
5. **A regression**: an existing test weakened, renamed or deleted. Diff the test files first and account
   for every assertion that left.

`gh pr checks` belongs here too. **CI is the machine gate, and a red one ends the review.**

## 3. Reconstruct the intent, and mark what you cannot know

Write down, explicitly:

- **What the change assumes** about the system that the author could not have verified.
- **What constraint they may have been under** that would explain a choice that looks wrong. An external
  author optimising for their own deployment is not making a mistake, they are solving a different problem.
- **What you cannot determine from the diff**, and say so in the review rather than guessing. "I cannot
  tell whether this path is reachable when X" is a useful review comment; a confident wrong claim is not.

**Then check the trace.** In this project an issue exists only when it traces to the canon and the trace is
cited (`CLAUDE.md` "Process & tracking"). For an internal contribution, a change that traces to nothing is the finding. **For an
external one, the absence of a trace is a question, not an accusation**: ask what it is fixing, because a
contribution addressing a real setup nobody here tested is valuable precisely because it came from outside.

## 4. Judge, in three severities

Read [`../code-review/references/canon-checks.md`](../code-review/references/canon-checks.md) for what a
violation of each invariant looks like in code. That file is shared and is not duplicated here.

**Blocks the merge.** An invariant, a structural rule, a disqualifier from section 2, a security or data
integrity problem, a backward incompatibility for anyone already running this. These are not negotiable
and the reason is that the cost lands on somebody who did not choose it.

**Should fix.** A missing test, a name that will confuse the next reader, a smell heavy enough to matter.
State the correction, not just the complaint.

**Worth noting.** A preference. **Say that it is a preference**, and let the author decline it. A reviewer
who cannot tell a preference from a rule trains contributors to ignore all of it.

Two things get extra weight on external code and almost none on your own:

- **New dependencies.** Every one walks the gate in `specs/dependencies.md`: maintenance health, licence,
  build scripts, weight, and whether it is compatible with what this project pins. A dependency arriving
  inside a feature pull request is a decision arriving without a decision record.
- **Data and credentials.** No production data, no fixture derived from the 1.0 dump, no secret, no
  hard-coded endpoint. This is permanent (foundation 9.1) and it does not care who wrote the diff.

## 5. Report

Group by what the author has to do, not by which axis found it: **blocks the merge**, **should fix**,
**worth noting**. Give `file:line`, the correction, and the rule where a rule exists.

Then close with the two things a maintainer actually needs:

- **What you did not examine and why.** A path with no test, an integration nobody ran, a claim you could
  not verify from the diff. **When a model says "here are all the bugs", it found some bugs, never all.**
- **What the canon has to absorb**, if the change is right and the documents do not describe it yet. That
  is a fan-out before the merge, not a follow-up after it.

**If the pull request is clean, say so plainly.** A reviewer prompted to find gaps will produce some even
when the work is sound, and chasing those buys defensive code and abstraction nobody needed. Manufacturing
findings to look thorough is how a review process loses its authority.
