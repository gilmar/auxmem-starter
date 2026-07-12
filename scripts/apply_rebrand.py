#!/usr/bin/env python3
"""One-shot mechanical rebrand replacements. Maintainer use during 2.0 rebrand."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP = {
    ROOT / "docs" / "REBRAND-PLAN.md",
    ROOT / "scripts" / "apply_rebrand.py",
    ROOT / "auxmem_starter.egg-info",
    ROOT / "build",
    ROOT / ".git",
}

MECHANICAL = [
    (".scripts/vault.config.json", ".scripts/auxmem.config.json"),
    ("vault.config.json", "auxmem.config.json"),
    ("validate_vault.py", "validate_auxmem.py"),
    ("vault-sync.sh", "auxmem-sync.sh"),
    ("vault-sync.systemd", "auxmem-sync.systemd"),
    ("vault-sync.service", "auxmem-sync.service"),
    ("vault-sync.timer", "auxmem-sync.timer"),
    ("vault-sync.lock.d", "auxmem-sync.lock.d"),
    ("[vault-sync ", "[auxmem-sync "),
    ("adr-0001-vault-structure", "adr-0001-auxmem-structure"),
    ("--vault-config", "--auxmem-config"),
    ("load_vault_domains", "load_auxmem_domains"),
    ("VAULT_ROOT", "AUXMEM_ROOT"),
    ("__VAULT_NAME__", "__AUXMEM_NAME__"),
    ("$HOME/vault", "$HOME/auxmem"),
    ("~/vault", "~/auxmem"),
    ("auxmem-starter", "AuxMem"),
    ("name = \"AuxMem\"", "name = \"auxmem\""),  # fix pyproject over-replace
]

# Never skip lines during vault→auxmem prose replacement.
PRESERVE_LINE = re.compile(r"$^")


def should_skip(path: Path) -> bool:
    for s in SKIP:
        if s in path.parents or path == s:
            return True
    if path.suffix in (".png", ".jpg", ".pyc") or path.name.endswith(".egg-info"):
        return True
    if "egg-info" in path.parts or path.parts[0] == "build":
        return True
    return False


def prose_vault_to_auxmem(text: str) -> str:
    """Replace standalone vault terminology."""
    lines = []
    for line in text.splitlines(keepends=True):
        if PRESERVE_LINE.search(line):
            lines.append(line)
            continue
        # common phrases
        line = re.sub(r"\ban auxmem vault\b", "an auxmem", line, flags=re.I)
        line = re.sub(r"\bthe vault's\b", "the auxmem's", line, flags=re.I)
        line = re.sub(r"\bthe vault\b", "the auxmem", line, flags=re.I)
        line = re.sub(r"\ba vault\b", "an auxmem", line, flags=re.I)
        line = re.sub(r"\bVault validation\b", "Auxmem validation", line)
        line = re.sub(r"\bvault validation\b", "auxmem validation", line, flags=re.I)
        line = re.sub(r"\bvault root\b", "auxmem root", line, flags=re.I)
        line = re.sub(r"\bvault folder\b", "auxmem folder", line, flags=re.I)
        line = re.sub(r"\bvault template\b", "auxmem template", line, flags=re.I)
        line = re.sub(r"\bauxmem vault\b", "auxmem", line, flags=re.I)
        line = re.sub(r"\bcreate a vault\b", "create an auxmem", line, flags=re.I)
        line = re.sub(r"\bnew vault\b", "new auxmem", line, flags=re.I)
        line = re.sub(r"\bexisting vault\b", "existing auxmem", line, flags=re.I)
        line = re.sub(r"\btarget vault\b", "target auxmem", line, flags=re.I)
        line = re.sub(r"\binto the vault\b", "into the auxmem", line, flags=re.I)
        line = re.sub(r"\binto your vault\b", "into your auxmem", line, flags=re.I)
        line = re.sub(r"\bfrom the vault\b", "from the auxmem", line, flags=re.I)
        line = re.sub(r"\bin the vault\b", "in the auxmem", line, flags=re.I)
        line = re.sub(r"\binto a vault\b", "into an auxmem", line, flags=re.I)
        line = re.sub(r"\bfrom a vault\b", "from an auxmem", line, flags=re.I)
        line = re.sub(r"\bfor a vault\b", "for an auxmem", line, flags=re.I)
        line = re.sub(r"\bfor the vault\b", "for the auxmem", line, flags=re.I)
        line = re.sub(r"\bEach vault\b", "Each auxmem", line)
        line = re.sub(r"\bevery vault\b", "every auxmem", line, flags=re.I)
        line = re.sub(r"\bYour vault\b", "Your auxmem", line)
        line = re.sub(r"\byour vault\b", "your auxmem", line, flags=re.I)
        line = re.sub(r"\bthis vault\b", "this auxmem", line, flags=re.I)
        line = re.sub(r"\bthe auxmem tool\b", "the `auxmem` CLI", line, flags=re.I)
        line = re.sub(r" @vault\b", " @auxmem", line)
        lines.append(line)
    return "".join(lines)


def process_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, IsADirectoryError):
        return False
    orig = text
    for old, new in MECHANICAL:
        text = text.replace(old, new)
    if path.suffix in (".md", ".py", ".sh", ".json", ".toml", ".txt", ".systemd") or path.name == "pre-commit":
        if path.name != "CHANGELOG.md":
            text = prose_vault_to_auxmem(text)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or should_skip(path):
            continue
        if process_file(path):
            changed.append(path.relative_to(ROOT))
    print(f"updated {len(changed)} file(s)")
    for p in changed:
        print(f"  {p}")


if __name__ == "__main__":
    main()
