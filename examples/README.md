# Reference corpora

Sanitized, fictional corpora that demonstrate governed work memory patterns. All content is synthetic — no real client, employer, or personal data.

## Examples

| path | scenario | domains |
| --- | --- | --- |
| [`software-project/`](software-project/) | Payments platform engineering | engineering, product |
| [`consulting-engagement/`](consulting-engagement/) | Retail transformation engagement | engagement, client |
| [`research-project/`](research-project/) | Cell-count ML research | literature, experiments |

Each example includes:

- realistic domain configuration;
- decisions (with one superseded ADR and one active successor);
- meetings, logs, and tasks;
- sources, synthesized pages, and internal links;
- one **stale synthesis** (source updated after `generated_at`);
- one **unresolved contradiction** documented in synthesis pages.

## Materialize / refresh

Examples are generated from the current template:

```bash
uv run python examples/build_references.py
```

Commit the output after template changes. Git history is recreated by the build script locally but is not shipped inside `examples/` (see `docs/EVALUATION.md`).

## Evaluation

Deterministic checks:

```bash
uv run python -m koinome.evaluation
```

Agent-assisted prompts and scoring: [`evaluation/`](evaluation/) and [`docs/EVALUATION.md`](../docs/EVALUATION.md).
