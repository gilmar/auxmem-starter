---
name: todo
description: Manage auxmem vault tasks in 72-tasks/todo.txt and done.txt using the todo.txt grammar. Use when adding, completing, prioritizing, or archiving vault tasks.
---

# Todo management

Open tasks: `72-tasks/todo.txt`. Archive: `72-tasks/done.txt`. One task per line, no blank lines.

## Open task format

```
(A) 2026-07-04 Description +project @context due:YYYY-MM-DD ref:path.md
```

- `(A)` optional priority (single uppercase letter), first
- Creation date when creating
- `+project` uses domain slugs from `.scripts/vault.config.json`
- `@context`, `due:`, `ref:` optional

## Complete a task

In place in `todo.txt`:

```
x 2026-07-05 2026-07-04 Description +project pri:A
```

Lowercase `x`, completion date, creation date, preserve original priority as `pri:A`.

## Write rules

- Append new tasks at end of `todo.txt`
- Complete in place; never delete an open task
- To drop a task, complete with `+cancelled`
- At session close, move `x` lines to `done.txt` (append-only)
- After edits: `python3 .scripts/validate_vault.py --all` (validator enforces grammar)

For full session wrap-up, use the `session-close` skill.
