---
name: session-close
description: Close an auxmem vault agent session. Completes tasks, archives done items, appends a log entry, regenerates MOCs, validates, and commits. Use at session end or when the user asks to wrap up, close out, or finish a vault session.
---

# Session close

Run from the vault root.

## Checklist

```
- [ ] Update 72-tasks/todo.txt (complete in place)
- [ ] Move x lines to 72-tasks/done.txt
- [ ] Append 71-log/YYYY-MM-DD-session.md
- [ ] python3 .scripts/gen_mocs.py
- [ ] python3 .scripts/validate_vault.py --all
- [ ] git commit (normal commit, not --no-verify)
```

## Steps

1. **Tasks** — Complete open tasks in `72-tasks/todo.txt` in place (`x YYYY-MM-DD ...`). Never delete an open task; to drop one, complete with `+cancelled`. Move all `x` lines to `72-tasks/done.txt` (append-only). See AGENTS.md for todo.txt grammar.

2. **Log** — Append `71-log/<today>-session.md` (`type: log`, `domain` from config). Record: decisions made, facts learned, open loops. Full frontmatter required.

3. **MOCs** — `python3 .scripts/gen_mocs.py`

4. **Validate** — `python3 .scripts/validate_vault.py --all`. If failures remain, invoke the `fix-validation` skill.

5. **Commit** — Stage material changes. Use a descriptive message. Do not use `--no-verify`; the pre-commit hook is the quality gate.
