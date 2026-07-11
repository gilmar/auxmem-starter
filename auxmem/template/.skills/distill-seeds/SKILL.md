---
name: distill-seeds
description: Distill AI provider export staging corpus into seed notes inside an auxmem. Use when bootstrapping an auxmem from seed-staging, provider exports, or conversation history imports.
---

# Distill seeds

Staging corpus lives **outside** the auxmem in `seed-staging/`. Output is 15–30 current-state seed notes inside the auxmem.

## Inputs (priority order)

1. `seed-staging/manual/*.md` — read fully first
2. `seed-staging/index.md` — triage table; select conversations
3. `seed-staging/{claude,chatgpt,gemini}/*.md` — read selectively

## Produce

- Domain notes in populated `10-*`–`50-*` folders
- ADRs in `60-decisions/` from ADR-0002 onward (0001 is the auxmem itself)
- `80-moc/home-moc.md` plus domain MOCs linking every seed
- `71-log/<today>-auxmem-bootstrap.md`
- `72-tasks/todo.txt` for open commitments (todo.txt grammar, creation date = today)

## Hard rules

1. Full frontmatter on every note. Run `python3 .scripts/validate_auxmem.py --all` before finishing.
2. Never copy transcript text verbatim — synthesize in your own words.
3. No sensitive personnel content in this auxmem. Flag sources in `seed-staging/sensitive-review.md` (outside the auxmem); do not summarize sensitive content.
4. Mark uncertainty: "as of \<date\>" for single old mentions.
5. Do not invent metric, model, or system names.
6. Relative markdown links only. No wikilinks.
7. Commit in logical batches. Normal commits, not `--no-verify`.

## Order

1. Read manual dumps and index; build shortlist
2. Read shortlist; draft domain notes and ADRs
3. Write MOCs last
4. Validate, fix, commit, write bootstrap log

Present `sensitive-review.md` list and bootstrap log to the user as final summary.

Full importer doc: AuxMem `importers/distill-seeds.md` (reference if available outside the auxmem).
