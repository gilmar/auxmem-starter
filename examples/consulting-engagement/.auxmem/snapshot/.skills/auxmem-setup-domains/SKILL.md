---
name: auxmem-setup-domains
description: Tailor or reorganize auxmem domain folders. Interviews the user, proposes domains, updates auxmem.config.json and folders, regenerates MOCs, validates, and commits. Use when restructuring subject areas, changing the domain map, or when invoked by auxmem-init for new auxmems without pre-set domains.
---

# Setup domains

Run from the auxmem root. New auxmems reach this workflow via `auxmem-init`. Use directly when reorganizing subject areas or changing the domain map after init.

## Interview

Ask what this auxmem is for: subject areas, active projects, teams, or stakeholders they track. If `seed-staging/` exists outside the auxmem or notes are already present, read them for signal.

Propose 3 to 6 domains as `NN-folder=slug`:

- Folder keys numbered in tens (`10-…`, `20-…`, …); slugs lowercase, digits, hyphens only
- First domain is primary (used in ADR-0001, initial tasks, seed content)
- One sentence of rationale per domain

Present the full map. Get explicit approval before changing anything. Do not guess domain names or slugs.

## Apply

1. Edit `domains` in `.scripts/auxmem.config.json`. Preserve other config keys.
2. For each removed domain folder:
   - Empty: delete the folder
   - Has notes: `git mv` into the best-fit new folder and update each note's `domain:` frontmatter
3. If the primary domain slug changed, or placeholders remain, update `__PRIMARY_DOMAIN__` in:
   - `60-decisions/adr-0001-auxmem-structure.md`
   - `60-decisions/index.md`
   - `72-tasks/todo.txt`
4. `./bootstrap.sh` (creates new domain folders, idempotent)
5. `python3 .scripts/gen_mocs.py`
6. `python3 .scripts/validate_auxmem.py --all`. Fix failures with the `auxmem-fix-validation` skill.
7. Commit with a message describing the domain map.

## Rules

- `.scripts/auxmem.config.json` is the single source of truth; folders follow the config, not the reverse
- Never delete notes to match a domain change; move or re-tag them
- At least one domain is required
- Slugs must match the validator vocabulary; read valid options from the config if unsure
