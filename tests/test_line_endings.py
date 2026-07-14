"""Regression: Windows/Git autocrlf must not break bootstrap.sh (issue #36)."""

from __future__ import annotations

from pathlib import Path

import pytest

from koinome.line_endings import ensure_lf_bytes, normalize_corpus_shell_scripts
from koinome.scaffold import ScaffoldError, scaffold
from tests.helpers import REPO_ROOT, scaffold_corpus
from tests.test_bootstrap import run_bootstrap

TEMPLATE_BOOTSTRAP = REPO_ROOT / "koinome" / "template" / "bootstrap.sh"


def test_template_bootstrap_has_unix_line_endings():
    raw = TEMPLATE_BOOTSTRAP.read_bytes()
    assert b"\r" not in raw, "template bootstrap.sh must be LF-only in the repo"


def test_template_gitattributes_forces_lf_for_shell():
    text = (REPO_ROOT / "koinome" / "template" / ".gitattributes").read_text(encoding="utf-8")
    assert "eol=lf" in text
    assert "*.sh" in text
    assert ".scripts/pre-commit" in text


def test_repo_gitattributes_forces_lf_for_shell():
    text = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.sh text eol=lf" in text


def test_normalize_corpus_shell_scripts_rewrites_crlf(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    path = dest / "bootstrap.sh"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert b"\r\n" in path.read_bytes()
    changed = normalize_corpus_shell_scripts(dest)
    assert "bootstrap.sh" in changed
    assert b"\r" not in path.read_bytes()
    assert ensure_lf_bytes(b"a\r\nb\rc\n") == b"a\nb\nc\n"


def test_normalized_crlf_bootstrap_runs(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    path = dest / "bootstrap.sh"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    normalize_corpus_shell_scripts(dest)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr


def test_scaffold_normalizes_crlf_copied_from_template(tmp_path, monkeypatch):
    """If the bundled template arrives with CRLF (Windows checkout), scaffold still works."""
    import shutil

    import koinome.scaffold as scaffold_mod

    real_copytree = shutil.copytree

    def copytree_inject_crlf(src, dst, *args, **kwargs):
        result = real_copytree(src, dst, *args, **kwargs)
        bootstrap = Path(dst) / "bootstrap.sh"
        # copytree recurses into subdirs; only rewrite the corpus-root bootstraps.
        if bootstrap.is_file():
            bootstrap.write_bytes(bootstrap.read_bytes().replace(b"\n", b"\r\n"))
            for script in (Path(dst) / ".scripts").glob("*.sh"):
                script.write_bytes(script.read_bytes().replace(b"\n", b"\r\n"))
            pre = Path(dst) / ".scripts" / "pre-commit"
            if pre.is_file():
                pre.write_bytes(pre.read_bytes().replace(b"\n", b"\r\n"))
        return result

    monkeypatch.setattr(scaffold_mod.shutil, "copytree", copytree_inject_crlf)
    dest = tmp_path / "corpus"
    try:
        result = scaffold(
            "win-test",
            dest,
            {"10-projects": "projects"},
            run_bootstrap=True,
        )
    except ScaffoldError as exc:
        pytest.fail(f"scaffold failed with CRLF-injected template: {exc}")
    assert result["bootstrapped"] is True
    assert b"\r" not in (dest / "bootstrap.sh").read_bytes()
