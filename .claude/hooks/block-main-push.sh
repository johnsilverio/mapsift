#!/usr/bin/env bash
# Blocks a direct push touching main. Branch and pull request always; main never receives a direct
# push (`dev-workflow` section 5, ADR-0008 section 4).
#
# Why this exists even though the ruleset is real. Measured 2026-08-10, this repository's ruleset is
# active with conditions `include: ["~DEFAULT_BRANCH"]`, so `non_fast_forward` and the pull-request
# requirement do cover main on the server. Two things it still buys. It fails at the call rather
# than at the remote, so the session learns before it has written a push it has to reason about.
# And the ruleset's enforcement is conditional on this repository staying public on a free plan,
# which `specs/session-handoff.md` records as a caveat that outlives the item: making it private
# silently stops the wall, and silently is the word that matters.
#
# Honest limit: it covers sessions running this toolkit, not a bare terminal.
#
# PreToolUse on Bash. Exit 2 blocks the call before it runs.
set -euo pipefail

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload")
[[ "$tool" == "Bash" ]] || exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$payload")
grep -qE '\bgit\b[^|&;]*\bpush\b' <<<"$cmd" || exit 0

deny() {
  cat >&2 <<EOF
Blocked: direct push touching main. Branch and pull request always; main never receives a
direct push (dev-workflow section 5, ADR-0008 section 4).

$1

Create the branch from the Linear issue and push that. If this is a false positive, the owner
lifts it deliberately rather than the session working around it.
EOF
  exit 2
}

# A push naming main as a refspec is refused outright. \bmain\b also matches a branch such as
# feature/main-page: that false positive is accepted, fail closed.
if grep -qE '\bmain\b' <<<"$cmd"; then
  deny "Command: $cmd
It names main."
fi

# A push with no refspec pushes the current branch, so any push while main is checked out is
# refused, including one that names another ref. Fail closed.
branch=$(git -C "${CLAUDE_PROJECT_DIR:-.}" branch --show-current 2>/dev/null || true)
if [[ "$branch" == "main" ]]; then
  deny "Command: $cmd
The current branch is main, so this pushes main."
fi

exit 0
