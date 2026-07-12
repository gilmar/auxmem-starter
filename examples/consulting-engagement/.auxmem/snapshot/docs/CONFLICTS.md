# Conflicting sources

How to handle contradictory evidence in an auxmem. Configuration (domains, types, statuses) still comes only from `.scripts/auxmem.config.json`; this document covers content conflicts between notes, transcripts, and synthesis sources.

## Policy

1. **Do not silently resolve contradictions.** If two sources disagree, the record must show both claims and their provenance until a human resolves them.
2. **Retain provenance.** Keep citations (`sources:` on synthesized pages, links and refs on authored notes) so each claim can be traced.
3. **Compare authority explicitly.** Weigh scope (local vs global), effective date, whether a later note supersedes an earlier ADR, and who authored the claim — not just file mtime.
4. **Mark unresolved contradictions for review.** Use synthesis `review: needed`, an "Open questions and contradictions" section, or an inbox note. Do not mark `review: approved` while a material contradiction remains unresolved.
5. **Recency is one signal, not automatic truth.** A newer chat transcript does not override an accepted ADR or a validated domain note without an explicit supersession or human decision.
6. **Prefer authored ground truth for decisions.** When a synthesized page conflicts with an authored ADR or domain note, treat the authored record as the default authority until a new ADR says otherwise.

## In practice

- **Seed distillation and imports:** Prefer recent evidence when triaging stale transcripts, but record conflicts in the bootstrap log and flag notes that need human review instead of picking a silent winner.
- **Synthesis loop:** Record contradictions in the synthesized page; set `review: needed`. See `docs/SYNTHESIS.md`.
- **Day-to-day notes:** Use "as of YYYY-MM-DD" for single-source uncertainty. When two durable facts conflict, write a finding or inbox note naming both sources and leave resolution to the human.

## Related

- `docs/SYNTHESIS.md` — synthesis provenance and review gates
- `AGENTS.md` — agent write rules
- `.scripts/auxmem.config.json` — schema and controlled vocabularies (not content-truth rules)
