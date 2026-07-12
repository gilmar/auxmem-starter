"""Scratch corpus lifecycle checks used by the repository gate."""

from __future__ import annotations

from tests.helpers import init_git_repo, read_corpus_config, run_git, run_koinome, validate_corpus


def test_scratch_corpus_has_domains_and_git(tmp_path):
    dest = tmp_path / "scratch"
    run_koinome(
        [
            "new",
            "--name",
            "scratch",
            "--path",
            str(dest),
            "--domain",
            "10-projects=projects",
            "--domain",
            "20-governance=governance",
        ]
    )
    cfg = read_corpus_config(dest)
    assert cfg["domains"] == {
        "10-projects": "projects",
        "20-governance": "governance",
    }
    init_git_repo(dest)
    status = run_git(["status", "--porcelain"], cwd=dest)
    assert status.returncode == 0


def test_scratch_corpus_validation_clean(tmp_path):
    dest = tmp_path / "scratch"
    run_koinome(
        [
            "new",
            "--name",
            "scratch",
            "--path",
            str(dest),
            "--domain",
            "10-projects=projects",
        ]
    )
    result = validate_corpus(dest)
    assert result.returncode == 0, result.stdout + result.stderr
