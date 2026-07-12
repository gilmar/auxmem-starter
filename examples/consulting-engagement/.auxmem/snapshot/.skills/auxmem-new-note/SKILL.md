---
name: auxmem-new-note
description: Create a new auxmem note from 90-templates with correct frontmatter and domain. Use when adding a project doc, meeting note, stakeholder profile, reference, or any new auxmem note.
---

# New note

## Steps

1. **Pick template** — Copy from `90-templates/` whose `type:` matches the note you need. Valid `type` and `status` values are only those listed under `vocab` in `.scripts/auxmem.config.json`.

2. **Choose domain** — `domain` must be a slug from `domains` values in `.scripts/auxmem.config.json`. Do not guess; ask if unclear.

3. **Fill frontmatter** — Required fields and `min_summary_len` are in the config. Set `title`, `summary` (meet minimum length, concrete nouns), `type`, `status`, `domain`, `created`, `updated` (today).

4. **Write body** — CommonMark + GFM only. Internal links: relative markdown `[title](../path/note.md)`. No wikilinks, no callouts, no Dataview.

5. **Place file** — Use the folder matching content:
   - Domain notes → matching `10-*`–`50-*` folder
   - ADRs → `60-decisions/`
   - Meetings → `70-meetings/`
   - Sources → `05-sources/` (`type: source`, immutable intake)
   - Synthesized → `85-synthesis/` only via `auxmem-synthesize` skill

6. **Validate** — `python3 .scripts/gen_mocs.py` then `python3 .scripts/validate_auxmem.py --all`

7. **Commit** — Normal commit, not `--no-verify`.
