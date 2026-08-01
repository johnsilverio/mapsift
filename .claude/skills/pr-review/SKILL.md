---
name: pr-review
description: Review a pull request against the Mapsift standards. Use when the user wants a PR reviewed, code quality checked, or structured feedback on changes. Accepts a PR number or URL. Triggers on requests like "review PR 123", "check this pull request", "/pr-review 123".
---

# PR review

Review the pull request the user named (number or URL).

## 1. Get the PR

```bash
gh pr view <PR>
gh pr diff <PR>
gh pr checks <PR>
```

If the required checks are red, say so first: a review of a change that does not pass its own gate starts
with that fact.

## 2. Use the project's review standards

`.claude/agents/code-reviewer.md` holds the full polyglot checklist and the architecture invariants; for a
diff that is mostly Angular, `.claude/agents/angular-reviewer.md` is the sharper pass. Both are read-only.
The path-scoped rules in `.claude/rules/` carry the per-language detail.

## 3. Apply the checklist to every changed file

Per language touched:

- **Python** (`apps/api`): complete type hints, no `Any` without a justifying comment, Pydantic at every
  boundary, thin routers with the decision in a pure function, no N+1, no domain rule welded to a model.
- **Rust** (`libs/core`): serializable boundary with no live references, no `unwrap` on a recoverable path,
  the conflict rule small and deterministic.
- **Angular** (`apps/web`, `libs/ui`): TypeScript strict with no `any`, signals and `input()`/`output()`,
  OnPush, native control flow, generated API types, design tokens instead of literals, no client logic that
  belongs in the core.

Across all of them, the invariants are Critical when broken: tenant isolation keyed on the **tenant** and
enforced in the database (C4), preserve-not-discard for legal-weight geometry (C7), the conflict rule's two
golden-tested runtimes with the server holding authority (C10), the serializable boundary (C11), idempotency
and the mutation-number cursor (C12), proved authorship (C13), gated agent writes (C14), and no metric
computed in degrees (PRD M5).

Also check: tests cover the new behaviour and assert behaviour rather than implementation; generated files
were regenerated and not hand-edited; nothing was created under a path ADR-0001 section 8 forbids for now;
and no secret, token or credential appears in the diff.

## 4. Give structured feedback

- **Critical**: must fix before merge (a broken invariant, a security hole, a type-safety hole).
- **Warning**: should fix (convention, performance, duplication).
- **Suggestion**: worth considering.

Every finding cites `file:line`, the rule it breaks, and the concrete fix. No vague "consider improving".
Commend the genuinely good patterns too, so the review reinforces them.

## 5. Post it

```bash
gh pr comment <PR> --body-file <file>
```

Do not add any AI attribution trailer to the comment.
