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
#
# The same shape once more: it cannot tell command text from PROSE PASSED AS AN ARGUMENT, so writing
# about this rule inside a long `--body` trips it. Pass a long body through `--body-file`, which is
# the better shape too. Four false positives so far, all met while documenting the guard, and each
# mitigation turned out to be the thing that should have been done anyway.
set -euo pipefail

command -v jq >/dev/null || { echo "block-main-push.sh requires jq" >&2; exit 2; }

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload")
[[ "$tool" == "Bash" ]] || exit 0

cmd=$(jq -r '.tool_input.command // empty' <<<"$payload")

# `is_a_push` is the single definition of what this hook acts on, and both the segment loop and the
# branch check below consult it. They disagreed once: the loop was narrowed and the branch check was
# not, so `git add block-main-push.sh` on the default branch was refused by a check that never asked
# whether the command was a push at all.
is_a_push() {
  # Begins with the command, because a line merely quoting a push is data and this hook's own test
  # suite is a file full of exactly that.
  grep -qE '^[[:space:]]*(then|do|\{|\()?[[:space:]]*git([[:space:]]|$)' <<<"$1" || return 1
  # And `push` is a WHOLE TOKEN, because \bpush\b matches inside `block-main-push.sh`, which made
  # this very file unstageable.
  grep -qE '(^|[[:space:]])push([[:space:]]|$)' <<<"$1"
}

pushes=0
while IFS= read -r seg; do is_a_push "$seg" && pushes=1; done < <(tr '|&;' '\n' <<<"$cmd")
[[ "$pushes" == 1 ]] || exit 0

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
  is_a_push "$seg" || continue
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
