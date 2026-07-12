# Evaluation methodology

AuxMem evaluation separates **deterministic guarantees** (validator, conformance, staleness detection) from **model-dependent outcomes** (agent context recovery). AuxMem does not claim to improve model intelligence — it measures portability, provenance, auditability, and failure detection.

## Deterministic evaluation

Run on all reference auxmems:

```bash
uv run python -m auxmem.evaluation
```

Included in the release gate via `bash scripts/check_release.sh`.

| check | what it proves |
| --- | --- |
| validation | reference auxmem passes `validate_auxmem.py --all` |
| conformance | `check_auxmem.py` passes (validation + MOC freshness) |
| moc-freshness | generated MOCs are current |
| synthesis-signals | `synthesis_status.py` reports stale syntheses and review queue |
| superseded-adr | one superseded ADR and one active successor exist |
| unresolved-contradiction | synthesis pages document conflicts without resolving them |
| broken-link-detection | validator rejects a probe note with a broken internal link |
| recovery-deletion | deleting a linked ADR surfaces broken links on re-validation |
| upgrade-preservation | `auxmem upgrade --dry-run` reports up-to-date on fresh references |
| plain-text-readability | every `.md` file is UTF-8 text without tooling |

### Not covered deterministically here

- **Sync conflict quarantine** — covered by `tests/test_sync.py` on ephemeral auxmems.
- **Agent provider behavior** — manual or scripted agent runs using `examples/evaluation/agent_prompts.md`.

## Agent-assisted evaluation

Public prompt set: [`examples/evaluation/agent_prompts.md`](../examples/evaluation/agent_prompts.md)

Scoring rubric: [`examples/evaluation/scoring_rubric.md`](../examples/evaluation/scoring_rubric.md)

Record for each provider run:

- files opened;
- estimated tokens read (provider metadata if available);
- correctness against rubric;
- unsupported claims;
- file citations in the answer;
- time to first useful answer.

Compare providers on **context recovery** and **citation quality**, not reasoning novelty.

## Results and limitations

Published results template: [`examples/evaluation/RESULTS.md`](../examples/evaluation/RESULTS.md)

Negative results and limitations must be reported explicitly. README guarantee claims should cite which deterministic checks or agent runs support them.

## Git history fixture

`examples/build_references.py` can recreate a short local git history when materializing examples. The committed `examples/` trees omit `.git` to keep the repository lean; history is optional for agent exercises that require `git log`.
