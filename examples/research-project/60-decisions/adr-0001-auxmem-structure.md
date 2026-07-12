---
title: ADR-0001 Open-standard agent-readable auxmem
summary: Records the decision to build this auxmem as a provider-independent, plain-markdown knowledge base optimized for CLI agent retrieval, governed by a validator.
type: adr
status: active
domain: literature
created: 2026-07-04
updated: 2026-07-04
tags: [meta, auxmem]
---
## Status
Accepted

## Context
Business context and memory must outlive any single AI provider. Provider apps hold state in systems we do not own. We interact with models via CLI and API, not desktop or web UIs.

## Decision Drivers
- Provider independence: no lock-in to one vendor's memory or format.
- Agent retrieval: structure optimized for grep, glob, and frontmatter triage.
- Longevity: formats that predate and will outlive current tools.

## Considered Options
### Obsidian-flavored markdown
Pros: rich plugin ecosystem, link maintenance.
Cons: wikilinks, Dataview, and callouts are non-standard and tie us to Obsidian.

### Open-standard markdown (chosen)
Pros: CommonMark plus GFM tables plus YAML frontmatter reads everywhere and greps cleanly.
Cons: no automatic link maintenance; must be enforced by tooling.

## Decision
Adopt open-standard markdown with a strict frontmatter schema, a config-driven validator as the enforcement plane, git as sync, and todo.txt for tasks. Agent orientation lives in AGENTS.md.

## Consequences
Easier: any model reads the auxmem; migration between providers is free.
Harder: link maintenance and dashboards must be generated, not plugin-provided. The validator and gen_mocs.py cover both.
