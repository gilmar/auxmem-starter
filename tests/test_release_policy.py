"""Release version policy checks before PyPI publish."""

from __future__ import annotations

import json
import re

import pytest

from koinome import __version__
from koinome.version import CONFORMANCE_VERSION, TEMPLATE_VERSION
from tests.helpers import REPO_ROOT

PYPROJECT = REPO_ROOT / "pyproject.toml"
RELEASE_DOC = REPO_ROOT / "docs" / "RELEASE.md"
MANIFEST = REPO_ROOT / "koinome" / "template" / ".koinome-manifest.json"
MISTAKEN_PYPI_VERSION = "2.0.0"


def _read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml missing version"
    return match.group(1)


def _release_tuple(version: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+(?:\.\d+)*)", version)
    assert match, f"invalid version: {version}"
    return tuple(int(part) for part in match.group(1).split("."))


def test_cli_and_pyproject_versions_match():
    assert __version__ == _read_pyproject_version()


def test_template_and_conformance_versions_documented_in_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["template_version"] == TEMPLATE_VERSION
    assert manifest["conformance_version"] == CONFORMANCE_VERSION


def test_release_policy_documented():
    text = RELEASE_DOC.read_text(encoding="utf-8")
    assert MISTAKEN_PYPI_VERSION in text
    assert "yank" in text.lower() or "2.0.1" in text


def test_pre_release_version_not_below_mistaken_pypi_release():
    """Before publishing, never ship a version lower than mistaken 2.0.0 on PyPI."""
    if __version__ == "0.0.0":
        pytest.skip("pre-release source version; policy applies at publish time")
    if __version__.startswith("0."):
        pytest.skip("0.x releases are intentional for the new koinome PyPI project")
    assert _release_tuple(__version__) > _release_tuple(MISTAKEN_PYPI_VERSION)
