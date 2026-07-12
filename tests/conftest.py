"""Pytest fixtures for AuxMem repository tests."""

from __future__ import annotations

import pytest

from tests.helpers import REPO_ROOT, create_bare_remote, init_git_repo, scaffold_auxmem


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture
def tmp_auxmem(tmp_path):
    """Fresh scaffolded auxmem with default domains and bootstrap completed."""
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest)
    return dest


@pytest.fixture
def tmp_auxmem_git(tmp_auxmem):
    """Scaffolded auxmem with an initialized git repository."""
    init_git_repo(tmp_auxmem)
    return tmp_auxmem


@pytest.fixture
def bare_remote(tmp_path):
    return create_bare_remote(tmp_path / "remote.git")


@pytest.fixture
def validator_auxmem(tmp_path):
    """Scaffolded auxmem with domains for validator-focused tests."""
    dest = tmp_path / "validator-auxmem"
    scaffold_auxmem(dest)
    return dest
