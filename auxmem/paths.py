"""Shared paths for auxmem folders (managed memory directories)."""

from pathlib import Path

CONFIG_NEW = Path(".scripts/auxmem.config.json")
CONFIG_LEGACY = Path(".scripts/auxmem.config.json")

# 1.x → 2.0 on-disk renames applied by `auxmem upgrade` before manifest work.
LEGACY_RENAMES = {
    ".scripts/auxmem.config.json": ".scripts/auxmem.config.json",
    ".scripts/validate_auxmem.py": ".scripts/validate_auxmem.py",
    ".scripts/auxmem-sync.sh": ".scripts/auxmem-sync.sh",
    ".scripts/auxmem-sync.systemd": ".scripts/auxmem-sync.systemd",
    "60-decisions/adr-0001-auxmem-structure.md": (
        "60-decisions/adr-0001-auxmem-structure.md"
    ),
}


class AuxmemPathError(Exception):
    pass


def resolve_auxmem(dest):
    """Return resolved path if dest looks like an auxmem (legacy or current config)."""
    dest = Path(dest).expanduser().resolve()
    if (dest / CONFIG_NEW).is_file() or (dest / CONFIG_LEGACY).is_file():
        return dest
    raise AuxmemPathError(
        f"{dest} is not an auxmem (no {CONFIG_NEW} or legacy {CONFIG_LEGACY})"
    )


def config_path(dest):
    """Path to the config file to use (prefers current name)."""
    dest = Path(dest)
    if (dest / CONFIG_NEW).is_file():
        return dest / CONFIG_NEW
    if (dest / CONFIG_LEGACY).is_file():
        return dest / CONFIG_LEGACY
    raise AuxmemPathError(f"no auxmem config under {dest}")


def remap_manifest_keys(manifest: dict) -> dict:
    """Map old managed-file paths to current names for upgrade comparisons."""
    files = {}
    for rel, meta in manifest.get("files", {}).items():
        files[LEGACY_RENAMES.get(rel, rel)] = meta
    out = dict(manifest)
    out["files"] = files
    return out


def migrate_legacy_layout(dest, report: list) -> bool:
    """Rename 1.x managed files to 2.0 names. Returns True if anything moved."""
    dest = Path(dest)
    if (dest / CONFIG_NEW).exists():
        return False
    if not (dest / CONFIG_LEGACY).exists():
        return False
    moved = False
    for old_rel, new_rel in LEGACY_RENAMES.items():
        old = dest / old_rel
        new = dest / new_rel
        if old.exists() and not new.exists():
            new.parent.mkdir(parents=True, exist_ok=True)
            old.rename(new)
            report.append(f"renamed: {old_rel} -> {new_rel}")
            moved = True
    snap = dest / ".auxmem" / "snapshot"
    if snap.is_dir():
        for old_rel, new_rel in LEGACY_RENAMES.items():
            old = snap / old_rel
            new = snap / new_rel
            if old.exists() and not new.exists():
                new.parent.mkdir(parents=True, exist_ok=True)
                old.rename(new)
    return moved
