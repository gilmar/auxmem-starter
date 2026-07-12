"""Importer wrappers: run one-time seeding and migration against a target auxmem.

These operations live in the AuxMem package, not inside an auxmem folder. Each
wrapper shells out to auxmem/importers/, then runs the target auxmem's own
validator and MOC generator.

Obsidian imports are atomic: candidates are built in an isolated directory,
validated on a workspace copy of the target auxmem, and applied only after
validation succeeds.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .import_atomic import apply_validated_candidate
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


def _load_importer_script(name: str):
    import importlib.util

    path = IMPORTERS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"auxmem_importer_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _atomic_obsidian_import(
    src,
    dest,
    *,
    map_file=None,
    dry_run=False,
    importer_name: str,
    extra_args: list[str] | None = None,
):
    dest = _dest(dest)
    cfg = config_path(dest)
    script = IMPORTERS / f"{importer_name}.py"
    importer_mod = _load_importer_script(importer_name)

    if dry_run:
        cmd = [
            _PYTHON, str(script),
            "--src", str(src), "--dst", str(dest),
            "--auxmem-config", str(cfg),
        ]
        if map_file:
            cmd += ["--map", str(map_file)]
        cmd.append("--dry-run")
        if extra_args:
            cmd += extra_args
        return _run(cmd)

    with tempfile.TemporaryDirectory(prefix="auxmem-import-") as td:
        candidate = Path(td) / "candidate"
        report_json = candidate / ".import-report.json"
        cmd = [
            _PYTHON, str(script),
            "--src", str(src), "--dst", str(candidate),
            "--auxmem-config", str(cfg),
            "--report-json", str(report_json),
        ]
        if map_file:
            cmd += ["--map", str(map_file)]
        if extra_args:
            cmd += extra_args
        rc, out, err = _run(cmd)
        if rc != 0:
            return rc, out, err
        report = json.loads(report_json.read_text(encoding="utf-8")) if report_json.is_file() else {}
        if report_json.is_file():
            report_json.unlink()

        apply_rc, apply_out, apply_err = apply_validated_candidate(
            dest,
            candidate,
            report_writer=importer_mod.write_report,
            report_payload=report,
        )
        combined = "\n".join(p for p in (out, apply_out) if p).strip()
        if apply_rc != OK:
            return apply_rc, combined, apply_err
        return OK, combined, apply_err


def migrate_obsidian_single(src, dest, map_file=None, dry_run=False):
    """Single-script Obsidian import (no toolchain). Writes into the auxmem."""
    return _atomic_obsidian_import(
        src, dest, map_file=map_file, dry_run=dry_run, importer_name="migrate_obsidian"
    )


def migrate_obsidian_pipeline(src, dest, export_tmp, map_file=None, dry_run=False):
    """Two-stage Obsidian import via obsidian-export. Preferred when available."""
    dest = _dest(dest)
    if dry_run:
        rc, out, err = _run(["bash", str(IMPORTERS / "export_obsidian.sh"), str(src), str(export_tmp)])
        if rc != 0:
            return rc, out, err
        cfg = config_path(dest)
        cmd = [
            _PYTHON, str(IMPORTERS / "restructure_export.py"),
            "--src", str(export_tmp), "--dst", str(dest),
            "--auxmem-config", str(cfg),
        ]
        if map_file:
            cmd += ["--map", str(map_file)]
        cmd.append("--dry-run")
        return _run(cmd)

    rc, out, err = _run(["bash", str(IMPORTERS / "export_obsidian.sh"), str(src), str(export_tmp)])
    if rc != 0:
        return rc, out, err
    return _atomic_obsidian_import(
        export_tmp,
        dest,
        map_file=map_file,
        dry_run=False,
        importer_name="restructure_export",
    )
