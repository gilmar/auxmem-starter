"""Legacy AuxMem → Koinome migration tests."""

from __future__ import annotations

import json
from pathlib import Path

from koinome import upgrade as upgrade_mod
from koinome.exit_codes import OPERATION_FAILED
from koinome.paths import (
    AUXMEM_TO_KOINOME_RENAMES,
    CONFIG_LEGACY_AUXMEM,
    CONFIG_NEW,
    STATE_DIR_LEGACY,
    STATE_DIR_NEW,
    detect_legacy_auxmem,
    is_legacy_auxmem,
    migrate_legacy_layout,
    plan_legacy_migration,
    scan_user_notes_for_legacy_refs,
)
from koinome.upgrade import PostCheckResult
from tests.helpers import note_with_fm, scaffold_corpus, tree_bytes_snapshot, write_note


def _make_legacy_auxmem(dest: Path) -> Path:
    """Scaffold a corpus, then rewrite managed state to legacy AuxMem names."""
    scaffold_corpus(dest, name="legacy-corpus")

    # managed state directory
    koinome_dir = dest / STATE_DIR_NEW
    legacy_dir = dest / STATE_DIR_LEGACY
    if koinome_dir.exists():
        koinome_dir.rename(legacy_dir)

    manifest_root = dest / ".koinome-manifest.json"
    if manifest_root.exists():
        manifest_root.rename(dest / ".auxmem-manifest.json")

    for new_rel, old_rel in {v: k for k, v in AUXMEM_TO_KOINOME_RENAMES.items()}.items():
        new_path = dest / new_rel
        old_path = dest / old_rel
        if new_path.exists() and not old_path.exists():
            old_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.rename(old_path)

    snap = legacy_dir / "snapshot"
    if snap.is_dir():
        for new_rel, old_rel in {v: k for k, v in AUXMEM_TO_KOINOME_RENAMES.items()}.items():
            new_path = snap / new_rel
            old_path = snap / old_rel
            if new_path.exists() and not old_path.exists():
                old_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.rename(old_path)
        manifest = legacy_dir / "manifest.json"
        if manifest.is_file():
            text = manifest.read_text(encoding="utf-8")
            for old, new in AUXMEM_TO_KOINOME_RENAMES.items():
                text = text.replace(new, old)
            text = text.replace(".koinome/", ".auxmem/")
            manifest.write_text(text, encoding="utf-8")

    for skill_dir in (dest / ".skills").iterdir():
        if skill_dir.is_dir() and skill_dir.name.startswith("koinome-"):
            skill_dir.rename(dest / ".skills" / ("auxmem-" + skill_dir.name[8:]))

    return dest


def test_fresh_corpus_uses_koinome_paths(tmp_corpus):
    assert (tmp_corpus / CONFIG_NEW).is_file()
    assert (tmp_corpus / STATE_DIR_NEW / "manifest.json").is_file()
    assert not (tmp_corpus / CONFIG_LEGACY_AUXMEM).exists()
    assert not is_legacy_auxmem(tmp_corpus)


def test_detect_legacy_auxmem_folder(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    detected = detect_legacy_auxmem(dest)
    assert detected
    assert is_legacy_auxmem(dest)


def test_dry_run_legacy_migration_plans_renames(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    before = tree_bytes_snapshot(dest)
    result = upgrade_mod.upgrade(dest, force=True, dry_run=True)
    assert result["status"] == "dry-run"
    assert any("renamed:" in c for c in result["changes"])
    assert tree_bytes_snapshot(dest) == before


def test_migrate_unmodified_legacy_corpus(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    result = upgrade_mod.upgrade(dest, force=True)
    assert result["status"] == "upgraded"
    assert (dest / CONFIG_NEW).is_file()
    assert (dest / STATE_DIR_NEW / "manifest.json").is_file()
    assert not is_legacy_auxmem(dest)


def test_migration_preserves_user_notes_byte_for_byte(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    note = write_note(
        dest,
        "10-projects/user-owned.md",
        note_with_fm(
            "Owned body.",
            title="Owned",
            summary="User note preserved during migration.",
            type="project-doc",
            status="active",
            domain="projects",
            created="2026-07-04",
            updated="2026-07-04",
        ),
    )
    before = note.read_bytes()
    upgrade_mod.upgrade(dest, force=True)
    assert note.read_bytes() == before


def test_migration_preserves_user_edited_managed_guidance(tmp_path, monkeypatch):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    agents = dest / "AGENTS.md"
    snap = dest / STATE_DIR_LEGACY / "snapshot" / "AGENTS.md"
    edited = snap.read_text(encoding="utf-8").replace(
        "## Session bootstrap", "## User edited bootstrap"
    )
    agents.write_text(edited, encoding="utf-8")
    upgrade_mod.upgrade(dest, force=True)
    assert "## User edited bootstrap" in agents.read_text(encoding="utf-8")


def test_migration_rolls_back_on_failed_post_check(tmp_path, monkeypatch):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    tool = dest / ".scripts" / "validate_auxmem.py"
    before = tool.read_bytes()
    monkeypatch.setattr(
        upgrade_mod,
        "_run_post_checks",
        lambda _dest: PostCheckResult(1, "moc generation failed", 0, ""),
    )
    result = upgrade_mod.upgrade(dest, force=True)
    assert result["status"] == "failed"
    assert result["post_exit_code"] == OPERATION_FAILED
    restored = dest / ".scripts" / "validate_auxmem.py"
    if not restored.is_file():
        restored = dest / ".scripts" / "validate_corpus.py"
    assert restored.read_bytes() == before


def test_migration_remaps_manifest_paths(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    upgrade_mod.upgrade(dest, force=True)
    manifest = json.loads((dest / STATE_DIR_NEW / "manifest.json").read_text(encoding="utf-8"))
    joined = json.dumps(manifest)
    assert "auxmem" not in joined.lower()
    assert ".scripts/validate_corpus.py" in joined


def test_migration_reports_legacy_refs_in_user_notes(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    write_note(
        dest,
        "10-projects/legacy-link.md",
        note_with_fm(
            "Run `auxmem doctor` on this corpus.",
            title="Legacy link",
            summary="Note mentioning legacy auxmem command for migration reporting.",
            type="project-doc",
            status="active",
            domain="projects",
            created="2026-07-04",
            updated="2026-07-04",
        ),
    )
    refs = scan_user_notes_for_legacy_refs(dest)
    assert any(r["path"] == "10-projects/legacy-link.md" for r in refs)
    result = upgrade_mod.upgrade(dest, force=True)
    assert result.get("legacy_note_refs")


def test_plan_legacy_migration_lists_expected_renames(tmp_path):
    dest = tmp_path / "legacy"
    _make_legacy_auxmem(dest)
    planned = plan_legacy_migration(dest)
    assert any(".auxmem" in p for p in planned)
    report: list[str] = []
    migrate_legacy_layout(dest, report)
    assert (dest / CONFIG_NEW).is_file()


def test_new_corpus_has_no_active_auxmem_paths(tmp_corpus):
    for path in tmp_corpus.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        rel = str(path.relative_to(tmp_corpus))
        assert "auxmem" not in rel.lower(), rel
