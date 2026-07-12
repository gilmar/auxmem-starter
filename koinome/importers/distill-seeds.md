# Distill seed notes from the staging area

You are bootstrapping a fresh work corpus from exported AI conversation history.
The staging area lives OUTSIDE the corpus in `seed-staging/`. It is raw material,
not corpus content. Your output is a small set of current-state seed notes inside
the corpus, valid against the corpus schema.

## Inputs, in priority order
1. `seed-staging/manual/*.md`: self-description dumps the user requested from each
   provider before leaving ("write out everything you know about me"). Highest
   signal. Read all of them fully, first.
2. `seed-staging/index.md`: triage table of all exported conversations. Use it to
   select; do not read every conversation.
3. `seed-staging/{claude,chatgpt,gemini}/*.md`: full transcripts (Gemini contains
   prompts only). Read selectively based on the index.

## What to produce
Synthesize CURRENT STATE, not history. Transcripts are evidence of what was true at some point; prefer recent material when triaging, but when sources conflict do not pick a silent winner — follow `docs/CONFLICTS.md` (retain both claims, flag for review).

Read subject domain folders from `domains` in `.scripts/koinome.config.json`. Target 15 to 30 seed notes total, distributed across populated domain folders, plus:

- `60-decisions/`: one ADR per durable decision found in the corpus, MADR format,
  numbered from ADR-0002 (ADR-0001 documents the corpus itself). If a decision was
  later reversed in the corpus, record both with supersession, not just the winner.
- `80-moc/home-moc.md` plus one MOC per populated domain, linking every seed note.
- `71-log/<today>-corpus-bootstrap.md`: what you imported, what you skipped, what
  looked stale or contradictory and needs the user's review.
- `72-tasks/todo.txt`: any clearly open commitments found in recent conversations, one task
  per line in todo.txt grammar, creation date = today.

## Hard rules
1. Every note gets full frontmatter per the corpus schema. After writing, run
   `.scripts/validate_corpus.py --all` and fix every violation before finishing.
2. NEVER copy transcript text verbatim. Synthesize in your own words. Transcripts
   include half-formed ideas the user later abandoned; a verbatim import launders
   drafts into facts.
3. Sensitive personnel content (performance issues, terminations, compensation,
   health, or anything about a named individual's employment situation) does NOT
   enter this corpus. When you encounter it, skip it and add one line to
   `seed-staging/sensitive-review.md` (outside the corpus) naming only the source
   file, so the user can route it to private storage manually. Do not summarize
   the sensitive content itself, even in that list.
4. Mark uncertainty in the notes. If a fact appears once, in an old conversation,
   write "as of <date>" rather than asserting it as current.
5. Do not invent metric names, model names, or system names not present in the
   corpus. Missing detail is acceptable; fabricated detail is not.
6. Internal links use relative markdown links. No wikilinks.
7. Commit in logical batches with descriptive messages (seeds by domain, then
   MOCs, then log and 72-tasks/todo.txt). Normal commits, not --no-verify: the hook is
   part of the bootstrap quality gate.

## Order of work
1. Read manual dumps, then the index. Build a shortlist of conversations to read.
2. Read the shortlist. Draft the domain notes and ADRs.
3. Write MOCs last, linking everything.
4. Validate, fix, commit, write the bootstrap log, and stop. Present the
   sensitive-review list and the log to the user as the final summary.
