"""Shared paths for Koinome corpora (governed knowledge directories)."""

from __future__ import annotations

import re
from pathlib import Path

CONFIG_NEW = Path(".scripts/koinome.config.json")
CONFIG_LEGACY_AUXMEM = Path(".scripts/auxmem.config.json")
STATE_DIR_NEW = Path(".koinome")
STATE_DIR_LEGACY = Path(".auxmem")
MANIFEST_ROOT_NEW = Path(".koinome-manifest.json")
MANIFEST_ROOT_LEGACY = Path(".auxmem-manifest.json")

SKILL_SUFFIXES = (
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
)

# AuxMem → Koinome on-disk renames applied by `koinome upgrade`.
AUXMEM_TO_KOINOME_RENAMES: dict[str, str] = {
    ".scripts/auxmem.config.json": ".scripts/koinome.config.json",
    ".scripts/validate_auxmem.py": ".scripts/validate_corpus.py",
    ".scripts/check_auxmem.py": ".scripts/check_corpus.py",
    ".scripts/auxmem_sync.py": ".scripts/koinome_sync.py",
    ".scripts/auxmem-sync.sh": ".scripts/koinome-sync.sh",
    ".scripts/auxmem-sync.systemd": ".scripts/koinome-sync.systemd",
    ".github/workflows/auxmem-check.yml": ".github/workflows/koinome-check.yml",
    "60-decisions/adr-0001-auxmem-structure.md": "60-decisions/adr-0001-corpus-structure.md",
}
for suffix in SKILL_SUFFIXES:
    AUXMEM_TO_KOINOME_RENAMES[f".skills/auxmem-{suffix}"] = f".skills/koinome-{suffix}"

LEGACY_REF_PATTERNS = [
    re.compile(r"\bauxmem\b", re.I),
    re.compile(r"\bAuxMem\b"),
    re.compile(r"\ban auxmem\b", re.I),
    re.compile(r"\bauxmems\b", re.I),
    re.compile(r"auxmem-init", re.I),
    re.compile(r"validate_auxmem\.py", re.I),
    re.compile(r"auxmem\.config\.json", re.I),
    re.compile(r"\.auxmem/", re.I),
]

USER_NOTE_GLOBS = ("*.md", "72-tasks/*.txt")


class CorpusPathError(Exception):
    pass


def resolve_corpus(dest):
    """Return resolved path if dest looks like a corpus (Koinome or legacy AuxMem)."""
    dest = Path(dest).expanduser().resolve()
    if (dest / CONFIG_NEW).is_file() or (dest / CONFIG_LEGACY_AUXMEM).is_file():
        return dest
    raise CorpusPathError(
        f"{dest} is not a corpus (no {CONFIG_NEW} or legacy {CONFIG_LEGACY_AUXMEM})"
    )


def managed_path(dest: Path, rel: str) -> Path:
    """Resolve a managed file path, including legacy AuxMem names on disk."""
    dest = Path(dest)
    current = dest / rel
    if current.exists():
        return current
    for old_rel, new_rel in AUXMEM_TO_KOINOME_RENAMES.items():
        if new_rel == rel and (dest / old_rel).exists():
            return dest / old_rel
    return current


def config_path(dest):
    """Path to the active config file (prefers Koinome name)."""
    dest = Path(dest)
    if (dest / CONFIG_NEW).is_file():
        return dest / CONFIG_NEW
    if (dest / CONFIG_LEGACY_AUXMEM).is_file():
        return dest / CONFIG_LEGACY_AUXMEM
    raise CorpusPathError(f"no corpus config under {dest}")


def is_legacy_auxmem(dest: Path) -> bool:
    dest = Path(dest)
    if (dest / CONFIG_NEW).is_file() and (dest / STATE_DIR_NEW).is_dir():
        return False
    return any(
        (
            (dest / STATE_DIR_LEGACY).is_dir(),
            (dest / CONFIG_LEGACY_AUXMEM).is_file(),
            (dest / MANIFEST_ROOT_LEGACY).is_file(),
            any(
                (dest / f".scripts/{name}").exists()
                for name in (
                    "validate_auxmem.py",
                    "check_auxmem.py",
                    "auxmem_sync.py",
                    "auxmem-sync.sh",
                )
            ),
            any((dest / f".skills/auxmem-{s}").is_dir() for s in SKILL_SUFFIXES),
            (dest / "60-decisions/adr-0001-auxmem-structure.md").is_file(),
        )
    )


def detect_legacy_auxmem(dest: Path) -> list[str]:
    """Return inspectable legacy AuxMem artifacts under dest."""
    dest = Path(dest)
    found: list[str] = []
    if (dest / STATE_DIR_LEGACY).is_dir():
        found.append(str(STATE_DIR_LEGACY))
    if (dest / MANIFEST_ROOT_LEGACY).is_file():
        found.append(str(MANIFEST_ROOT_LEGACY))
    for old_rel in AUXMEM_TO_KOINOME_RENAMES:
        if (dest / old_rel).exists():
            found.append(old_rel)
    manifest = dest / STATE_DIR_LEGACY / "manifest.json"
    if manifest.is_file():
        text = manifest.read_text(encoding="utf-8")
        if "auxmem" in text.lower():
            found.append(f"{STATE_DIR_LEGACY}/manifest.json (contains AuxMem paths)")
    return sorted(set(found))


def remap_manifest_keys(manifest: dict) -> dict:
    """Map old managed-file paths to current names for upgrade comparisons."""
    files = {}
    for rel, meta in manifest.get("files", {}).items():
        files[AUXMEM_TO_KOINOME_RENAMES.get(rel, rel)] = meta
    out = dict(manifest)
    out["files"] = files
    return out


def _rename_path(old: Path, new: Path, report: list[str], label: str) -> bool:
    if not old.exists() or new.exists():
        return False
    new.parent.mkdir(parents=True, exist_ok=True)
    old.rename(new)
    report.append(f"renamed: {label}")
    return True


def _remap_manifest_content(manifest_path: Path, report: list[str]) -> None:
    if not manifest_path.is_file():
        return
    text = manifest_path.read_text(encoding="utf-8")
    updated = text
    for old, new in AUXMEM_TO_KOINOME_RENAMES.items():
        updated = updated.replace(old, new)
    updated = updated.replace(".auxmem/", ".koinome/")
    updated = updated.replace(".auxmem-manifest.json", ".koinome-manifest.json")
    if updated != text:
        manifest_path.write_text(updated, encoding="utf-8")
        report.append(f"remapped paths: {manifest_path.relative_to(manifest_path.parent.parent)}")


def scan_user_notes_for_legacy_refs(dest: Path) -> list[dict[str, str]]:
    """Report legacy AuxMem references in user-authored notes (not managed tooling)."""
    dest = Path(dest)
    managed_prefixes = (
        ".scripts/",
        ".skills/",
        ".koinome/",
        ".auxmem/",
        ".github/",
        "docs/",
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "README.md",
        "bootstrap.sh",
    )
    findings: list[dict[str, str]] = []
    candidates: list[Path] = list(dest.rglob("*.md"))
    tasks = dest / "72-tasks"
    if tasks.is_dir():
        candidates.extend(tasks.glob("*.txt"))
    for path in candidates:
            rel = str(path.relative_to(dest)).replace("\\", "/")
            if rel.startswith(managed_prefixes) or rel in managed_prefixes:
                continue
            if rel.startswith("90-templates/"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for rx in LEGACY_REF_PATTERNS:
                if rx.search(text):
                    findings.append({"path": rel, "pattern": rx.pattern})
                    break
    return findings


def plan_legacy_migration(dest: Path) -> list[str]:
    """Return planned AuxMem → Koinome renames without modifying dest."""
    dest = Path(dest)
    if not is_legacy_auxmem(dest):
        return []
    planned: list[str] = []
    if (dest / STATE_DIR_LEGACY).is_dir() and not (dest / STATE_DIR_NEW).exists():
        planned.append(f"renamed: {STATE_DIR_LEGACY} -> {STATE_DIR_NEW}")
    if (dest / MANIFEST_ROOT_LEGACY).is_file() and not (dest / MANIFEST_ROOT_NEW).exists():
        planned.append(f"renamed: {MANIFEST_ROOT_LEGACY} -> {MANIFEST_ROOT_NEW}")
    for old_rel, new_rel in AUXMEM_TO_KOINOME_RENAMES.items():
        if (dest / old_rel).exists() and not (dest / new_rel).exists():
            planned.append(f"renamed: {old_rel} -> {new_rel}")
    snap = dest / STATE_DIR_LEGACY / "snapshot"
    if not snap.is_dir():
        snap = dest / STATE_DIR_NEW / "snapshot"
    if snap.is_dir():
        for old_rel, new_rel in AUXMEM_TO_KOINOME_RENAMES.items():
            if (snap / old_rel).exists() and not (snap / new_rel).exists():
                planned.append(f"renamed: snapshot/{old_rel} -> snapshot/{new_rel}")
    return planned


def migrate_legacy_layout(dest, report: list) -> bool:
    """Migrate legacy AuxMem managed state to Koinome names. Returns True if anything moved."""
    dest = Path(dest)
    if not is_legacy_auxmem(dest):
        return False

    moved = False

    if (dest / STATE_DIR_LEGACY).is_dir() and not (dest / STATE_DIR_NEW).exists():
        (dest / STATE_DIR_LEGACY).rename(dest / STATE_DIR_NEW)
        report.append(f"renamed: {STATE_DIR_LEGACY} -> {STATE_DIR_NEW}")
        moved = True

    if (dest / MANIFEST_ROOT_LEGACY).is_file() and not (dest / MANIFEST_ROOT_NEW).exists():
        (dest / MANIFEST_ROOT_LEGACY).rename(dest / MANIFEST_ROOT_NEW)
        report.append(f"renamed: {MANIFEST_ROOT_LEGACY} -> {MANIFEST_ROOT_NEW}")
        moved = True

    for old_rel, new_rel in AUXMEM_TO_KOINOME_RENAMES.items():
        old = dest / old_rel
        new = dest / new_rel
        if _rename_path(old, new, report, f"{old_rel} -> {new_rel}"):
            moved = True

    state_dir = dest / STATE_DIR_NEW
    snap = state_dir / "snapshot"
    if snap.is_dir():
        for old_rel, new_rel in AUXMEM_TO_KOINOME_RENAMES.items():
            old = snap / old_rel
            new = snap / new_rel
            if _rename_path(old, new, report, f"snapshot/{old_rel} -> snapshot/{new_rel}"):
                moved = True

    for provider in (".cursor", ".codex", ".claude", ".gemini"):
        prov = dest / provider / "skills"
        if not prov.is_dir():
            continue
        for suffix in SKILL_SUFFIXES:
            old = prov / f"auxmem-{suffix}"
            new = prov / f"koinome-{suffix}"
            if _rename_path(old, new, report, f"{provider}/skills/auxmem-{suffix} -> koinome-{suffix}"):
                moved = True

    manifest = state_dir / "manifest.json"
    _remap_manifest_content(manifest, report)
    root_manifest = dest / MANIFEST_ROOT_NEW
    if not root_manifest.is_file() and (dest / MANIFEST_ROOT_LEGACY).is_file():
        root_manifest = dest / MANIFEST_ROOT_LEGACY
    _remap_manifest_content(root_manifest, report)

    return moved
