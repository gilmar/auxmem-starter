---
name: adr
description: Write or supersede an auxmem architecture decision record (ADR) and update the decision log index. Use when recording a durable decision, reversing a prior decision, or when the user asks for an ADR.
---

# ADR workflow

Decisions are immutable. To change one, supersede it with a new ADR.

## New ADR

1. Read `60-decisions/index.md` for the next number.
2. Copy `90-templates/adr.md` to `60-decisions/adr-NNNN-short-slug.md`.
3. Fill frontmatter: `type: adr`, `status: in-review` (or `active` when accepted), valid `domain`, full `summary`.
4. Write MADR sections: Status, Context, Decision Drivers, Considered Options, Decision, Consequences.
5. Append a row to `60-decisions/index.md` (newest near top).
6. `python3 .scripts/gen_mocs.py` then `python3 .scripts/validate_auxmem.py --all`. Commit.

## Supersede an existing ADR

1. Create new ADR documenting the reversal or refinement.
2. Set old ADR `status: superseded` and `updated:` today. In its Status section, note "Superseded by ADR-NNNN".
3. New ADR Status references the superseded ADR.
4. Update `60-decisions/index.md` for both records.
5. Validate and commit.

## Rules

- Never edit a decision's substance in place; write a new ADR.
- Do not invent system or metric names; check domain notes for exact names.
