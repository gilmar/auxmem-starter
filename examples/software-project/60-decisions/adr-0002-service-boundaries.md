---
title: ADR-0002 Service boundaries
summary: Accepted decision to split the payments platform into checkout, ledger, and reconciliation services.
type: adr
status: active
domain: engineering
created: 2026-06-12
updated: 2026-06-12
---
## Status
Accepted. Supersedes [ADR-0001](adr-0001-monolith-stack.md).

## Context
Traffic growth and team parallelism require clearer boundaries.

## Decision
Split checkout, ledger, and reconciliation into separate services.

## Consequences
More operational overhead, better isolation.
