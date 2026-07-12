"""Repository-wide obsolete naming consistency check."""

from __future__ import annotations

import re
from pathlib import Path

from tests.helpers import REPO_ROOT

# Narrow allowlist for intentional legacy or historical references.
ALLOWLIST_PATHS = {
    "tests/test_naming_consistency.py",
}

FORBIDDEN_PATTERNS = [
    re.compile(r"\bauxmem\b", re.I),
    re.compile(r"\bAuxMem\b"),
    re.compile(r"\bauxiliary memory\b", re.I),
    re.compile(r"\ban auxmem\b", re.I),
    re.compile(r"\bauxmems\b", re.I),
]

# Package modules live under koinome/, not corpus/ (managed folders are corpora).
WRONG_MODULE_INVOCATION = re.compile(r"python(?:3)? -m corpus\.", re.I)

SKIP_DIRS = {".git", ".venv", "build", "dist", "__pycache__", ".pytest_cache", "auxmem.egg-info", "koinome.egg-info"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".sh", ".toml", ".yml", ".yaml", ".txt", ".systemd", ".service", ".timer"}


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in ("pre-commit", "koinome-cli", "AGENTS.md"):
            continue
        rel = path.relative_to(root).as_posix()
        if rel in ALLOWLIST_PATHS:
            continue
        yield rel, path


def test_no_obsolete_names_outside_allowlist():
    violations: list[str] = []
    for rel, path in _iter_text_files(REPO_ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                violations.append(f"{rel} matched {pattern.pattern}")
                break
    assert not violations, "obsolete names found:\n" + "\n".join(violations[:40])


def test_no_wrong_corpus_module_invocations():
    violations: list[str] = []
    for rel, path in _iter_text_files(REPO_ROOT):
        text = path.read_text(encoding="utf-8", errors="replace")
        if WRONG_MODULE_INVOCATION.search(text):
            violations.append(rel)
    assert not violations, (
        "use python -m koinome.<module>, not python -m corpus.<module>:\n"
        + "\n".join(violations[:40])
    )


def test_readme_states_free_open_source_commitment():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "free and open-source" in readme.lower()
    assert "corpus" in readme.lower()
    assert "corpora" in readme.lower()


def test_readme_states_current_scope():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "one corpus at a time" in readme.lower() or "one at a time" in readme.lower()
    assert "cross-corpus" in readme.lower()
