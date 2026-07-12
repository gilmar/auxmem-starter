---
title: ADR-0001 Monolith stack
summary: Original decision to ship the payments API as a single monolith for speed to market.
type: adr
status: superseded
domain: engineering
created: 2026-05-01
updated: 2026-06-12
---
## Status
Superseded by [ADR-0002](adr-0002-service-boundaries.md).

## Context
Early delivery favored a single deployable artifact.

## Decision
Run the payments API as one monolith.

## Consequences
Fast iteration, later scaling limits.
