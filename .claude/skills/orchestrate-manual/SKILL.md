---
name: orchestrate-manual
description: Open an orchestrator session in manual dispatch mode, where the owner opens Windows A and B by hand and the orchestrator only writes the prompts and reviews what comes back. Use when the task is still being understood, when you want to watch a window work, or when a prompt needs editing before it runs. Triggers on "/orchestrate-manual", "orquestração manual", "manual mode", "eu abro as janelas".
disable-model-invocation: true
allowed-tools: Bash(git *), Bash(ls *), Bash(sed *), Bash(wc *), Bash(head *), Bash(grep *)
---

# Orchestrator boot, manual dispatch

**This is `orchestrate` with one thing changed: who opens the window.** Everything else is identical and
none of it is repeated here, because a second copy of the role, the rules and the register is a second copy
that drifts.

## The whole of it, injected

!`sed -n '/^# Orchestrator boot/,$p' .claude/skills/orchestrate/SKILL.md`

---

## What this mode overrides, and it is only this

**You do not dispatch.** You hand the owner the prompt and stop. Read the "Dispatching a window" section
above for the prompt's shape and its three harness facts, and then **do not run it**: the owner pastes it
into a clean window, runs it, and brings the report back.

**The review is unchanged and so is its instrument.** You still run the machine gates yourself, still run
`code-review` over a green build, still refuse to approve on a window's own report, and Window B's prompt
still does not exist until Window A's result has been reviewed. **The three judgement axes still run as
three parallel subagents**, because that isolation is about the review and not about the dispatch.

## When this mode is the right one

Three cases beyond the condition the injected section above already states, each a real one rather than a
preference. **A prompt that needs editing before it runs**,
which happens when the orchestrator and the owner disagree about scope. **A task whose canon reading is
itself in doubt**, where watching which documents the window opens is the finding. And **anything the owner
wants to comb through**, which needs no justification.

## What this mode is not

**It is not the safe mode.** Both modes run the same prompt, the same skills and the same gates, and since
2026-08-10 both run under the same enforcement layer in `.claude/hooks/` (MAP-40). The difference is
observation, not protection.

**It is not the older mode kept for compatibility.** ADR-0008 section 4 names both, and the condition that
selects this one is written there.
