"""Pytest fixtures for Koinome repository tests."""

from __future__ import annotations

import pytest

from tests.helpers import REPO_ROOT, create_bare_remote, init_git_repo, scaffold_corpus


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture
def tmp_corpus(tmp_path):
    """Fresh scaffolded corpus with default domains and bootstrap completed."""
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    return dest


@pytest.fixture
def tmp_corpus_git(tmp_corpus):
    """Scaffolded corpus with an initialized git repository."""
    init_git_repo(tmp_corpus)
    return tmp_corpus


@pytest.fixture
def bare_remote(tmp_path):
    return create_bare_remote(tmp_path / "remote.git")


@pytest.fixture
def validator_corpus(tmp_path):
    """Scaffolded corpus with domains for validator-focused tests."""
    dest = tmp_path / "validator-corpus"
    scaffold_corpus(dest)
    return dest