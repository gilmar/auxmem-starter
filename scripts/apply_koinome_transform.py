#!/usr/bin/env python3
"""One-shot AuxMem → Koinome mechanical transform. Maintainer use during 2.0 rename."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", ".venv", "build", "dist", "__pycache__", ".pytest_cache", "auxmem.egg-info", "koinome.egg-info"}
SKIP_FILES = {
    ROOT / "scripts" / "apply_koinome_transform.py",
    ROOT / "scripts" / "apply_rebrand.py",
    ROOT / "docs" / "plans" / "open" / "koinome-transform-plan.md",
    ROOT / "docs" / "plans" / "closed" / "rebrand-plan.md",
}

FILE_RENAMES: list[tuple[str, str]] = [
    (".auxmem-manifest.json", ".koinome-manifest.json"),
    (".scripts/auxmem.config.json", ".scripts/koinome.config.json"),
    (".scripts/validate_corpus.py", ".scripts/validate_corpus.py"),
    (".scripts/check_auxmem.py", ".scripts/check_corpus.py"),
    (".scripts/auxmem_sync.py", ".scripts/koinome_sync.py"),
    (".scripts/auxmem-sync.sh", ".scripts/koinome-sync.sh"),
    (".scripts/auxmem-sync.systemd", ".scripts/koinome-sync.systemd"),
    (".github/workflows/auxmem-check.yml", ".github/workflows/koinome-check.yml"),
    ("60-decisions/adr-0001-auxmem-structure.md", "60-decisions/adr-0001-corpus-structure.md"),
]

SKILL_PREFIX_OLD = "auxmem-"
SKILL_PREFIX_NEW = "koinome-"

CONTENT_REPLACEMENTS: list[tuple[str, str]] = [
    ("AuxmemPathError", "CorpusPathError"),
    ("resolve_auxmem", "resolve_corpus"),
    ("scaffold_auxmem", "scaffold_corpus"),
    ("run_auxmem", "run_koinome"),
    ("read_auxmem_config", "read_corpus_config"),
    ("write_auxmem_state", "write_corpus_state"),
    ("load_auxmem_domains", "load_corpus_domains"),
    ("__AUXMEM_NAME__", "__CORPUS_NAME__"),
    (".auxmem-manifest.json", ".koinome-manifest.json"),
    (".auxmem/", ".koinome/"),
    (".auxmem", ".koinome"),
    ("auxmem.config.json", "koinome.config.json"),
    ("validate_corpus.py", "validate_corpus.py"),
    ("check_auxmem.py", "check_corpus.py"),
    ("auxmem_sync.py", "koinome_sync.py"),
    ("auxmem-sync.sh", "koinome-sync.sh"),
    ("auxmem-sync.systemd", "koinome-sync.systemd"),
    ("auxmem-sync.service", "koinome-sync.service"),
    ("auxmem-sync.timer", "koinome-sync.timer"),
    ("auxmem-sync.lock.d", "koinome-sync.lock.d"),
    ("auxmem-check.yml", "koinome-check.yml"),
    ("adr-0001-auxmem-structure.md", "adr-0001-corpus-structure.md"),
    ("AuxMem Manager", "Koinome CLI"),
    ("auxmem-cli", "koinome-cli"),
    ("from auxmem", "from koinome"),
    ("import auxmem", "import koinome"),
    ('"auxmem.cli"', '"koinome.cli"'),
    ("auxmem/template", "koinome/template"),
    ('prog="auxmem"', 'prog="koinome"'),
    ('metavar="AUXMEM"', 'metavar="CORPUS"'),
    ('name = "auxmem"', 'name = "koinome"'),
    ('packages = ["auxmem"]', 'packages = ["koinome"]'),
    ('auxmem = "auxmem.cli:main"', 'koinome = "koinome.cli:main"'),
    ("[tool.setuptools.package-data]\nauxmem", "[tool.setuptools.package-data]\nkoinome"),
    ("auxmem-*.whl", "koinome-*.whl"),
    ("AUXMEM_ROOT", "CORPUS_ROOT"),
    ("auxmem-upgrade-", "koinome-upgrade-"),
    ("test@auxmem", "test@koinome"),
    ("auxmem-test", "koinome-test"),
    ("test-auxmem", "test-corpus"),
    ("validator-auxmem", "validator-corpus"),
    ("tmp_auxmem", "tmp_corpus"),
    ("reference auxmems", "reference corpora"),
    ("reference auxmem", "reference corpus"),
    ("## auxmem ", "## koinome "),
    ("AuxMem (auxiliary memory)", "Koinome"),
    ("AuxMem", "Koinome"),
    ("auxiliary memory", "durable knowledge"),
]

PROSE_PATTERNS: list[tuple[str, str]] = [
    (r"\bstaging corpus\b", "staging area"),
    (r"\ban auxmem\b", "a corpus"),
    (r"\bauxmems\b", "corpora"),
    (r"\bthe auxmem's\b", "the corpus's"),
    (r"\bthe auxmem\b", "the corpus"),
    (r"\ba auxmem\b", "a corpus"),
    (r"\bYour auxmem\b", "Your corpus"),
    (r"\byour auxmem\b", "your corpus"),
    (r"\bthis auxmem\b", "this corpus"),
    (r"\bexisting auxmem\b", "existing corpus"),
    (r"\bnew auxmem\b", "new corpus"),
    (r"\btarget auxmem\b", "target corpus"),
    (r"\binto the auxmem\b", "into the corpus"),
    (r"\binto your auxmem\b", "into your corpus"),
    (r"\bfrom the auxmem\b", "from the corpus"),
    (r"\bin the auxmem\b", "in the corpus"),
    (r"\binto an auxmem\b", "into a corpus"),
    (r"\bfrom an auxmem\b", "from a corpus"),
    (r"\bfor an auxmem\b", "for a corpus"),
    (r"\bfor the auxmem\b", "for the corpus"),
    (r"\bEach auxmem\b", "Each corpus"),
    (r"\bevery auxmem\b", "every corpus"),
    (r"\bcreate an auxmem\b", "create a corpus"),
    (r"\bcreate a auxmem\b", "create a corpus"),
    (r"\bno auxmem\b", "no corpus"),
    (r"\bany auxmem\b", "any corpus"),
    (r"\bauxmem folder\b", "corpus folder"),
    (r"\bauxmem root\b", "corpus root"),
    (r"\bauxmem template\b", "Koinome template"),
    (r"\bauxmem validation\b", "corpus validation"),
    (r"\bauxmem-init\b", "koinome-init"),
    (r"\bauxmem-setup-domains\b", "koinome-setup-domains"),
    (r"\bauxmem-new-note\b", "koinome-new-note"),
    (r"\bauxmem-adr\b", "koinome-adr"),
    (r"\bauxmem-todo\b", "koinome-todo"),
    (r"\bauxmem-synthesize\b", "koinome-synthesize"),
    (r"\bauxmem-session-close\b", "koinome-session-close"),
    (r"\bauxmem-distill-seeds\b", "koinome-distill-seeds"),
    (r"\bauxmem-fix-validation\b", "koinome-fix-validation"),
    (r"\bauxmem-weekly-review\b", "koinome-weekly-review"),
    (r"\bthe `auxmem` CLI\b", "the `koinome` CLI"),
    (r"\b`auxmem` command\b", "`koinome` command"),
    (r"\b`auxmem`\b", "`koinome`"),
    (r"\bauxmem subcommands\b", "koinome subcommands"),
    (r"\bauxmem new\b", "koinome new"),
    (r"\bauxmem check\b", "koinome check"),
    (r"\bauxmem doctor\b", "koinome doctor"),
    (r"\bauxmem upgrade\b", "koinome upgrade"),
    (r"\bauxmem seed\b", "koinome seed"),
    (r"\bauxmem --help\b", "koinome --help"),
    (r"\buv tool install auxmem\b", "uv tool install koinome"),
    (r"\bpipx install auxmem\b", "pipx install koinome"),
    (r"\bpython3 auxmem-cli\b", "python3 koinome-cli"),
    (r"\b@auxmem\b", "@koinome"),
]

SKILL_RENAMES = [
    "init",
    "setup-domains",
    "new-note",
    "adr",
    "todo",
    "synthesize",
    "session-close",
    "distill-seeds",
    "fix-validation",
    "weekly-review",
]


def should_skip(path: Path) -> bool:
    if path in SKIP_FILES:
        return True
    for part in path.parts:
        if part in SKIP_DIRS:
            return True
    if path.suffix in (".png", ".jpg", ".pyc", ".ico"):
        return True
    if path.name.endswith(".egg-info"):
        return True
    return False


def rename_skill_dirs(root: Path) -> list[Path]:
    changed: list[Path] = []
    for skill_root in (root / ".skills",):
        if not skill_root.is_dir():
            continue
        for old_dir in sorted(skill_root.iterdir()):
            if old_dir.is_dir() and old_dir.name.startswith(SKILL_PREFIX_OLD):
                new_name = SKILL_PREFIX_NEW + old_dir.name[len(SKILL_PREFIX_OLD) :]
                new_dir = skill_root / new_name
                if not new_dir.exists():
                    old_dir.rename(new_dir)
                    changed.append(new_dir)
    for provider in (".cursor", ".codex", ".claude", ".gemini"):
        prov_skills = root / provider / "skills"
        if not prov_skills.is_dir():
            continue
        for old_dir in sorted(prov_skills.iterdir()):
            if old_dir.is_dir() and old_dir.name.startswith(SKILL_PREFIX_OLD):
                new_name = SKILL_PREFIX_NEW + old_dir.name[len(SKILL_PREFIX_OLD) :]
                new_dir = prov_skills / new_name
                if not new_dir.exists():
                    old_dir.rename(new_dir)
                    changed.append(new_dir)
    return changed


def rename_managed_files(root: Path) -> list[Path]:
    changed: list[Path] = []
    for old_suffix, new_suffix in FILE_RENAMES:
        for old_path in root.rglob(old_suffix.split("/")[-1] if "/" not in old_suffix else Path(old_suffix).name):
            if not old_path.is_file():
                continue
            rel = str(old_path.relative_to(root)).replace("\\", "/")
            if not rel.endswith(old_suffix):
                continue
            new_rel = rel[: -len(old_suffix)] + new_suffix
            new_path = root / new_rel
            if old_path != new_path and not new_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.rename(new_path)
                changed.append(new_path)
    # rename .auxmem directories
    for old_dir in sorted(root.rglob(".auxmem")):
        if not old_dir.is_dir():
            continue
        new_dir = old_dir.parent / ".koinome"
        if not new_dir.exists():
            old_dir.rename(new_dir)
            changed.append(new_dir)
    return changed


def apply_content(text: str) -> str:
    for old, new in CONTENT_REPLACEMENTS:
        text = text.replace(old, new)
    for pattern, repl in PROSE_PATTERNS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    for skill in SKILL_RENAMES:
        text = text.replace(f"auxmem-{skill}", f"koinome-{skill}")
    return text


def process_file(path: Path) -> bool:
    if should_skip(path) or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    new_text = apply_content(text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> None:
    # top-level renames
    pkg_old = ROOT / "auxmem"
    pkg_new = ROOT / "koinome"
    if pkg_old.is_dir() and not pkg_new.exists():
        pkg_old.rename(pkg_new)
        print(f"renamed {pkg_old.name}/ -> {pkg_new.name}/")

    cli_old = ROOT / "auxmem-cli"
    cli_new = ROOT / "koinome-cli"
    if cli_old.is_file() and not cli_new.exists():
        cli_old.rename(cli_new)
        print(f"renamed {cli_old.name} -> {cli_new.name}")

    # managed file and skill renames under repo
    for sub in [ROOT, ROOT / "koinome" / "template", ROOT / "examples"]:
        if sub.is_dir():
            rename_managed_files(sub)
            rename_skill_dirs(sub)

    changed: list[Path] = []
    for path in sorted(ROOT.rglob("*")):
        if process_file(path):
            changed.append(path.relative_to(ROOT))
    print(f"updated content in {len(changed)} file(s)")


if __name__ == "__main__":
    main()
