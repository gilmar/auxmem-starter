"""Importer wrappers: run one-time seeding against a target auxmem.

These operations live in the AuxMem package, not inside an auxmem folder. Each
wrapper shells out to auxmem/importers/, then runs the target auxmem's own
validator and MOC generator when needed.
"""

import subprocess
import sys
from pathlib import Path

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .paths import AuxmemPathError, resolve_auxmem

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


def check_conformance(dest, *, manifest=False, git=False):
    """Read-only conformance check: validation and MOC freshness only.

    Returns (exit_code, message). Never mutates the auxmem.
    """
    dest = _dest(dest)
    checker = dest / ".scripts" / "check_auxmem.py"
    if checker.is_file():
        cmd = [_PYTHON, str(checker)]
        if manifest:
            cmd.append("--manifest")
        if git:
            cmd.append("--git")
        rc, out, err = _run(cmd, cwd=dest)
        message = (out or err).strip() or "conformance check failed"
        if rc == 0:
            return OK, message
        return NON_CONFORMANT, message

    val_rc, val_out, val_err = _run(
        [_PYTHON, ".scripts/validate_auxmem.py", "--all"], cwd=dest
    )
    if val_rc != 0:
        return NON_CONFORMANT, _format_phase_failure("Validation", val_out, val_err)

    moc_rc, moc_out, moc_err = _run([_PYTHON, ".scripts/gen_mocs.py", "--check"], cwd=dest)
    if moc_rc != 0:
        return NON_CONFORMANT, _format_phase_failure("MOC freshness", moc_out, moc_err)

    return OK, (val_out or moc_out or "auxmem conformance check passed.").strip()


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
