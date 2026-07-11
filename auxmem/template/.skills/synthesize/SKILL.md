---
name: synthesize
description: Run the governed auxmem synthesis loop over 05-sources into 85-synthesis entity and concept pages with provenance. Use when synthesizing sources, refreshing stale synthesized pages, or when synthesis_status.py reports queue or staleness.
---

# Synthesize

Synthesis is intentional and batch-only. Never synthesize silently on every write.

## Status

```bash
python3 .scripts/synthesis_status.py
```

Note: unsynthesized sources, stale pages (source updated after `generated_at`), pages awaiting review.

## Loop

For each unsynthesized source and each stale page:

1. Read source(s) and any existing synthesized page.
2. Create or update pages in `85-synthesis/` using `90-templates/entity.md` or `concept.md`.
3. On every synthesized page set:
   - `synthesis: generated`
   - `sources:` — auxmem-root-relative paths (non-empty)
   - `generated_at:` today
   - `review: needed`
4. Make every claim traceable to a cited source. Record contradictions in "Open questions and contradictions"; do not silently resolve.
5. Append `71-log/<today>-synthesis.md` (`type: log`): what was synthesized, from which sources, contradictions surfaced.
6. `python3 .scripts/gen_mocs.py` then `python3 .scripts/validate_auxmem.py --all`. Fix failures (see `fix-validation` skill).
7. Commit.

## Boundaries

- Never synthesize sensitive personnel content. See `docs/ARCHITECTURE.md`.
- Authored domain notes (10–50) are ground truth; never mark them `synthesis: generated`.
- Do not delete raw sources after synthesizing.

Full loop: `docs/SYNTHESIS.md`
