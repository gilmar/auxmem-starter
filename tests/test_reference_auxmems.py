"""Reference auxmem fixtures (AUX-012)."""

from __future__ import annotations

import pytest

from auxmem.evaluation import REFERENCE_NAMES, evaluate_reference
from tests.helpers import REPO_ROOT, run_conformance_check, validate_auxmem

EXAMPLES = REPO_ROOT / "examples"


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_reference_auxmem_exists(name: str):
    path = EXAMPLES / name
    assert path.is_dir(), f"missing {path}; run examples/build_references.py"
    assert (path / ".scripts/auxmem.config.json").is_file()


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_reference_auxmem_validates(name: str):
    path = EXAMPLES / name
    result = validate_auxmem(path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_reference_auxmem_conformance(name: str):
    path = EXAMPLES / name
    result = run_conformance_check(path)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_reference_has_required_story_elements(name: str):
    path = EXAMPLES / name
    decisions = list((path / "60-decisions").glob("adr-*.md"))
    assert len(decisions) >= 2
    sources = list((path / "05-sources").glob("*.md"))
    assert len(sources) >= 2
    synthesis = list((path / "85-synthesis").rglob("*.md"))
    assert synthesis


@pytest.mark.parametrize("name", REFERENCE_NAMES)
def test_deterministic_evaluation_passes(name: str):
    report = evaluate_reference(EXAMPLES / name)
    failed = [r for r in report.results if not r.ok]
    assert not failed, "\n".join(f"{r.name}: {r.detail}" for r in failed)
