"""Importer wrappers: run one-time seeding and migration against a target auxmem.

These operations live in the AuxMem package, not inside an auxmem folder. Each
wrapper shells out to auxmem/importers/, then runs the target auxmem's own
validator and MOC generator.
"""

import subprocess
from pathlib import Path

from .paths import AuxmemPathError, config_path, resolve_auxmem

_PKG_ROOT = Path(__file__).resolve().parent
IMPORTERS = _PKG_ROOT / "importers"


class ImportError_(Exception):
    pass


def _run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _dest(path):
    try:
        return resolve_auxmem(path)
    except AuxmemPathError as e:
        raise ImportError_(str(e)) from e


def validate_and_moc(dest):
    """Run the target auxmem's own MOC generator and validator."""
    dest = _dest(dest)
    _run(["python3", ".scripts/gen_mocs.py"], cwd=dest)
    return _run(["python3", ".scripts/validate_auxmem.py", "--all"], cwd=dest)


def extract_export(export_file, staging, provider=None, since=None, min_messages=None):
    """Stage 1 of seeding: normalize a provider export into a staging corpus."""
    if not IMPORTERS.is_dir():
        raise ImportError_(
            f"importers not found at {IMPORTERS}. "
            "The installed package is missing importer scripts; reinstall AuxMem."
        )
    cmd = ["python3", str(IMPORTERS / "seed_extract.py"), str(export_file), "--out", str(staging)]
    if provider:
        cmd += ["--provider", provider]
    if since:
        cmd += ["--since", since]
    if min_messages is not None:
        cmd += ["--min-messages", str(min_messages)]
    return _run(cmd)


def migrate_obsidian_single(src, dest, map_file=None, dry_run=False):
    """Single-script Obsidian import (no toolchain). Writes into the auxmem."""
    dest = _dest(dest)
    cfg = config_path(dest)
    cmd = [
        "python3", str(IMPORTERS / "migrate_obsidian.py"),
        "--src", str(src), "--dst", str(dest),
        "--auxmem-config", str(cfg),
    ]
    if map_file:
        cmd += ["--map", str(map_file)]
    if dry_run:
        cmd += ["--dry-run"]
    rc, out, err = _run(cmd)
    if rc == 0 and not dry_run:
        validate_and_moc(dest)
    return rc, out, err


def migrate_obsidian_pipeline(src, dest, export_tmp, map_file=None, dry_run=False):
    """Two-stage Obsidian import via obsidian-export. Preferred when available."""
    dest = _dest(dest)
    rc, out, err = _run(["bash", str(IMPORTERS / "export_obsidian.sh"), str(src), str(export_tmp)])
    if rc != 0:
        return rc, out, err
    cmd = [
        "python3", str(IMPORTERS / "restructure_export.py"),
        "--src", str(export_tmp), "--dst", str(dest),
        "--auxmem-config", str(config_path(dest)),
    ]
    if map_file:
        cmd += ["--map", str(map_file)]
    if dry_run:
        cmd += ["--dry-run"]
    rc2, out2, err2 = _run(cmd)
    if rc2 == 0 and not dry_run:
        validate_and_moc(dest)
    return rc2, out + out2, err + err2
