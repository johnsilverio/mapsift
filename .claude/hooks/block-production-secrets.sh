#!/usr/bin/env bash
# Blocks a credential or production data from entering this repository, in any form.
#
# C6 and foundation I7: no production credential and no production data in any non-production
# environment, ever. It is the one rule here whose violation cannot be undone by reverting a commit,
# because a secret that reaches a remote is permanent and external, and this project already has the
# scar: `claude mcp get` printed a live API key in clear into a transcript on 2026-08-03 and the
# revocation is still an open owner item in `specs/session-handoff.md`.
#
# What this adds over `.gitignore`, which already lists `.env`, `*.pem` and the rest. A `git add -f`
# walks straight past an ignore rule, and `.gitignore` says nothing at all about the CONTENT of a
# file with an innocent name. Those are the two gaps, and they are what this guards.
#
# PreToolUse on Bash|Write|Edit. Exit 2 blocks the call before it runs.
set -euo pipefail

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload")

# Paths that are a credential by their name alone, mirroring the secrets block of `.gitignore`.
# The `.example` templates are tracked on purpose, because a template with no real values is
# documentation, so they are excluded here the same way.
SECRET_PATH='(^|/)\.env($|\.)|\.pem$|\.p12$|(^|/)credentials\.json$|(^|/)service-account[^/]*\.json$'
EXAMPLE_PATH='\.example$'

# Live credential shapes, each requiring enough body that prose naming the prefix does not match.
# This canon has to be able to write about `lin_api_` without tripping its own guard.
SECRET_BODY='lin_api_[A-Za-z0-9]{40,}|gh[pousr]_[A-Za-z0-9]{36,}|sk-ant-[A-Za-z0-9_-]{24,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----'

deny() {
  cat >&2 <<EOF
Blocked: this puts a credential or production data into the repository, which C6 and foundation I7
forbid in any non-production environment, ever.

$1

A secret that reaches a remote is permanent and external; reverting the commit does not unsend it.
Rotate first and commit never. If this is a false positive, the owner lifts it deliberately rather
than the session working around it.
EOF
  exit 2
}

case "$tool" in
  Write|Edit)
    path=$(jq -r '.tool_input.file_path // empty' <<<"$payload")
    body=$(jq -r '.tool_input.content // .tool_input.new_string // empty' <<<"$payload")

    # Content first, and on any path: a key pasted into a markdown note is the shape this project
    # actually met, and a path check would never have seen it.
    if grep -qE "$SECRET_BODY" <<<"$body"; then
      deny "File: $path
Its content carries something shaped like a live credential.

If you are documenting the format rather than carrying a key, write the prefix without a body: this
guard requires enough characters after the prefix that a prefix alone never matches."
    fi
    ;;
  Bash)
    cmd=$(jq -r '.tool_input.command // empty' <<<"$payload")

    # Staging is the point of no return, so it is what is guarded rather than the write. A plain
    # `git add` of an ignored path is refused by git itself; `-f` is the hole this closes.
    #
    # `git add` is matched only at a COMMAND position, never anywhere in the text. The first version
    # of this line used a bare word match and blocked its own test suite, because a payload quoting
    # the string `git add -f infra/.env` is data rather than a command. A guard wider than its rule
    # gets switched off, which is worse than not having it.
    GIT_ADD='(^|[;&|]|^[[:space:]]*)[[:space:]]*git[[:space:]]+add\b'
    if grep -qE "$GIT_ADD" <<<"$cmd"; then
      if grep -qE "$SECRET_PATH" <<<"$cmd" && ! grep -qE "$EXAMPLE_PATH" <<<"$cmd"; then
        deny "Command: $cmd
It stages a path that is a credential by its name."
      fi

      # `dev-workflow` section 4: stage explicit paths, never `git add -A`. That rule has existed
      # with nothing enforcing it, and it is what turns an untracked secret sitting in the tree into
      # a staged one without anybody naming it.
      if grep -qE "${GIT_ADD%%\\b}[[:space:]]+(-A\b|--all\b|\.( |$))" <<<"$cmd"; then
        deny "Command: $cmd
It stages everything present rather than the paths you mean, which dev-workflow section 4 forbids
by name. Two untracked .env files live in this tree (infra/ and apps/api/), so a blanket stage is
one -f away from a committed credential."
      fi
    fi
    ;;
esac
exit 0
