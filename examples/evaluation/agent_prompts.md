# Agent evaluation prompts (AUX-012)

Use the same prompt set for each provider (Claude Code, Codex CLI, Gemini CLI, Cursor). Point the agent at one reference auxmem root. Do not modify files unless the prompt says to.

Record provider name, version, date, and auxmem path with each run.

## P1 — Recover project state

> Read this auxmem and summarize the current project state in five bullets. Cite the file path for each bullet.

**Expected signals:** mentions active ADR-0002, open tasks, stale synthesis or review queue, unresolved contradiction.

## P2 — Latest accepted decision

> What is the latest **accepted** architecture/process decision? Give the ADR id, title, and file path.

**Expected:** ADR-0002 (wording varies by example), not the superseded ADR-0001.

## P3 — Superseded vs current

> Which decision did ADR-0002 replace, and what changed? Cite both ADR files.

**Expected:** ADR-0001 marked superseded; explicit supersedes link.

## P4 — Unresolved tasks

> List open tasks from `72-tasks/todo.txt` and any related note paths referenced there.

## P5 — Meeting preparation

> A steering/lab/architecture meeting is tomorrow. What open contradictions and stale syntheses should be on the agenda? Cite sources.

**Expected:** cites `synthesis_status.py` output or equivalent files; names contradiction without picking a winner.

## P6 — Contradictory sources

> Describe the unresolved contradiction between the captured sources. Do not resolve it — show both claims and their files.

## P7 — Evidence citations

> Answer: "What claims are disputed in this auxmem?" Every claim must include a supporting file path.

## P8 — Provider switch

> Continue from a prior summary using only files in this auxmem. (Run P1–P3 on a second provider on the same auxmem, then ask this on the second provider with the first provider's answer pasted in context.)

**Measures:** portability of the file-backed record across providers.

Scoring: see [`scoring_rubric.md`](scoring_rubric.md).
