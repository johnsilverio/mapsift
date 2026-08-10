#!/usr/bin/env bash
# Blocks an em dash, an en dash or a double hyphen in prose, in any markdown this repository owns.
# The rule is `.claude/skills/writing-for-agents/SKILL.md` and `specs/session-handoff.md`; MAP-40 is
# why it is a script.
#
# PostToolUse on Write|Edit. Exit 2 returns the message to the model.
#
# TRAP, and read it before "fixing" this to PreToolUse. PostToolUse is deliberate: an Edit's
# `new_string` is a FRAGMENT, so a fence or an inline span that opens outside it is undecidable, and
# a pre-write check on fragments false-positives on every flag inside a code block. The file on disk
# is the only text where the exclusions below are decidable. The cost is stated rather than hidden:
# the write lands and is handed back, so a turn that ends first leaves the violation on disk, and a
# markdown written through Bash is never seen at all. That is why the code-review Craft axis still
# reads prose in a diff.
set -euo pipefail

command -v jq >/dev/null || { echo "check-prose.sh requires jq" >&2; exit 2; }

path=$(jq -r '.tool_input.file_path // empty')
[[ -z "$path" ]] && exit 0
[[ "$path" != *.md ]] && exit 0
[[ ! -f "$path" ]] && exit 0

# The one exception in this canon, and it is written rather than assumed: `specs/index.md` and
# `specs/log.md` are flat catalogs whose one-line-per-entry format uses a dash as a structural
# separator (session-handoff header, Language note). Exempt whole, because narrowing it to the
# separator position would fail on every historical line the moment anybody appends.
case "${path#"${CLAUDE_PROJECT_DIR:-}/"}" in
  specs/log.md|specs/index.md) exit 0 ;;
esac

# Four things are not prose and are blanked before the check. Every pass PRESERVES THE LINE COUNT,
# because the reported line number is the whole value of the message: a fenced block (a diagram
# arrow is not punctuation), an inline span (which is what lets `--strict` be written about), an
# HTML comment, and a URL. The last two are why this once refused every edit to README.md, where a
# shields.io badge escapes a literal hyphen as `--` and collapsing it silently breaks the badge.
stripped=$(
  awk '/^[[:space:]]*```/{f=!f; print ""; next} {print (f ? "" : $0)}' "$path" |
  perl -0777 -pe 's/`([^`]*)`/"`" . ($1 =~ s{[^\n]}{}gr) . "`"/ge' |
  perl -0777 -pe 's{<!--.*?-->|\bhttps?://\S+}{$& =~ s/[^\n]//gr}ge'
)

fail() {
  printf '%s\n\n%s\n\n%s\n' "$1" "$2" \
"The rule is in .claude/skills/writing-for-agents/SKILL.md and specs/session-handoff.md: no em dash
and no double hyphen in prose, anywhere, including under .claude/. The en dash is swept with them.
Replace with a comma, a period, or two sentences. Fenced blocks, inline code, HTML comments and URLs
are already excluded, and specs/log.md and specs/index.md are exempt whole." >&2
  exit 2
}

if grep -qP '[\x{2014}\x{2013}]' <<<"$stripped"; then
  fail "Em dash or en dash found in prose in $path." "$(grep -nP '[\x{2014}\x{2013}]' <<<"$stripped" | head -5)"
fi

# The double hyphen half. Exactly two hyphens and never a longer run, because a thematic break, a
# table rule and a YAML fence are three or more and are structure. A bare --flag outside backticks is
# flagged on purpose: the convention in this tree is that a flag is code.
DOUBLE='(^|[^-])--([^-]|$)'
if grep -qE "$DOUBLE" <<<"$stripped"; then
  fail "Double hyphen found in prose in $path." "$(grep -nE "$DOUBLE" <<<"$stripped" | head -5)"
fi
exit 0
