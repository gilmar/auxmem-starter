"""Read-only conformance command and generated CI (AUX-004)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from auxmem.cli import main
from auxmem.exit_codes import NON_CONFORMANT, OK
from tests.helpers import (
    note_with_fm,
    run_auxmem,
    run_conformance_check,
    scaffold_auxmem,
    tree_bytes_snapshot,
    write_note,
)

VALID_FM = dict(
    title="Conformance note",
    summary="Concrete nouns for conformance check tests in this auxmem folder.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


def test_scaffold_contains_ci_workflow(tmp_path):
    dest = tmp_path / "fresh"
    scaffold_auxmem(dest)
    workflow = dest / ".github" / "workflows" / "auxmem-check.yml"
    assert workflow.is_file()
    data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    assert data["jobs"]["check"]["steps"][-1]["run"] == "python3 .scripts/check_auxmem.py"


def test_scaffold_contains_check_script(tmp_path):
    dest = tmp_path / "fresh"
    scaffold_auxmem(dest)
    assert (dest / ".scripts" / "check_auxmem.py").is_file()


def test_check_help_lists_read_only():
    result = run_auxmem(["check", "--help"])
    assert result.returncode == 0
    assert "without modifying" in (result.stdout + result.stderr).lower()


def test_check_passes_on_valid_auxmem(tmp_auxmem):
    rc = main(["check", str(tmp_auxmem)])
    assert rc == OK
    assert "conformance check passed" in run_conformance_check(tmp_auxmem).stdout


def test_check_is_read_only(tmp_auxmem):
    before = tree_bytes_snapshot(tmp_auxmem)
    rc = main(["check", str(tmp_auxmem)])
    after = tree_bytes_snapshot(tmp_auxmem)
    assert rc == OK
    assert before == after


def test_check_fails_on_stale_moc(tmp_auxmem):
    write_note(
        tmp_auxmem,
        "10-projects/stale-moc.md",
        note_with_fm("Body.", **VALID_FM),
    )
    rc = main(["check", str(tmp_auxmem)])
    assert rc == NON_CONFORMANT
    assert "MOC" in run_conformance_check(tmp_auxmem).stdout


def test_doctor_repairs_stale_moc_then_check_passes(tmp_auxmem):
    write_note(
        tmp_auxmem,
        "10-projects/repair-moc.md",
        note_with_fm("Body.", **VALID_FM),
    )
    assert main(["check", str(tmp_auxmem)]) == NON_CONFORMANT
    assert main(["doctor", str(tmp_auxmem)]) == OK
    assert main(["check", str(tmp_auxmem)]) == OK


def test_manifest_lists_ci_workflow():
    manifest = json.loads(
        Path("auxmem/template/.auxmem-manifest.json").read_text(encoding="utf-8")
    )
    assert ".github/workflows/auxmem-check.yml" in manifest["files"]
    assert manifest["files"][".github/workflows/auxmem-check.yml"]["policy"] == "overwrite"


def test_upgrade_delivers_workflow(tmp_path):
    dest = tmp_path / "legacy"
    scaffold_auxmem(dest)
    workflow = dest / ".github" / "workflows" / "auxmem-check.yml"
    if workflow.exists():
        workflow.unlink()
    workflow.parent.rmdir()
    result = run_auxmem(["upgrade", "--force", str(dest)])
    assert result.returncode == OK, result.stdout + result.stderr
    assert workflow.is_file()
