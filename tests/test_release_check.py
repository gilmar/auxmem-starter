"""Release check module and compatibility documentation (AUX-011)."""

from __future__ import annotations

import json

from koinome import release_check
from tests.helpers import REPO_ROOT


def test_release_check_passes_in_repository():
    results = release_check.run_checks(strict=True)
    failed = [r for r in results if not r.ok]
    assert not failed, "\n".join(f"{r.name}: {r.detail}" for r in failed)


def test_compatibility_doc_lists_required_environments():
    text = (REPO_ROOT / "docs" / "COMPATIBILITY.md").read_text(encoding="utf-8")
    for name in release_check.REQUIRED_COMPATIBILITY_HEADERS:
        assert name in text, f"missing environment {name}"
    assert "compatibility_smoke.sh" in text


def test_release_check_refuses_mismatched_target_version():
    results = release_check.run_checks(target_version="9.9.9", skip_scaffold=True)
    failed = {r.name for r in results if not r.ok}
    assert "target-version" in failed


def test_release_check_refuses_stable_one_dot_zero():
    result = release_check.check_prerelease_not_stable("1.0.0")
    assert not result.ok


def test_release_check_refuses_publish_zero_zero_zero():
    result = release_check.check_prerelease_not_stable("0.0.0")
    assert not result.ok


def test_manifest_conformance_version_matches_source():
    from koinome.version import CONFORMANCE_VERSION

    manifest = json.loads(
        (REPO_ROOT / "koinome" / "template" / ".koinome-manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["conformance_version"] == CONFORMANCE_VERSION


def test_changelog_distinguishes_mistaken_pypi_release():
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "2.0.0" in text
    assert "mistaken" in text.lower() or "accidental" in text.lower()
    assert "Unreleased" in text or "0.0.0" in text
