# Synthesis

How raw material becomes synthesized knowledge in this auxmem, intentionally and with provenance. Synthesis is a batch operation you run, not something that happens silently.

## The contract

Three layers, borrowed from Karpathy's LLM wiki pattern but adapted so synthesis is governed rather than the default runtime:

- Raw sources (`05-sources/`, `type: source`): immutable intake. Papers, transcripts, docs, clippings, captured notes. Read but not rewritten. Ground truth for provenance; you can always re-derive syntheses from here.
- Authored notes (`10-50` domains): your own ground truth. Decisions, findings, profiles. Not synthesized, not derived.
- Synthesized pages (`85-synthesis/`, `type: entity` or `type: concept`): derived, agent-maintained, one page per notable entity or concept. Convenience and navigation, not authority.

The distinction is enforced by the validator: a synthesized page must declare `synthesis: generated`, cite a non-empty `sources:` list, and carry `review:` and `generated_at`. A page that does not cite its provenance cannot exist. Authored notes must never claim to be generated.

## Why it is a queue, not automatic

`05-sources/` is the synthesis queue. Dropping material there does not synthesize it; running the loop does. This keeps synthesis intentional. Silent per-write synthesis is the drift failure mode this auxmem is designed to avoid.

## The loop (run with a CLI agent)

1. `python3 .scripts/synthesis_status.py` to see the queue (unsynthesized sources), stale pages (a source changed after the page was generated), and pages awaiting review.
2. For each unsynthesized source and each stale page, read the source(s) and the existing synthesized page if one exists.
3. Create or update entity pages (one per notable person, system, org, product) and concept pages (one per topic or idea) in `85-synthesis/`. Copy the template from `90-templates/entity.md` or `concept.md`.
4. For every synthesized page:
   - Cite every source it draws from in `sources:` (auxmem-root-relative paths, e.g. `05-sources/cube-docs.md` or `10-data-hub/mcp-server.md`).
   - Set `generated_at` to today and `review: needed`.
   - Make every claim traceable to a cited source. Do not invent. Mark uncertainty.
   - Record contradictions between sources in the page's "Open questions and contradictions" section rather than silently resolving them.
5. Append a synthesis log entry to `71-log/` (`type: log`): what you synthesized, from which sources, and any contradictions surfaced.
6. `python3 .scripts/gen_mocs.py` then `python3 .scripts/validate_auxmem.py --all`. Fix violations.
7. Commit.

## Review and staleness

- `review: needed` marks a page as not yet human-approved. A human reads it, checks it against sources, and flips it to `review: approved`. Approval is the intentional-acceptance step.
- Staleness: because each page lists its sources, `synthesis_status.py` flags a page whose source has a newer `updated` date than the page's `generated_at`. Stale is visible, not silent. Re-run the loop on stale pages.

## Boundaries

- Never synthesize sensitive personnel content into the auxmem. If a source contains it, it does not belong in `05-sources/` either. See ARCHITECTURE.md.
- Synthesized pages are derived; when a synthesized claim drives a real decision, verify against the cited source first, then record the decision as an authored ADR, not as a synthesized page.
- Do not delete raw sources after synthesizing. They are the provenance and the ability to re-derive.
