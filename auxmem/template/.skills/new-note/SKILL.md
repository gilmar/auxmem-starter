---
name: new-note
description: Create a new auxmem note from 90-templates with correct frontmatter and domain. Use when adding a project doc, meeting note, stakeholder profile, reference, or any new auxmem note.
---

# New note

## Steps

1. **Pick template** — Copy from `90-templates/` matching the note type:
   - `project-doc`, `governance-finding`, `meeting`, `1on1`, `stakeholder`, `exec-doc`, `source`, `entity`, `concept`, `adr`, `weekly-review`

2. **Choose domain** — `domain` must be a slug from `.scripts/auxmem.config.json` `domains` values. Do not guess; ask if unclear.

3. **Fill frontmatter** — Required: `title`, `summary` (≥40 chars, concrete nouns), `type`, `status`, `domain`, `created`, `updated` (today). Use controlled `type` and `status` from config vocab.

4. **Write body** — CommonMark + GFM only. Internal links: relative markdown `[title](../path/note.md)`. No wikilinks, no callouts, no Dataview.

5. **Place file** — Use the folder matching content:
   - Domain notes → matching `10-*`–`50-*` folder
   - ADRs → `60-decisions/`
   - Meetings → `70-meetings/`
   - Sources → `05-sources/` (`type: source`, immutable intake)
   - Synthesized → `85-synthesis/` only via `synthesize` skill

6. **Validate** — `python3 .scripts/gen_mocs.py` then `python3 .scripts/validate_auxmem.py --all`

7. **Commit** — Normal commit, not `--no-verify`.
