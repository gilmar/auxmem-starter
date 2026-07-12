"""Coordinated CLI, template, and conformance versioning (AUX-011)."""

from __future__ import annotations

import json
import re

from koinome import __version__
from koinome.version import CONFORMANCE_VERSION, TEMPLATE_VERSION
from tests.helpers import REPO_ROOT

MANIFEST = REPO_ROOT / "koinome" / "template" / ".koinome-manifest.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"
VERSION_MODULE = REPO_ROOT / "koinome" / "version.py"


def _read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml missing version"
    return match.group(1)


def test_cli_version_sources_match():
    assert __version__ == _read_pyproject_version()


def test_template_version_in_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["template_version"] == TEMPLATE_VERSION


def test_conformance_version_in_manifest():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["conformance_version"] == CONFORMANCE_VERSION


def test_version_module_documents_three_tracks():
    text = VERSION_MODULE.read_text(encoding="utf-8")
    assert "TEMPLATE_VERSION" in text
    assert "CONFORMANCE_VERSION" in text
    assert "CLI" in text or "conformance" in text.lower()
