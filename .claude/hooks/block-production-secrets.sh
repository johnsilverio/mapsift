#!/usr/bin/env bash
# Blocks a credential or production data from entering this repository, in any form.
# C6 and foundation I7; the incident that motivated it is in `specs/session-handoff.md`.
#
# What this adds over `.gitignore`, which already lists `.env`, `*.pem` and the rest: `git add -f`
# walks straight past an ignore rule, and `.gitignore` says nothing about the CONTENT of a file with
# an innocent name. Those are the two gaps.
#
# PreToolUse on Bash|Write|Edit. Exit 2 blocks the call before it runs.
set -euo pipefail

command -v jq >/dev/null || { echo "block-production-secrets.sh requires jq" >&2; exit 2; }

payload=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$payload")

# Paths that are a credential by their name alone, mirroring the secrets block of `.gitignore`.
SECRET_PATH='(^|/)\.env($|\.)|\.pem$|\.p12$|(^|/)credentials\.json$|(^|/)service-account[^/]*\.json$'

# Live credential shapes, each requiring enough body that prose naming the prefix does not match.
# This canon has to be able to write about `lin_api_` without tripping its own guard.
SECRET_BODY='lin_api_[A-Za-z0-9]{40,}|gh[pousr]_[A-Za-z0-9]{36,}|sk-ant-[A-Za-z0-9_-]{24,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----'

# TRAP: `git add` is matched at a COMMAND POSITION, never anywhere in the text. The first version
# used a bare word match and blocked its own test suite, because a payload quoting the string is
# data rather than a command. The alternatives cover the separators plus the shell keywords, because
# `if true; then git add -A; fi` is a command position too.
GIT_ADD_HEAD='(^|[;&|(){]|\bthen\b|\bdo\b)[[:space:]]*git[[:space:]]+add'

deny() {
  cat >&2 <<EOF
Blocked: this puts a credential or production data into the repository, which C6 and foundation I7
forbid in any non-production environment, ever.

$1

A secret that reaches a remote is permanent and external; reverting the commit does not unsend it.
Rotate first and commit never.
EOF
  exit 2
}

case "$tool" in
  Write|Edit)
    path=$(jq -r '.tool_input.file_path // empty' <<<"$payload")
    body=$(jq -r '.tool_input.content // .tool_input.new_string // empty' <<<"$payload")

    # Content, on any path: a key pasted into a markdown note is the shape this project actually
    # met, and a path check would never have seen it. Writing `infra/.env` locally is legitimate, so
    # the path is guarded at the stage instead.
    if grep -qE "$SECRET_BODY" <<<"$body"; then
      deny "File: $path
Its content carries something shaped like a live credential.

If you are documenting the format rather than carrying a key, write the prefix without a body: this
guard requires enough characters after the prefix that a prefix alone never matches."
    fi
    ;;
  Bash)
    cmd=$(jq -r '.tool_input.command // empty' <<<"$payload")

    if grep -qE "${GIT_ADD_HEAD}\b" <<<"$cmd"; then
      # TRAP: PER TOKEN and never per line. The first version anchored the `.example` exemption to
      # the end of the whole command, so `git add infra/.env apps/api/.env.example` staged a live
      # secret and `git add infra/.env.example && echo done` was refused. Same two paths, opposite
      # verdicts by argument order.
      read -ra words <<<"$cmd"
      for w in "${words[@]}"; do
        [[ "$w" == *.example ]] && continue
        if grep -qE "$SECRET_PATH" <<<"$w"; then
          deny "Command: $cmd
It stages $w, a path that is a credential by its name."
        fi
      done

      # `dev-workflow` section 4: stage explicit paths, never `git add -A`. That rule existed with
      # nothing enforcing it, and it is what turns an untracked secret into a staged one without
      # anybody naming it.
      if grep -qE "${GIT_ADD_HEAD}[[:space:]]+(-A\b|--all\b|\.( |$))" <<<"$cmd"; then
        deny "Command: $cmd
It stages everything present rather than the paths you mean, which dev-workflow section 4 forbids
by name. Two untracked .env files live in this tree (infra/ and apps/api/), so a blanket stage is
one -f away from a committed credential."
      fi
    fi
    ;;
esac
exit 0
