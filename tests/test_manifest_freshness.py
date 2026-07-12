"""Verify the template manifest matches the current template tree."""

from __future__ import annotations

import json
import subprocess
import sys

from tests.helpers import REPO_ROOT


def _manifest_text() -> str:
    path = REPO_ROOT / "auxmem" / "template" / ".auxmem-manifest.json"
    return path.read_text(encoding="utf-8")


def test_manifest_is_fresh():
    before = _manifest_text()
    proc = subprocess.run(
        [sys.executable, "build_manifest.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    after = _manifest_text()
    assert before == after, (
        "template manifest is stale; run `uv run python build_manifest.py` and commit "
        "auxmem/template/.auxmem-manifest.json"
    )


def test_manifest_lists_managed_files():
    manifest = json.loads(_manifest_text())
    assert manifest["files"], "manifest must list managed files"
    for rel, meta in manifest["files"].items():
        assert meta.get("policy") in {"overwrite", "merge", "merge3"}, rel
        assert meta.get("sha256"), rel
        assert (REPO_ROOT / "auxmem" / "template" / rel).is_file(), rel
