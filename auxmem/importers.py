"""Importer wrappers: run one-time seeding and migration against a target auxmem.

These operations live in the AuxMem package, not inside an auxmem folder. Each
wrapper shells out to auxmem/importers/, then runs the target auxmem's own
validator and MOC generator.
"""

import subprocess
import sys
from pathlib import Path

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .paths import AuxmemPathError, config_path, resolve_auxmem

_PKG_ROOT = Path(__file__).resolve().parent
IMPORTERS = _PKG_ROOT / "importers"
_PYTHON = sys.executable


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


def _format_phase_failure(phase: str, out: str, err: str) -> str:
    detail = (out or err or "").strip()
    if detail:
        return f"{phase} failed:\n{detail}"
    return f"{phase} failed (non-zero exit; no output captured)"


def validate_and_moc(dest):
    """Run the target auxmem's MOC generator then validator.

    Returns (exit_code, stdout_message). exit_code is OK, OPERATION_FAILED, or
    NON_CONFORMANT.
    """
    dest = _dest(dest)
    moc_rc, moc_out, moc_err = _run([_PYTHON, ".scripts/gen_mocs.py"], cwd=dest)
    if moc_rc != 0:
        return OPERATION_FAILED, _format_phase_failure("MOC generation", moc_out, moc_err)

    val_rc, val_out, val_err = _run(
        [_PYTHON, ".scripts/validate_auxmem.py", "--all"], cwd=dest
    )
    if val_rc != 0:
        return NON_CONFORMANT, _format_phase_failure("Validation", val_out, val_err)

    return OK, (val_out or val_err or "auxmem validation clean.").strip()


def extract_export(export_file, staging, provider=None, since=None, min_messages=None):
    """Stage 1 of seeding: normalize a provider export into a staging corpus."""
    if not IMPORTERS.is_dir():
        raise ImportError_(
            f"importers not found at {IMPORTERS}. "
            "The installed package is missing importer scripts; reinstall AuxMem."
        )
    cmd = [_PYTHON, str(IMPORTERS / "seed_extract.py"), str(export_file), "--out", str(staging)]
    if provider:
        cmd += ["--provider", provider]
    if since:
        cmd += ["--since", since]
    if min_messages is not None:
        cmd += ["--min-messages", str(min_messages)]
    return _run(cmd)


def _finalize_import(rc, out, err, dest, *, dry_run):
    if rc != 0:
        return rc, out, err
    if dry_run:
        return OK, out, err
    exit_code, message = validate_and_moc(dest)
    if exit_code != OK:
        combined = "\n".join(p for p in (out, message) if p).strip()
        return exit_code, combined, err
    return OK, out, err


def migrate_obsidian_single(src, dest, map_file=None, dry_run=False):
    """Single-script Obsidian import (no toolchain). Writes into the auxmem."""
    dest = _dest(dest)
    cfg = config_path(dest)
    cmd = [
        _PYTHON, str(IMPORTERS / "migrate_obsidian.py"),
        "--src", str(src), "--dst", str(dest),
        "--auxmem-config", str(cfg),
    ]
    if map_file:
        cmd += ["--map", str(map_file)]
    if dry_run:
        cmd += ["--dry-run"]
    rc, out, err = _run(cmd)
    return _finalize_import(rc, out, err, dest, dry_run=dry_run)


def migrate_obsidian_pipeline(src, dest, export_tmp, map_file=None, dry_run=False):
    """Two-stage Obsidian import via obsidian-export. Preferred when available."""
    dest = _dest(dest)
    rc, out, err = _run(["bash", str(IMPORTERS / "export_obsidian.sh"), str(src), str(export_tmp)])
    if rc != 0:
        return rc, out, err
    cmd = [
        _PYTHON, str(IMPORTERS / "restructure_export.py"),
        "--src", str(export_tmp), "--dst", str(dest),
        "--auxmem-config", str(config_path(dest)),
    ]
    if map_file:
        cmd += ["--map", str(map_file)]
    if dry_run:
        cmd += ["--dry-run"]
    rc2, out2, err2 = _run(cmd)
    return _finalize_import(rc2, out + out2, err + err2, dest, dry_run=dry_run)
