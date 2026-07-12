"""Pre-commit staged snapshot gate (AUX-003)."""

from __future__ import annotations

import subprocess

import pytest

from tests.helpers import (
    REPO_ROOT,
    git_add,
    init_git_repo,
    note_with_fm,
    run_git,
    run_staged_snapshot_check,
    scaffold_corpus,
    write_note,
)

VALID_FM = dict(
    title="Target note",
    summary="Concrete nouns for staged snapshot gate tests in this corpus.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


@pytest.fixture
def git_corpus(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    init_git_repo(dest)
    run_git(["add", "-A"], cwd=dest)
    run_git(["commit", "-m", "initial"], cwd=dest)
    return dest


def _note(rel: str, body: str = "Body.", **fm) -> str:
    return note_with_fm(body, **{**VALID_FM, **fm})


def test_no_staged_corpus_changes_passes(git_corpus):
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_staged_valid_note_passes(git_corpus):
    write_note(git_corpus, "10-projects/new.md", _note("10-projects/new.md"))
    run_git(["add", "10-projects/new.md"], cwd=git_corpus)
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    run_git(["add", "80-moc"], cwd=git_corpus)
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_staged_invalid_note_fails(git_corpus):
    write_note(
        git_corpus,
        "10-projects/bad.md",
        _note("10-projects/bad.md", type="not-a-type"),
    )
    git_add(git_corpus, "10-projects/bad.md")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode != 0
    assert "not in controlled vocabulary" in result.stdout + result.stderr


def test_staged_valid_with_invalid_unstaged_passes(git_corpus):
    write_note(git_corpus, "10-projects/good.md", _note("10-projects/good.md"))
    git_add(git_corpus, "10-projects/good.md")
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    git_add(git_corpus, "80-moc")
    # Invalid note exists only in the working tree, not in the index.
    write_note(
        git_corpus,
        "10-projects/bad-unstaged.md",
        _note("10-projects/bad-unstaged.md", type="bad-type"),
    )
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_staged_invalid_with_valid_unstaged_fails(git_corpus):
    write_note(git_corpus, "10-projects/staged-bad.md", _note("10-projects/staged-bad.md", type="bad"))
    git_add(git_corpus, "10-projects/staged-bad.md")
    write_note(git_corpus, "10-projects/unstaged-good.md", _note("10-projects/unstaged-good.md"))
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode != 0


def test_staged_deletion_breaks_unchanged_inbound_link(git_corpus):
    write_note(git_corpus, "10-projects/target.md", _note("10-projects/target.md"))
    write_note(
        git_corpus,
        "10-projects/linker.md",
        _note("10-projects/linker.md", body="See [target](target.md)."),
    )
    run_git(["add", "10-projects/target.md", "10-projects/linker.md"], cwd=git_corpus)
    run_git(["commit", "-m", "add notes"], cwd=git_corpus)
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    run_git(["add", "80-moc"], cwd=git_corpus)
    run_git(["commit", "-m", "mocs"], cwd=git_corpus)

    run_git(["rm", "10-projects/target.md"], cwd=git_corpus)
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode != 0
    assert "broken internal link" in result.stdout + result.stderr


def test_staged_rename_with_corrected_links_passes(git_corpus):
    write_note(git_corpus, "10-projects/old-name.md", _note("10-projects/old-name.md"))
    run_git(["add", "10-projects/old-name.md"], cwd=git_corpus)
    run_git(["commit", "-m", "note"], cwd=git_corpus)
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    run_git(["add", "80-moc"], cwd=git_corpus)
    run_git(["commit", "-m", "mocs"], cwd=git_corpus)

    run_git(["mv", "10-projects/old-name.md", "10-projects/new-name.md"], cwd=git_corpus)
    git_add(git_corpus, "10-projects/new-name.md")
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    git_add(git_corpus, "80-moc")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_staged_rename_without_corrected_links_fails(git_corpus):
    write_note(git_corpus, "10-projects/old.md", _note("10-projects/old.md"))
    write_note(
        git_corpus,
        "10-projects/ref.md",
        _note("10-projects/ref.md", body="[x](old.md)"),
    )
    run_git(["add", "10-projects"], cwd=git_corpus)
    run_git(["commit", "-m", "notes"], cwd=git_corpus)
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    run_git(["add", "80-moc"], cwd=git_corpus)
    run_git(["commit", "-m", "mocs"], cwd=git_corpus)

    run_git(["mv", "10-projects/old.md", "10-projects/renamed.md"], cwd=git_corpus)
    git_add(git_corpus, "10-projects/renamed.md")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode != 0
    assert "broken internal link" in result.stdout + result.stderr


def test_untracked_invalid_note_does_not_block(git_corpus):
    write_note(
        git_corpus,
        "10-projects/untracked-bad.md",
        _note("10-projects/untracked-bad.md", type="bad"),
    )
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0


def test_staged_stale_moc_fails(git_corpus):
    write_note(git_corpus, "10-projects/new-note.md", _note("10-projects/new-note.md"))
    git_add(git_corpus, "10-projects/new-note.md")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode != 0
    assert "MOC" in result.stdout + result.stderr


def test_staged_regenerated_moc_passes(git_corpus):
    write_note(git_corpus, "10-projects/fresh.md", _note("10-projects/fresh.md"))
    git_add(git_corpus, "10-projects/fresh.md")
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    git_add(git_corpus, "80-moc")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_filename_with_spaces(git_corpus):
    rel = "10-projects/my note.md"
    write_note(git_corpus, rel, _note(rel, title="Spaced title"))
    git_add(git_corpus, rel)
    subprocess.run(["python3", ".scripts/gen_mocs.py"], cwd=git_corpus, check=True, capture_output=True)
    git_add(git_corpus, "80-moc")
    result = run_staged_snapshot_check(git_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_pre_commit_hook_bash_syntax():
    proc = subprocess.run(
        ["/bin/bash", "-n", "koinome/template/.scripts/pre-commit"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
