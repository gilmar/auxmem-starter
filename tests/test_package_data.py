"""Ensure packaged template and importer assets ship in the wheel."""

from __future__ import annotations

import os
import zipfile

import pytest

from tests.helpers import REPO_ROOT, build_wheel, wheel_members

TEMPLATE_ROOT = REPO_ROOT / "koinome" / "template"
IMPORTERS_ROOT = REPO_ROOT / "koinome" / "importers"

REQUIRED_WHEEL_PREFIXES = (
    "koinome/template/.koinome-manifest.json",
    "koinome/template/.gitignore",
    "koinome/template/.gitattributes",
    "koinome/template/bootstrap.sh",
    "koinome/template/.scripts/validate_corpus.py",
    "koinome/template/.scripts/check_corpus.py",
    "koinome/template/.scripts/koinome.config.json",
    "koinome/template/.scripts/gen_mocs.py",
    "koinome/template/.scripts/pre-commit",
    "koinome/template/.github/workflows/koinome-check.yml",
    "koinome/template/.skills/koinome-init/SKILL.md",
    "koinome/importers/seed_extract.py",
)


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory):
    dist = tmp_path_factory.mktemp("dist")
    return build_wheel(dist)


def test_wheel_contains_runtime_assets(built_wheel):
    members = wheel_members(built_wheel)
    missing = [prefix for prefix in REQUIRED_WHEEL_PREFIXES if prefix not in members]
    assert not missing, f"missing wheel entries: {missing}"


def test_wheel_contains_all_template_skills(built_wheel):
    members = wheel_members(built_wheel)
    skill_files = list((TEMPLATE_ROOT / ".skills").glob("*/SKILL.md"))
    assert skill_files, "expected template skills in source tree"
    missing = []
    for skill in skill_files:
        wheel_path = "koinome/" + skill.relative_to(REPO_ROOT / "koinome").as_posix()
        if wheel_path not in members:
            missing.append(wheel_path)
    assert not missing, f"missing skill files in wheel: {missing}"


def test_wheel_contains_importer_scripts(built_wheel):
    members = wheel_members(built_wheel)
    importer_files = list(IMPORTERS_ROOT.glob("*.py"))
    assert importer_files, "expected importer scripts in source tree"
    missing = []
    for script in importer_files:
        wheel_path = "koinome/" + script.relative_to(REPO_ROOT / "koinome").as_posix()
        if wheel_path not in members:
            missing.append(wheel_path)
    assert not missing, f"missing importer scripts in wheel: {missing}"


def test_wheel_includes_dot_directories(built_wheel):
    members = wheel_members(built_wheel)
    dot_prefixes = (
        "koinome/template/.scripts/",
        "koinome/template/.skills/",
        "koinome/template/.github/",
    )
    for prefix in dot_prefixes:
        assert any(m.startswith(prefix) for m in members), f"wheel missing files under {prefix}"


def test_bootstrap_sh_is_executable_in_wheel(built_wheel):
    with zipfile.ZipFile(built_wheel) as zf:
        info = zf.getinfo("koinome/template/bootstrap.sh")
        unix_mode = info.external_attr >> 16
        assert unix_mode & 0o111, f"bootstrap.sh not executable in wheel: {oct(unix_mode)}"


def test_package_data_sources_exist():
    """Every explicitly listed package-data glob must resolve to at least one file."""
    required_paths = [
        TEMPLATE_ROOT / ".koinome-manifest.json",
        TEMPLATE_ROOT / ".gitignore",
        TEMPLATE_ROOT / ".gitattributes",
        TEMPLATE_ROOT / "bootstrap.sh",
        TEMPLATE_ROOT / ".scripts" / "validate_corpus.py",
        TEMPLATE_ROOT / ".scripts" / "koinome.config.json",
        TEMPLATE_ROOT / ".scripts" / "check_corpus.py",
        TEMPLATE_ROOT / ".github" / "workflows" / "koinome-check.yml",
    ]
    missing = [str(p.relative_to(REPO_ROOT)) for p in required_paths if not p.is_file()]
    assert not missing, f"missing source package-data files: {missing}"

    skill_dirs = list((TEMPLATE_ROOT / ".skills").glob("*/SKILL.md"))
    assert skill_dirs, "expected at least one template skill"

    importer_scripts = list(IMPORTERS_ROOT.glob("*.py"))
    assert importer_scripts, "expected importer python scripts"

    assert os.access(TEMPLATE_ROOT / "bootstrap.sh", os.X_OK)
