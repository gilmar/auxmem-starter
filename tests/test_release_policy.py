"""Release version policy checks before PyPI publish."""

from __future__ import annotations

import re

import pytest

from auxmem import __version__
from tests.helpers import REPO_ROOT

PYPROJECT = REPO_ROOT / "pyproject.toml"
RELEASE_DOC = REPO_ROOT / "docs" / "RELEASE.md"
MISTAKEN_PYPI_VERSION = "2.0.0"


def _read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "pyproject.toml missing version"
    return match.group(1)


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def test_cli_and_pyproject_versions_match():
    assert __version__ == _read_pyproject_version()


def test_release_policy_documented():
    text = RELEASE_DOC.read_text(encoding="utf-8")
    assert MISTAKEN_PYPI_VERSION in text
    assert "yank" in text.lower() or "2.0.1" in text


def test_pre_release_version_not_below_mistaken_pypi_release():
    """Before publishing, never ship a version lower than mistaken 2.0.0 on PyPI."""
    if __version__ == "0.0.0":
        pytest.skip("pre-release source version; policy applies at publish time")
    assert _version_tuple(__version__) > _version_tuple(MISTAKEN_PYPI_VERSION)
