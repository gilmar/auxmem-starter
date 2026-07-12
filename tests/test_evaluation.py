"""Evaluation harness entry points (AUX-012)."""

from __future__ import annotations

from auxmem.evaluation import evaluate_all_references
from tests.helpers import REPO_ROOT


def test_evaluate_all_references_pass():
    reports = evaluate_all_references(REPO_ROOT / "examples")
    failed = [r for r in reports if not r.passed]
    assert not failed, ", ".join(r.auxmem for r in failed)


def test_evaluation_docs_exist():
    root = REPO_ROOT
    required = [
        root / "docs/EVALUATION.md",
        root / "examples/evaluation/agent_prompts.md",
        root / "examples/evaluation/scoring_rubric.md",
        root / "examples/evaluation/RESULTS.md",
        root / "examples/README.md",
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
    assert not missing, f"missing evaluation docs: {missing}"
