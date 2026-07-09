---
name: weekly-review
description: Run a guided weekly review of an auxmem vault using graph gaps, open tasks, and recent logs. Use for weekly review, retrospective, or vault health check at week end.
---

# Weekly review

## Prepare

```bash
python3 .scripts/graph_report.py
python3 .scripts/synthesis_status.py
```

Read `72-tasks/todo.txt`, recent `71-log/` entries, and `80-moc/home-moc.md`.

## Review

1. **Tasks** — Triage open tasks: reprioritize `(A)`–`(Z)`, set `due:`, add `ref:` to relevant notes. Complete stale items or mark `+cancelled`.
2. **Decisions** — Scan `60-decisions/` and this week's meetings for decisions not yet recorded as ADRs.
3. **Gaps** — From `graph_report.py`: orphan notes, missing backlinks, tags without pages, synthesis queue/stale pages.
4. **Synthesis** — Flag pages with `review: needed` for human approval.

## Output

Create `71-log/YYYY-MM-DD-weekly-review.md` from `90-templates/weekly-review.md`:

- Decisions this week
- Findings and changes
- Open loops
- Next week

Set `updated:` today. Validate and commit.
