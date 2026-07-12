# Fixing validation failures

The validator is a gate, not a wall. When it fails, most of the work is repair, and most of that repair should not fall on you by hand. This is the protocol an AI agent follows to help fix failures while keeping you accountable for the content.

Run `python3 .scripts/validate_auxmem.py --json --all` to get machine-readable errors. Each error carries a `fixable` tag: `auto`, `llm`, or `human`. Fix in that order.

## Tier 1: auto (no model, no human)

Mechanical errors with a single correct repair: a missing `updated` or `created` date, a `tag:` that should be `tags:`, a date that needs zero-padding, a `tags` scalar that should be a list.

Fix them deterministically:
```bash
python3 .scripts/validate_auxmem.py --fix --all
```
This rewrites only frontmatter, never the body, and only for the unambiguous cases. It reports exactly what it changed. No judgment is involved, so no one needs to review the meaning, only that the command ran.

## Tier 2: llm (agent drafts, human accepts)

Errors that need understanding of the note but whose fix is grounded in the note's own content: a `summary` that is missing or too short, a missing `title`, a synthesized page that needs its `sources` filled from what it clearly draws on.

Rules for the agent:
- Draft the fix from the note body and its existing frontmatter. Do not invent facts. A summary must describe what the note actually says, front-loaded with concrete nouns someone would grep for.
- For a missing `title`, propose one from the note's heading or filename.
- For empty `sources` on a synthesized page, list only sources the page visibly draws on; if you cannot tell, drop to Tier 3 and ask.
- Present the drafted change to the human and get acceptance before committing. The human authors the note in the sense that it enters the record under their responsibility. You are removing toil, not taking ownership.

## Tier 3: human (ask, do not guess)

Errors where the correct value is a genuine decision, not a derivation: a `type` or `domain` not in the vocabulary, a `sources:` path that does not resolve, a duplicate frontmatter key, a link or source path that escapes the auxmem root, a banned wikilink whose target is ambiguous.

Rules for the agent:
- Do not pick a domain or type on the human's behalf. Ask, offering the valid options from the config.
- For an unresolved source path, ask whether the source was renamed, moved, or never added, rather than deleting the citation.
- For a wikilink, convert it to a relative markdown link only if the target resolves unambiguously; otherwise ask.

## Why this preserves the model

The gate never weakens. What changes is who absorbs the friction: Tier 1 absorbs it with code, Tier 2 with an agent draft the human accepts, Tier 3 with a quick human decision. A strict gate plus this protocol is more ergonomic than a lax gate, because you get both loose typing and a clean, accountable result. That is the enabling-constraint: the rule is what makes the assistance safe enough to trust.

## What never gets auto-fixed

The fixer will not touch a malformed or absent frontmatter block, will not choose a controlled-vocabulary value, will not resolve a broken link, will not rewrite duplicate-key YAML, and will not edit note bodies. Those are either judgment calls or signs something is wrong that a silent rewrite would hide.
