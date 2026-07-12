"""Read-only conformance command and generated CI (AUX-004)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from koinome.cli import main
from koinome.exit_codes import NON_CONFORMANT, OK
from tests.helpers import (
    note_with_fm,
    run_conformance_check,
    run_koinome,
    scaffold_corpus,
    tree_bytes_snapshot,
    write_note,
)

VALID_FM = dict(
    title="Conformance note",
    summary="Concrete nouns for conformance check tests in this corpus folder.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


def test_scaffold_contains_ci_workflow(tmp_path):
    dest = tmp_path / "fresh"
    scaffold_corpus(dest)
    workflow = dest / ".github" / "workflows" / "koinome-check.yml"
    assert workflow.is_file()
    data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    assert data["jobs"]["check"]["steps"][-1]["run"] == "python3 .scripts/check_corpus.py"


def test_scaffold_contains_check_script(tmp_path):
    dest = tmp_path / "fresh"
    scaffold_corpus(dest)
    assert (dest / ".scripts" / "check_corpus.py").is_file()


def test_check_help_lists_read_only():
    result = run_koinome(["check", "--help"])
    assert result.returncode == 0
    assert "without modifying" in (result.stdout + result.stderr).lower()


def test_check_passes_on_valid_corpus(tmp_corpus):
    rc = main(["check", str(tmp_corpus)])
    assert rc == OK
    assert "conformance check passed" in run_conformance_check(tmp_corpus).stdout


def test_check_is_read_only(tmp_corpus):
    before = tree_bytes_snapshot(tmp_corpus)
    rc = main(["check", str(tmp_corpus)])
    after = tree_bytes_snapshot(tmp_corpus)
    assert rc == OK
    assert before == after


def test_check_fails_on_stale_moc(tmp_corpus):
    write_note(
        tmp_corpus,
        "10-projects/stale-moc.md",
        note_with_fm("Body.", **VALID_FM),
    )
    rc = main(["check", str(tmp_corpus)])
    assert rc == NON_CONFORMANT
    assert "MOC" in run_conformance_check(tmp_corpus).stdout


def test_doctor_repairs_stale_moc_then_check_passes(tmp_corpus):
    write_note(
        tmp_corpus,
        "10-projects/repair-moc.md",
        note_with_fm("Body.", **VALID_FM),
    )
    assert main(["check", str(tmp_corpus)]) == NON_CONFORMANT
    assert main(["doctor", str(tmp_corpus)]) == OK
    assert main(["check", str(tmp_corpus)]) == OK


def test_manifest_lists_ci_workflow():
    manifest = json.loads(
        Path("koinome/template/.koinome-manifest.json").read_text(encoding="utf-8")
    )
    assert ".github/workflows/koinome-check.yml" in manifest["files"]
    assert manifest["files"][".github/workflows/koinome-check.yml"]["policy"] == "overwrite"


def test_upgrade_delivers_workflow(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    workflow = dest / ".github" / "workflows" / "koinome-check.yml"
    if workflow.exists():
        workflow.unlink()
    workflow.parent.rmdir()
    result = run_koinome(["upgrade", "--force", str(dest)])
    assert result.returncode == OK, result.stdout + result.stderr
    assert workflow.is_file()
