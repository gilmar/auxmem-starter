"""Transactional upgrade with manifest verification (AUX-008)."""

from __future__ import annotations

import json
import shutil

import pytest

from auxmem import upgrade as upgrade_mod
from auxmem.cli import main
from auxmem.exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from auxmem.manifest import verify_bundled_template
from auxmem.upgrade import MANIFEST_SRC, TEMPLATE_DIR, PostCheckResult
from tests.helpers import (
    note_with_fm,
    read_auxmem_config,
    run_auxmem,
    scaffold_auxmem,
    tree_bytes_snapshot,
    write_note,
)

VALID_FM = dict(
    title="Upgrade note",
    summary="Concrete nouns for transactional upgrade tests in this auxmem.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


def test_verify_bundled_template_passes():
    verify_bundled_template(TEMPLATE_DIR, MANIFEST_SRC)


def test_verify_fails_on_hash_mismatch(tmp_path, monkeypatch):
    bad_manifest = tmp_path / "manifest.json"
    manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    rel = next(iter(manifest["files"]))
    manifest["files"][rel]["sha256"] = "0" * 64
    bad_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_bundled_template(TEMPLATE_DIR, bad_manifest)


def test_verify_fails_on_missing_template_file(tmp_path):
    template = tmp_path / "template"
    shutil.copytree(TEMPLATE_DIR, template)
    manifest_path = template / ".auxmem-manifest.json"
    rel = ".scripts/validate_auxmem.py"
    (template / rel).unlink()
    with pytest.raises(ValueError, match="hash mismatch|missing"):
        verify_bundled_template(template, manifest_path)


def test_verify_fails_on_unsupported_policy(tmp_path):
    template = tmp_path / "template"
    shutil.copytree(TEMPLATE_DIR, template)
    manifest_path = template / ".auxmem-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rel = next(iter(manifest["files"]))
    manifest["files"][rel]["policy"] = "replace-all"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported policy"):
        verify_bundled_template(template, manifest_path)


def test_verify_fails_when_managed_file_missing_from_manifest(tmp_path):
    template = tmp_path / "template"
    shutil.copytree(TEMPLATE_DIR, template)
    manifest_path = template / ".auxmem-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["files"][".scripts/validate_auxmem.py"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="missing from manifest"):
        verify_bundled_template(template, manifest_path)


def test_upgrade_up_to_date(tmp_auxmem):
    result = upgrade_mod.upgrade(tmp_auxmem)
    assert result["status"] == "up-to-date"


def test_upgrade_force_is_idempotent(tmp_auxmem):
    first = upgrade_mod.upgrade(tmp_auxmem, force=True)
    assert first["status"] == "upgraded"
    note_path = tmp_auxmem / "10-projects" / "seed-note.md"
    if note_path.exists():
        before = note_path.read_bytes()
    second = upgrade_mod.upgrade(tmp_auxmem, force=True)
    assert second["status"] == "upgraded"
    if note_path.exists():
        assert note_path.read_bytes() == before


def test_user_notes_unchanged_after_upgrade(tmp_auxmem):
    note = write_note(
        tmp_auxmem,
        "10-projects/user-owned.md",
        note_with_fm("Owned body.", **VALID_FM),
    )
    before = note.read_bytes()
    upgrade_mod.upgrade(tmp_auxmem, force=True)
    assert note.read_bytes() == before


def test_dry_run_makes_no_changes(tmp_auxmem):
    note = write_note(
        tmp_auxmem,
        "10-projects/dry-run.md",
        note_with_fm("Dry run body.", **VALID_FM),
    )
    before_tree = tree_bytes_snapshot(tmp_auxmem)
    result = upgrade_mod.upgrade(tmp_auxmem, force=True, dry_run=True)
    assert result["status"] == "dry-run"
    assert tree_bytes_snapshot(tmp_auxmem) == before_tree
    assert note.read_bytes() == before_tree[str(note.relative_to(tmp_auxmem))]


def test_dry_run_cli(tmp_auxmem):
    result = run_auxmem(["upgrade", "--dry-run", "--force", str(tmp_auxmem)])
    assert result.returncode == OK
    assert "dry-run" in result.stdout
    assert "Planned changes" in result.stdout


def test_dry_run_reports_validation_expectation(tmp_auxmem):
    result = upgrade_mod.upgrade(tmp_auxmem, force=True, dry_run=True)
    assert "post_validation_expected" in result


def test_upgrade_rolls_back_on_post_check_failure(tmp_auxmem, monkeypatch):
    tool = tmp_auxmem / ".scripts/validate_auxmem.py"
    before = tool.read_bytes()

    monkeypatch.setattr(
        upgrade_mod,
        "_run_post_checks",
        lambda _dest: PostCheckResult(1, "moc generation failed", 0, ""),
    )
    result = upgrade_mod.upgrade(tmp_auxmem, force=True)
    assert result["status"] == "failed"
    assert result["post_exit_code"] == OPERATION_FAILED
    assert tool.read_bytes() == before
    assert list((tmp_auxmem / ".auxmem" / "upgrade-failures").glob("*.log"))


def test_merge3_conflict_marks_file_and_exits_nonzero(tmp_path, monkeypatch):
    from auxmem.manifest import sha256_file

    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest)
    upgrade_mod.upgrade(dest, force=True)

    snap_text = (dest / ".auxmem/snapshot/AGENTS.md").read_text(encoding="utf-8")
    agents = dest / "AGENTS.md"
    agents.write_text(
        snap_text.replace("## Session bootstrap", "## User changed bootstrap"),
        encoding="utf-8",
    )

    fake_template = tmp_path / "template"
    shutil.copytree(upgrade_mod.TEMPLATE_DIR, fake_template)
    (fake_template / "AGENTS.md").write_text(
        snap_text.replace("## Session bootstrap", "## Template changed bootstrap"),
        encoding="utf-8",
    )
    manifest = json.loads((fake_template / ".auxmem-manifest.json").read_text(encoding="utf-8"))
    manifest["files"]["AGENTS.md"]["sha256"] = sha256_file(fake_template / "AGENTS.md")
    (fake_template / ".auxmem-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    monkeypatch.setattr(upgrade_mod, "TEMPLATE_DIR", fake_template)
    monkeypatch.setattr(upgrade_mod, "MANIFEST_SRC", fake_template / ".auxmem-manifest.json")

    result = upgrade_mod.upgrade(dest, force=True)
    assert "AGENTS.md" in result["conflicts"]
    assert "<<<<<<<" in agents.read_text(encoding="utf-8")
    assert result["post_exit_code"] == NON_CONFORMANT


def test_cli_exits_nonconformant_when_conflicts_remain(tmp_auxmem, monkeypatch):
    def fake_upgrade(dest, force=False, dry_run=False):
        return {
            "status": "upgraded",
            "from": "0.0.0",
            "to": "0.0.0",
            "changes": ["CONFLICT: AGENTS.md (1 conflict block(s); markers would be left in file)"],
            "conflicts": ["AGENTS.md"],
            "backup": str(tmp_auxmem / ".auxmem/backups/test"),
            "post_exit_code": NON_CONFORMANT,
            "post_phase": "merge conflicts",
            "post_detail": "1 file(s) need manual review",
        }

    monkeypatch.setattr(upgrade_mod, "upgrade", fake_upgrade)
    assert main(["upgrade", "--force", str(tmp_auxmem)]) == NON_CONFORMANT


def test_upgrade_preserves_custom_domains(tmp_auxmem):
    cfg = read_auxmem_config(tmp_auxmem)
    domains_before = dict(cfg["domains"])
    upgrade_mod.upgrade(tmp_auxmem, force=True)
    cfg_after = read_auxmem_config(tmp_auxmem)
    assert cfg_after["domains"] == domains_before


def test_upgrade_detects_edited_overwrite_tooling(tmp_auxmem):
    tool = tmp_auxmem / ".scripts/validate_auxmem.py"
    tool.write_text(tool.read_text(encoding="utf-8") + "\n# user patch\n", encoding="utf-8")
    plan = upgrade_mod.build_plan(tmp_auxmem, force=True)
    assert any("overwrite: .scripts/validate_auxmem.py" in c and "YOUR EDITS" in c for c in plan.changes)


def test_upgrade_rejects_corrupt_bundled_manifest(tmp_path, monkeypatch):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest)
    bad = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    rel = ".scripts/validate_auxmem.py"
    bad["files"][rel]["sha256"] = "0" * 64
    monkeypatch.setattr(upgrade_mod, "MANIFEST_SRC", tmp_path / "bad-manifest.json")
    (tmp_path / "bad-manifest.json").write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(upgrade_mod.UpgradeError, match="hash mismatch"):
        upgrade_mod.upgrade(dest, force=True)


def test_sequential_upgrades_safe(tmp_auxmem):
    upgrade_mod.upgrade(tmp_auxmem, force=True)
    upgrade_mod.upgrade(tmp_auxmem, force=True)
    result = upgrade_mod.upgrade(tmp_auxmem)
    assert result["status"] == "up-to-date"
