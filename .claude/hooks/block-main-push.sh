#!/usr/bin/env bash
# Blocks a direct push touching main (`dev-workflow` section 5, ADR-0008 section 4).
# Why it exists beside the server ruleset: MAP-40, and `specs/log.md` under 2026-08-10.
#
# PreToolUse on Bash. Exit 2 blocks the call before it runs.
#
# Honest limits, three of them. It covers sessions running this toolkit and not a bare terminal. It
# reads the command text literally, so `git $P` with `P=push` defeats it: this is a guardrail
# against a mistake, never a wall against intent. And it reads the branch at PreToolUse, BEFORE the
# command runs, so `git switch -c js/x && ... && git push` is refused while main is checked out even
# though the push would not have touched main. That one is left standing rather than solved: the fix
# would mean predicting the command's effect on the branch, and a guard that predicts is the next
# false positive. Split the switch from the push, which is a better shape anyway.
set -euo pipefail

command -v jq >/dev/null || { echo "block-main-push.sh requires jq" >&2; exit 2; }

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload")
[[ "$tool" == "Bash" ]] || exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$payload")
grep -qE '\bgit\b.*\bpush\b' <<<"$cmd" || exit 0

deny() {
  cat >&2 <<EOF
Blocked: direct push touching main. Branch and pull request always; main never receives a
direct push (dev-workflow section 5, ADR-0008 section 4).

$1

Create the branch from the Linear issue and push that.
EOF
  exit 2
}

# TRAP: the test is PER SEGMENT and never over the whole command line. The first version matched
# \bmain\b anywhere, which refused `git rebase origin/main && git push --force-with-lease origin
# js/x`, the exact recovery `dev-workflow` section 5 prescribes when main moves under an open pull
# request. A guard that blocks the ordinary rebase day gets switched off, which is worse than not
# having it.
while IFS= read -r seg; do
  # The segment must BEGIN with the command, after optional whitespace and a shell keyword. A line
  # that merely contains `git push origin main` inside quotes is data, and this suite is itself a
  # file full of exactly that, which is how the narrowing was found for the third time.
  grep -qE '^[[:space:]]*(then|do|\{|\()?[[:space:]]*git[[:space:]].*\bpush\b' <<<"$seg" || continue
  # \bmain\b also matches a branch such as feature/main-page. That false positive is accepted
  # because it is rare and loud, unlike the one above.
  if grep -qE '\bmain\b' <<<"$seg"; then
    deny "Command: $cmd
The segment \"$seg\" names main."
  fi
done < <(tr '|&;' '\n' <<<"$cmd")

# A push with no refspec pushes the current branch, so any push while main is checked out is
# refused. The directory is the CALL's, not the project root: ADR-0008 section 8 puts parallel work
# in worktrees, so the branch that matters is routinely not the one at CLAUDE_PROJECT_DIR. An
# unreadable branch is a refusal rather than a pass, which is what "fail closed" has to mean.
dir=$(jq -r '.cwd // empty' <<<"$payload")
branch=$(git -C "${dir:-${CLAUDE_PROJECT_DIR:-.}}" branch --show-current 2>/dev/null || true)
if [[ -z "$branch" ]]; then
  deny "Command: $cmd
The current branch could not be read at ${dir:-${CLAUDE_PROJECT_DIR:-.}}, so this cannot be shown
not to push main."
fi
if [[ "$branch" == "main" ]]; then
  deny "Command: $cmd
The current branch is main, so this pushes main."
fi

exit 0
