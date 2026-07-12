# Agent evaluation results (template)

No multi-provider agent benchmark has been run to completion in CI. Deterministic evaluation runs in every `check_release.sh` via `uv run python -m auxmem.evaluation`.

## Deterministic results (automated)

| date | command | outcome |
| --- | --- | --- |
| 2026-07-12 | `uv run python -m auxmem.evaluation` | pass on all three reference auxmems |

## Agent-assisted results (manual)

| date | provider | version | auxmem | prompts passed | notes |
| --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | pending |

### Known limitations

- Agent provider versions are not pinned in CI.
- Citation quality varies by model and context window settings.
- Examples are synthetic; real auxmems may have messier provenance graphs.

Update this file when running [`agent_prompts.md`](agent_prompts.md) across providers.
