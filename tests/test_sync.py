"""Validated sync with quarantine (AUX-005)."""

from __future__ import annotations

import subprocess

import pytest

from auxmem.exit_codes import CONFLICT, OK, OPERATION_FAILED
from tests.helpers import (
    REPO_ROOT,
    attach_bare_remote,
    clone_from_bare,
    commit_all_valid,
    gen_mocs,
    git_add,
    git_branches,
    note_with_fm,
    run_cmd,
    run_git,
    run_sync,
    scaffold_auxmem,
    write_note,
)

VALID_FM = dict(
    title="Sync note",
    summary="Concrete nouns for sync integrity tests in this auxmem folder.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


@pytest.fixture
def synced_auxmem(tmp_path, bare_remote):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest)
    commit_all_valid(dest)
    attach_bare_remote(dest, bare_remote)
    return dest


def _note(rel: str, body: str = "Body.", **fm) -> str:
    return note_with_fm(body, **{**VALID_FM, **fm})


def _add_valid_note(auxmem, rel: str, body: str = "Body.") -> None:
    write_note(auxmem, rel, _note(rel, body=body))
    gen_mocs(auxmem)
    git_add(auxmem, "-A")


def test_sync_script_delegates_to_python():
    proc = subprocess.run(
        ["/bin/bash", "-n", "auxmem/template/.scripts/auxmem-sync.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_sync_pushes_valid_changes(synced_auxmem, bare_remote):
    _add_valid_note(synced_auxmem, "10-projects/pushed.md")
    result = run_sync(synced_auxmem)
    assert result.returncode == OK, result.stdout + result.stderr
    remote_log = run_cmd(["git", "-C", str(bare_remote), "log", "-1", "--oneline"])
    assert "pushed.md" in remote_log.stdout or "sync(" in remote_log.stdout


def test_sync_quarantines_invalid_pending(synced_auxmem, bare_remote):
    tip_before = run_git(["rev-parse", "HEAD"], cwd=synced_auxmem).stdout.strip()
    write_note(
        synced_auxmem,
        "10-projects/invalid.md",
        _note("10-projects/invalid.md", type="bad-type"),
    )
    result = run_sync(synced_auxmem)
    assert result.returncode == CONFLICT, result.stdout + result.stderr
    tip_after = run_git(["rev-parse", "HEAD"], cwd=synced_auxmem).stdout.strip()
    assert tip_before == tip_after
    assert not (synced_auxmem / "10-projects/invalid.md").exists()
    remote_branches = git_branches(bare_remote, all_refs=True)
    assert any("sync-invalid/" in name for name in remote_branches)
    alerts = list((synced_auxmem / "00-inbox").glob("sync-invalid-*.md"))
    assert len(alerts) == 1


def test_sync_uses_current_branch(synced_auxmem, bare_remote):
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=synced_auxmem).stdout.strip()
    if branch != "master":
        run_git(["branch", "-m", branch, "master"], cwd=synced_auxmem)
        run_git(["push", "-u", "origin", "master"], cwd=synced_auxmem)
        if branch != "master":
            run_git(["push", "origin", "--delete", branch], cwd=synced_auxmem)
    _add_valid_note(synced_auxmem, "10-projects/on-master.md")
    result = run_sync(synced_auxmem)
    assert result.returncode == OK, result.stdout + result.stderr
    assert run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=synced_auxmem).stdout.strip() == "master"


def test_sync_lock_contention(synced_auxmem):
    lock = synced_auxmem / ".git" / "auxmem-sync.lock"
    lock.mkdir()
    try:
        result = run_sync(synced_auxmem)
        assert result.returncode == OPERATION_FAILED
        assert "another sync is running" in result.stdout
    finally:
        lock.rmdir()


def test_sync_rebase_conflict_quarantines(tmp_path, bare_remote):
    primary = tmp_path / "primary"
    scaffold_auxmem(primary)
    write_note(primary, "10-projects/shared.md", _note("10-projects/shared.md", body="line one\n"))
    commit_all_valid(primary, "seed")
    attach_bare_remote(primary, bare_remote)

    secondary = clone_from_bare(bare_remote, tmp_path / "secondary")
    (primary / "10-projects/shared.md").write_text(
        _note("10-projects/shared.md", body="line from primary\n"),
        encoding="utf-8",
    )
    gen_mocs(primary)
    git_add(primary, "-A")
    run_git(["commit", "-m", "primary edit"], cwd=primary)
    run_git(["push", "origin", "HEAD"], cwd=primary)

    (secondary / "10-projects/shared.md").write_text(
        _note("10-projects/shared.md", body="line from secondary\n"),
        encoding="utf-8",
    )
    gen_mocs(secondary)
    tip_before = run_git(["rev-parse", "HEAD"], cwd=secondary).stdout.strip()
    result = run_sync(secondary)
    assert result.returncode == CONFLICT, result.stdout + result.stderr
    remote_branches = git_branches(bare_remote, all_refs=True)
    assert any("sync-conflict/" in name for name in remote_branches)
    alerts = list((secondary / "00-inbox").glob("sync-conflict-*.md"))
    assert len(alerts) == 1
    tip_after = run_git(["rev-parse", "HEAD"], cwd=secondary).stdout.strip()
    assert tip_before != tip_after
