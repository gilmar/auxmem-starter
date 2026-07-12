"""Provider export seeding with fixture coverage."""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests.helpers import REPO_ROOT

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "imports"
SEED_EXTRACT = REPO_ROOT / "auxmem" / "importers" / "seed_extract.py"


def _seed(args: list[str], *, staging: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SEED_EXTRACT), *args, "--out", staging],
        capture_output=True,
        text=True,
    )


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
