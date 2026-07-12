---
name: auxmem-init
description: First-run onboarding after auxmem new — orient the user, set up domains, optionally seed or import content, configure git remote, validate, and commit. Use when initializing a new auxmem or when the user asks to finish setup.
---

# Auxmem init

Run from the auxmem root. This is the **first agent step** after `auxmem new`. It orchestrates setup; specialized skills handle individual workflows.

## 1. Orient

Run the AGENTS.md session bootstrap:

1. Read `AGENTS.md`
2. If domains exist in config, read `80-moc/home-moc.md`
3. Read `72-tasks/todo.txt`
4. Read the two most recent entries in `71-log/` (if any)

Brief the user: what this auxmem is for, what init will cover (domains, optional content, git remote), and that ongoing work uses other `auxmem-*` skills.

## 2. Domains

Read `domains` from `.scripts/auxmem.config.json`.

**Empty domains** (default wizard path): invoke the full `auxmem-setup-domains` skill — interview, propose map, apply, validate, commit. Do not duplicate those steps here.

**Pre-set domains** (`auxmem new --domain` path): present the current folder→slug map. Ask the user to confirm or request changes. If changes are needed, invoke `auxmem-setup-domains`; if confirmed, continue.

## 3. Optional content

Check for a staging corpus:

- Look for `seed-staging/` as a sibling of the auxmem root or at a path the user provides
- If present and non-empty, offer to distill. On acceptance, invoke `auxmem-distill-seeds`
- If no staging corpus, mention alternatives:
  - `auxmem seed <export.json> --staging ./seed-staging` then re-run init or invoke `auxmem-distill-seeds`
  - `auxmem import-obsidian <vault> --dest <this-auxmem>` for Obsidian migration
  - See `docs/IMPORTING.md` (starter docs) for full import guidance

Do not run seeding or import unless the user agrees.

## 4. Git remote (optional)

Ask whether to connect a private git remote. If yes, provide commands for the user to run with their URL:

```bash
git remote add origin <url>
git add -A && git commit -m "initial auxmem" && git push -u origin main
```

Never invent repository URLs.

## 5. Wrap up

1. `python3 .scripts/validate_auxmem.py --all`. On failure, invoke `auxmem-fix-validation`
2. Append `71-log/<today>-auxmem-init.md` (`type: log`, valid `domain` from config):
   - Domain map chosen
   - Seed/import decisions
   - Git remote status
   - Open loops
3. Commit with a descriptive message (normal commit, not `--no-verify`)
4. Hand off ongoing workflows: `auxmem-session-close` at session end, `auxmem-new-note` for notes, `auxmem-setup-domains` when reorganizing domains later
