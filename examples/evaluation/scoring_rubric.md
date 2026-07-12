# Agent evaluation scoring rubric

Score each prompt **per provider** and **per reference auxmem**. Results are comparative and model-dependent — they do not gate releases unless paired with a deterministic regression.

## Per-prompt grades

| grade | criteria |
| --- | --- |
| **pass** | Factually correct; cites real files that support the answer; does not silently resolve documented contradictions |
| **partial** | Directionally correct; incomplete citations; misses stale/review signals |
| **fail** | Wrong ADR/status; invents facts; picks one side of a documented contradiction without provenance |

## Dimensions (qualitative)

| dimension | what to observe |
| --- | --- |
| Context recovery | Can the agent reconstruct current state from files alone? |
| Provenance | Are claims tied to paths or frontmatter sources? |
| Portability | Does a second provider reach the same conclusions from the same auxmem? |
| Auditability | Does the agent distinguish superseded vs active decisions? |
| Failure detection | Does the agent surface stale synthesis and open contradictions? |

## Metrics to record

- files opened (from provider telemetry if available);
- estimated tokens read;
- time to first useful answer;
- unsupported claims (count);
- citation coverage (claims with paths / total claims).

## Reporting

Use [`RESULTS.md`](RESULTS.md) as the public log. Include negative results and provider-specific limitations.

**Do not** claim AuxMem improves model intelligence. Report whether the **file-backed record** made recovery and auditing easier or harder compared to ad-hoc chat context.
