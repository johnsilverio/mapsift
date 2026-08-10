#!/usr/bin/env bash
# Blocks an em dash, an en dash or a double hyphen in prose, in any markdown this repository owns.
#
# Why a hook and not a rule: `CLAUDE.md` and four other documents have forbidden these since the
# first commit, and `.claude/skills/README.md` recorded the absence of this file as "a known gap
# rather than a decision". A prose rule is a request that a long session drops; this is the
# enforcement half, and it is the layer that covers a dispatched subagent nobody is watching.
#
# PostToolUse on Write|Edit. Exit 2 blocks the turn and returns the message to the model.
set -euo pipefail

path=$(jq -r '.tool_input.file_path // empty')
[[ -z "$path" ]] && exit 0
[[ "$path" != *.md ]] && exit 0
[[ ! -f "$path" ]] && exit 0

# The one exception in this canon, and it is written rather than assumed: `specs/index.md` and
# `specs/log.md` are flat catalogs whose one-line-per-entry format uses a dash as a structural
# separator between an identifier and its description (session-handoff header, Language note).
# That is tabular punctuation and it stays, so the two files are exempt whole. Narrowing this to
# the separator position would fail on every historical version line the moment anybody appends.
case "${path#"$CLAUDE_PROJECT_DIR/"}" in
  specs/log.md|specs/index.md) exit 0 ;;
esac

# Fenced blocks are not prose: a diagram arrow and a shell flag are not punctuation. Inline spans
# are stripped for the same reason, which is what lets `--strict` be written about.
#
# The inline strip is a whole-file pass rather than a line pass, and that is a deliberate departure
# from the version this was adapted from: that one scans line by line, so a code span whose closing
# backtick lands on the next line reads as prose and false-positives. The replacement keeps the
# span's newlines so the reported line numbers stay true.
stripped=$(
  awk '/^[[:space:]]*```/{f=!f; next} !f' "$path" |
  perl -0777 -pe 's/`([^`]*)`/"`" . ($1 =~ s{[^\n]}{}gr) . "`"/ge'
)

fail() {
  printf '%s\n\n%s\n\n%s\n' "$1" "$2" \
"CLAUDE.md forbids all three, everywhere, including under .claude/. Replace with a comma, a period,
or two sentences. A CLI flag such as --strict is a flag and an arrow inside a fenced block is not
prose; both are already excluded, as is anything inside inline code. specs/log.md and
specs/index.md are exempt whole, by the exception written in the session-handoff header." >&2
  exit 2
}

if grep -qP '[\x{2014}\x{2013}]' <<<"$stripped"; then
  fail "Em dash or en dash found in prose in $path." "$(grep -nP '[\x{2014}\x{2013}]' <<<"$stripped" | head -5)"
fi

# The double hyphen half of the same rule. The pattern matches exactly two hyphens and never a
# longer run, because a thematic break, a table rule and a YAML fence are three or more and are
# structure rather than prose. A bare --flag written outside backticks is flagged on purpose: the
# convention in this tree is that a flag is code.
DOUBLE='(^|[^-])--([^-]|$)'
if grep -qE "$DOUBLE" <<<"$stripped"; then
  fail "Double hyphen found in prose in $path." "$(grep -nE "$DOUBLE" <<<"$stripped" | head -5)"
fi
exit 0
