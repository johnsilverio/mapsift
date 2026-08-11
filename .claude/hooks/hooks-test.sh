#!/usr/bin/env bash
# Trips every hook deliberately. Run it: bash .claude/hooks/hooks-test.sh
#
# ADR-0002 section 5, addition of 2026-08-10: a hook is proven by a committed suite that trips it,
# never by prose. The first three hooks shipped without this and carried five real defects that
# twenty minutes of adversarial probing found. Every one of those five has a case below, marked
# REGRESSION, and each is a case that PASSED before the fix and would pass again if somebody widened
# the guard back.
#
# Payloads live in files rather than on a command line, because the guards read command text and a
# payload quoting a forbidden string is data. Learning that cost one round.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
export CLAUDE_PROJECT_DIR="$PWD"

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0

# Two repositories with a known checked-out branch, because the branch is an INPUT to
# block-main-push.sh. Never use $PWD for these: the suite then passes or fails depending on which
# branch the reader happens to have checked out, which is how a suite starts lying. Found by running
# it from main after it had been written from a feature branch.
ON_MAIN="$T/on-main"
git init -q -b main "$ON_MAIN" && git -C "$ON_MAIN" commit -q --allow-empty -m x
ON_BRANCH="$T/on-branch"
git init -q -b js/x "$ON_BRANCH" && git -C "$ON_BRANCH" commit -q --allow-empty -m x

check() { # hook payload-json expected label
  printf '%s' "$2" > "$T/payload"
  local got out
  out=$(".claude/hooks/$1" < "$T/payload" 2>&1); got=$?
  if [[ "$got" == "$3" ]]; then
    pass=$((pass+1)); printf '  ok   %s\n' "$4"
  else
    fail=$((fail+1)); printf '  FAIL %s (expected %s, got %s)\n       %s\n' "$4" "$3" "$got" "${out%%$'\n'*}"
  fi
}

md() { printf '%b' "$2" > "$T/$1.md"; printf '{"tool_input":{"file_path":"%s/%s.md"}}' "$T" "$1"; }
bash_at() { printf '{"tool_name":"Bash","cwd":"%s","tool_input":{"command":%s}}' "$1" "$(printf '%s' "$2" | jq -Rs .)"; }
write_of() { printf '{"tool_name":"Write","tool_input":{"file_path":"/tmp/x.md","content":%s}}' "$(printf '%s' "$1" | jq -Rs .)"; }

echo "check-prose.sh"
check check-prose.sh "$(md a 'An em dash \xe2\x80\x94 here.\n')" 2 "em dash in prose"
check check-prose.sh "$(md b 'An en dash \xe2\x80\x93 here.\n')" 2 "en dash in prose"
check check-prose.sh "$(md c 'A double hyphen -- here.\n')" 2 "double hyphen in prose"
check check-prose.sh "$(md d 'Clean prose, one sentence.\n')" 0 "clean prose"
check check-prose.sh "$(md e 'Fine.\n\n\`\`\`\nflag --strict and \xe2\x80\x94 too\n\`\`\`\n')" 0 "both inside a fenced block"
check check-prose.sh "$(md f 'Run \`mypy --strict .\` now.\n')" 0 "a flag inside an inline span"
check check-prose.sh "$(md g 'Run \`ruff format\n--check .\` now.\n')" 0 "REGRESSION: span broken across two lines"
check check-prose.sh "$(md h 'One.\n\n---\n\nTwo.\n')" 0 "a thematic break is structure"
check check-prose.sh "$(md i '<img src="https://img.shields.io/badge/status-pre--implementation-orange" alt="s">\n')" 0 "REGRESSION: a shields.io escaped hyphen in a URL"
check check-prose.sh "$(md j '<!-- a placeholder -->\n\nText.\n')" 0 "REGRESSION: an HTML comment"
check check-prose.sh '{"tool_input":{"file_path":"/tmp/not-markdown.txt"}}' 0 "a file that is not markdown"
check check-prose.sh "{\"tool_input\":{\"file_path\":\"$PWD/specs/log.md\"}}" 0 "specs/log.md is exempt whole"

# REGRESSION: the awk pass once dropped fenced lines instead of blanking them, so every reported
# line number after the first fence was short by the size of every fence above it.
printf 'Text.\n\n```\na\nb\nc\n```\n\nAn em dash \xe2\x80\x94 here.\n' > "$T/k.md"
reported=$(".claude/hooks/check-prose.sh" <<<"{\"tool_input\":{\"file_path\":\"$T/k.md\"}}" 2>&1 | grep -oE '^9:' || true)
if [[ "$reported" == "9:" ]]; then pass=$((pass+1)); printf '  ok   %s\n' "REGRESSION: the reported line number survives a fence"
else fail=$((fail+1)); printf '  FAIL %s (the violation is on line 9)\n' "REGRESSION: the reported line number survives a fence"; fi

echo "block-main-push.sh"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git push origin main')" 2 "a push naming main"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git push origin HEAD:refs/heads/main')" 2 "a push naming main through a full ref"
check block-main-push.sh "$(bash_at "$ON_MAIN" 'git push')" 2 "a bare push while main is checked out"
check block-main-push.sh "$(bash_at "$ON_MAIN" 'git push origin js/foo')" 2 "any push while main is checked out"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git rebase origin/main && git push --force-with-lease origin js/x')" 0 "REGRESSION: the recovery dev-workflow section 5 prescribes"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git push -u origin js/foo && gh pr create --base main --title x')" 0 "REGRESSION: a push beside a command naming main"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git status')" 0 "not a push at all"
check block-main-push.sh "$(bash_at "$ON_BRANCH" "sed -i s/x/y/ f  # a file quoting 'git push origin main' as data")" 0 "REGRESSION: a command carrying the string as data"
check block-main-push.sh "$(bash_at "$ON_MAIN" 'git add .claude/hooks/block-main-push.sh')" 0 "REGRESSION: staging a file whose NAME carries both words"
check block-main-push.sh "$(bash_at "$ON_BRANCH" 'git -C /tmp/r push origin main')" 2 "a push behind a global option still names main"
check block-main-push.sh "$(bash_at "$T/gone" 'git push origin js/foo')" 2 "an unreadable branch fails closed"

echo "block-production-secrets.sh"
KEY="lin_api_$(printf 'A%.0s' $(seq 1 44))"
check block-production-secrets.sh "$(write_of "key is $KEY here")" 2 "a live-shaped key in written content"
check block-production-secrets.sh "$(write_of 'the lin_api_ prefix is the Linear shape')" 0 "the bare prefix in prose"
check block-production-secrets.sh "$(bash_at "$PWD" 'git add -A')" 2 "git add -A"
check block-production-secrets.sh "$(bash_at "$PWD" 'if true; then git add -A; fi')" 2 "REGRESSION: git add -A after a shell keyword"
check block-production-secrets.sh "$(bash_at "$PWD" 'git add -f infra/.env')" 2 "git add -f on a gitignored secret"
check block-production-secrets.sh "$(bash_at "$PWD" 'git add infra/.env apps/api/.env.example')" 2 "REGRESSION: one exempt token must not pardon a live one"
check block-production-secrets.sh "$(bash_at "$PWD" 'git add infra/.env.example && echo done')" 0 "REGRESSION: trailing text must not cancel the exemption"
check block-production-secrets.sh "$(bash_at "$PWD" 'git add specs/log.md specs/index.md')" 0 "explicit ordinary paths"
check block-production-secrets.sh "$(bash_at "$PWD" "echo 'a doc mentioning git add -f infra/.env'")" 0 "a command that only mentions the string"

printf '\n%s passed, %s failed\n' "$pass" "$fail"
exit $((fail > 0))
