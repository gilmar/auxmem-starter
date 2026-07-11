---
name: setup-domains
description: Tailor auxmem domain folders after creation or when reorganizing. Interviews the user, proposes domains, updates auxmem.config.json and folders, regenerates MOCs, validates, and commits. Use right after auxmem new, when restructuring subject areas, or when the user asks to set up or change auxmem domains.
---

# Setup domains

Run from the auxmem root. New auxmems start with **no subject domains** — only shared structural folders. This skill is the required first step after `auxmem new`: interview the user, propose domains, write the config, create folders, fix seed placeholders, validate, and commit.

## Interview

Ask what this auxmem is for: subject areas, active projects, teams, or stakeholders they track. If `seed-staging/` exists outside the auxmem or notes are already present, read them for signal.

Propose 3 to 6 domains as `NN-folder=slug`:

- Folders numbered in tens: `10-projects`, `20-governance`, ...
- Slugs lowercase, digits, hyphens only
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
6. `python3 .scripts/validate_auxmem.py --all`. Fix failures with the `fix-validation` skill.
7. Commit with a message describing the domain map.

## Rules

- `.scripts/auxmem.config.json` is the single source of truth; folders follow the config, not the reverse
- Never delete notes to match a domain change; move or re-tag them
- At least one domain is required
- Slugs must match the validator vocabulary; read valid options from the config if unsure
