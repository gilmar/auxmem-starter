"""Documentation and guidance consistency (AUX-006)."""

from __future__ import annotations

import re

import pytest

from koinome.cli import build_parser
from koinome.scaffold import parse_domains
from tests.helpers import REPO_ROOT, scaffold_corpus

TEMPLATE = REPO_ROOT / "koinome/template"
SKILLS_DIR = TEMPLATE / ".skills"

CANONICAL_GUIDANCE = [
    TEMPLATE / "AGENTS.md",
    TEMPLATE / "docs" / "SYNTHESIS.md",
    TEMPLATE / ".skills" / "koinome-new-note" / "SKILL.md",
    TEMPLATE / ".skills" / "koinome-setup-domains" / "SKILL.md",
    TEMPLATE / ".skills" / "koinome-distill-seeds" / "SKILL.md",
    TEMPLATE / ".skills" / "koinome-synthesize" / "SKILL.md",
    REPO_ROOT / "koinome" / "importers" / "distill-seeds.md",
]

FORBIDDEN_IN_CANONICAL = [
    "10-data-hub",
    "20-governance",
    "30-team",
    "40-stakeholders",
    "50-exec",
    "Default set:",
    "newest wins",
    "Controlled `type`:",
    "Controlled `status`:",
]

AGENTS_DOC_REFS = [
    "docs/OPERATIONS.md",
    "docs/ARCHITECTURE.md",
    "docs/FIXING.md",
    "docs/CONFLICTS.md",
    "docs/SYNTHESIS.md",
    "90-templates/",
    "60-decisions/index.md",
    "72-tasks/todo.txt",
    "71-log/",
    "80-moc/",
    ".scripts/gen_mocs.py",
    ".scripts/validate_corpus.py",
    ".scripts/synthesis_status.py",
    ".scripts/graph_report.py",
]


def _skill_name(skill_md: str) -> str:
    match = re.search(r"^name:\s*(\S+)", skill_md, re.MULTILINE)
    assert match, "SKILL.md missing name: frontmatter"
    return match.group(1)


@pytest.mark.parametrize("path", CANONICAL_GUIDANCE, ids=lambda p: p.name)
def test_canonical_guidance_points_to_config(path):
    text = path.read_text(encoding="utf-8")
    assert ".scripts/koinome.config.json" in text, f"{path} must reference the config file"


@pytest.mark.parametrize("path", CANONICAL_GUIDANCE, ids=lambda p: p.name)
def test_no_hardcoded_vocab_in_canonical_guidance(path):
    text = path.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_IN_CANONICAL:
        assert forbidden not in text, f"{path} contains forbidden {forbidden!r}"


def test_agents_references_conflicts_doc():
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/CONFLICTS.md" in agents


def test_conflicts_doc_exists():
    assert (TEMPLATE / "docs" / "CONFLICTS.md").is_file()


def test_cli_commands_documented_and_exist():
    parser = build_parser()
    sub = parser._subparsers._group_actions[0].choices
    usage = (REPO_ROOT / "docs" / "USAGE.md").read_text(encoding="utf-8")
    for cmd in sub:
        assert f"## koinome {cmd}" in usage, f"USAGE.md missing section for koinome {cmd}"


def test_skills_exist_and_use_koinome_prefix():
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    assert skill_dirs, "no skills under template/.skills"
    for skill_dir in skill_dirs:
        assert skill_dir.name.startswith("koinome-"), skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file(), skill_dir
        name = _skill_name(skill_md.read_text(encoding="utf-8"))
        assert name == skill_dir.name, f"{skill_dir.name} frontmatter name is {name!r}"


def test_agents_referenced_template_paths_exist():
    for rel in AGENTS_DOC_REFS:
        path = TEMPLATE / rel.rstrip("/")
        if rel.endswith("/"):
            assert path.is_dir(), rel
        else:
            assert path.is_file(), rel


def test_readme_domain_examples_parse():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    domains = re.findall(r"--domain\s+(\S+)", readme)
    assert domains, "expected --domain examples in README"
    for spec in domains:
        parsed = parse_domains([spec])
        assert parsed, spec


def test_scaffolded_agents_matches_onboarding(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest)
    agents = (dest / "AGENTS.md").read_text(encoding="utf-8")
    assert ".scripts/koinome.config.json" in agents
    assert "docs/CONFLICTS.md" in agents
    for forbidden in FORBIDDEN_IN_CANONICAL:
        assert forbidden not in agents, forbidden
    config = (dest / ".scripts" / "koinome.config.json").read_text(encoding="utf-8")
    assert "project-doc" in config
    assert "10-projects" not in agents or "10-projects" in config
