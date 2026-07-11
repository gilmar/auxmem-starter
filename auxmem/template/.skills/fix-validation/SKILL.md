---
name: fix-validation
description: Fix auxmem auxmem validation failures using the tiered protocol (auto, llm, human). Use when validate_auxmem.py fails, the pre-commit hook rejects a commit, or the user asks to fix auxmem validation errors.
---

# Fix validation failures

Do not weaken the gate. Fix notes until `python3 .scripts/validate_auxmem.py --all` passes.

## Diagnose

```bash
python3 .scripts/validate_auxmem.py --json --all
```

Work errors in `fixable` order: `auto`, then `llm`, then `human`.

## Tier 1: auto

Mechanical fixes only (dates, tag/tags, zero-padding):

```bash
python3 .scripts/validate_auxmem.py --fix --all
```

Re-run `--json --all` to confirm remaining errors.

## Tier 2: llm

Draft fixes grounded in the note's own content. Get human acceptance before committing:

- **summary** too short — draft from body; front-load concrete nouns
- **title** missing — propose from heading or filename
- **sources** empty on synthesized page — list only sources the page visibly draws on

## Tier 3: human

Ask; never guess:

- **type** or **domain** not in vocabulary — offer valid options from `.scripts/auxmem.config.json`
- **sources** path unresolved — ask if renamed, moved, or never added
- **wikilink** with ambiguous target — ask before converting

Full protocol: `docs/FIXING.md`
