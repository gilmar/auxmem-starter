"""Ensure packaged template and importer assets ship in the wheel."""

from __future__ import annotations

import pytest

from tests.helpers import REPO_ROOT, build_wheel, wheel_members

REQUIRED_WHEEL_PREFIXES = (
    "auxmem/template/.auxmem-manifest.json",
    "auxmem/template/.scripts/validate_auxmem.py",
    "auxmem/template/.scripts/auxmem.config.json",
    "auxmem/template/bootstrap.sh",
    "auxmem/template/.skills/auxmem-init/SKILL.md",
    "auxmem/importers/seed_extract.py",
    "auxmem/importers/migrate_obsidian.py",
)


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory):
    dist = tmp_path_factory.mktemp("dist")
    return build_wheel(dist)


def test_wheel_contains_runtime_assets(built_wheel):
    members = wheel_members(built_wheel)
    missing = [prefix for prefix in REQUIRED_WHEEL_PREFIXES if prefix not in members]
    assert not missing, f"missing wheel entries: {missing}"


def test_package_data_sources_exist():
    """Every explicitly listed package-data glob must resolve to at least one file."""
    template = REPO_ROOT / "auxmem" / "template"
    required_paths = [
        template / ".auxmem-manifest.json",
        template / ".gitignore",
        template / ".gitattributes",
        template / "bootstrap.sh",
        template / ".scripts" / "validate_auxmem.py",
        template / ".scripts" / "auxmem.config.json",
    ]
    missing = [str(p.relative_to(REPO_ROOT)) for p in required_paths if not p.is_file()]
    assert not missing, f"missing source package-data files: {missing}"

    skill_dirs = list((template / ".skills").glob("*/SKILL.md"))
    assert skill_dirs, "expected at least one template skill"

    importer_scripts = list((REPO_ROOT / "auxmem" / "importers").glob("*.py"))
    assert importer_scripts, "expected importer python scripts"
