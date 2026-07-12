"""Atomic, repeatable imports with fixture coverage (AUX-009)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from auxmem import import_atomic, importers
from auxmem.exit_codes import NON_CONFORMANT, OK
from auxmem.import_atomic import resolves_within_root
from tests.helpers import REPO_ROOT, scaffold_auxmem, tree_bytes_snapshot

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "imports"
SEED_EXTRACT = REPO_ROOT / "auxmem" / "importers" / "seed_extract.py"
OBSIDIAN_VAULT = FIXTURES / "obsidian_vault"
MAP_FILE = FIXTURES / "obsidian_map.json"


@pytest.fixture
def import_auxmem(tmp_path):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest)
    return dest


def _seed(args: list[str], *, staging: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SEED_EXTRACT), *args, "--out", staging],
        capture_output=True,
        text=True,
    )


def _content_snapshot(root):
    snap = tree_bytes_snapshot(root)
    return {k: v for k, v in snap.items() if not k.startswith(".auxmem/")}


@pytest.mark.parametrize(
    "fixture,provider,expected_min",
    [
        ("claude_minimal.json", "claude", 1),
        ("chatgpt_duplicate_titles.json", "chatgpt", 2),
        ("chatgpt_branched.json", "chatgpt", 1),
        ("chatgpt_multimodal.json", "chatgpt", 1),
        ("gemini_minimal.json", "gemini", 1),
    ],
)
def test_seed_extract_providers(tmp_path, fixture, provider, expected_min):
    staging = tmp_path / "staging"
    proc = _seed([str(FIXTURES / fixture), "--provider", provider, "--min-messages", "1"], staging=staging)
    assert proc.returncode == 0, proc.stderr
    written = list((staging / provider).glob("*.md"))
    assert len(written) >= expected_min
    assert (staging / "index.md").is_file()


def test_seed_extract_drops_empty_conversations(tmp_path):
    staging = tmp_path / "staging"
    proc = _seed(
        [str(FIXTURES / "chatgpt_empty.json"), "--provider", "chatgpt", "--min-messages", "2"],
        staging=staging,
    )
    assert proc.returncode == 0, proc.stderr
    assert list((staging / "chatgpt").glob("*.md")) == []


def test_seed_extract_malformed_json_fails(tmp_path):
    staging = tmp_path / "staging"
    proc = _seed([str(FIXTURES / "malformed.json")], staging=staging)
    assert proc.returncode != 0


def test_seed_extract_duplicate_titles_are_numbered(tmp_path):
    staging = tmp_path / "staging"
    proc = _seed(
        [str(FIXTURES / "chatgpt_duplicate_titles.json"), "--provider", "chatgpt", "--min-messages", "1"],
        staging=staging,
    )
    assert proc.returncode == 0, proc.stderr
    names = sorted(p.name for p in (staging / "chatgpt").glob("*.md"))
    assert len(names) == 2
    assert names[0] != names[1]


def test_obsidian_dry_run_makes_no_changes(import_auxmem):
    before = _content_snapshot(import_auxmem)
    rc, out, err = importers.migrate_obsidian_single(
        OBSIDIAN_VAULT, import_auxmem, map_file=MAP_FILE, dry_run=True
    )
    assert rc == OK, out + err
    assert _content_snapshot(import_auxmem) == before
    assert "->" in out


def test_obsidian_import_applies_valid_candidate(import_auxmem):
    rc, out, err = importers.migrate_obsidian_single(
        OBSIDIAN_VAULT, import_auxmem, map_file=MAP_FILE, dry_run=False
    )
    assert rc == OK, out + err
    imported = import_auxmem / "00-inbox" / "import" / "simple.md"
    assert imported.is_file()
    assert (import_auxmem / "10-projects" / "nested.md").is_file()
    assert (import_auxmem / "00-inbox" / "migration-report.md").is_file()


def test_failed_import_leaves_target_unchanged(import_auxmem, monkeypatch):
    before = _content_snapshot(import_auxmem)

    def fail_validate(_auxmem):
        return NON_CONFORMANT, "validation failed for test"

    monkeypatch.setattr(import_atomic, "_run_validate_and_moc", fail_validate)
    rc, out, err = importers.migrate_obsidian_single(
        OBSIDIAN_VAULT, import_auxmem, map_file=MAP_FILE, dry_run=False
    )
    assert rc == NON_CONFORMANT
    assert _content_snapshot(import_auxmem) == before
    assert (import_auxmem / ".auxmem" / "import-failures" / "latest.log").is_file()


def test_path_traversal_blocked(import_auxmem):
    assert not resolves_within_root(import_auxmem, "../outside.md")
    assert resolves_within_root(import_auxmem, "10-projects/safe.md")


def test_reimport_is_deterministic(import_auxmem):
    importers.migrate_obsidian_single(OBSIDIAN_VAULT, import_auxmem, map_file=MAP_FILE)
    first = (import_auxmem / "00-inbox" / "import" / "simple.md").read_bytes()
    importers.migrate_obsidian_single(OBSIDIAN_VAULT, import_auxmem, map_file=MAP_FILE)
    second = (import_auxmem / "00-inbox" / "import" / "simple.md").read_bytes()
    assert first == second
