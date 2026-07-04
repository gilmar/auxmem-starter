"""Importer wrappers: run one-time seeding and migration against a target vault.

These operations live in the starter, not in each vault. Each wrapper shells
out to the relevant script in ../importers/, then runs the TARGET vault's own
validator and MOC generator so the result is checked against that vault's config.
"""

import subprocess
from pathlib import Path

STARTER_ROOT = Path(__file__).resolve().parent.parent
IMPORTERS = STARTER_ROOT / "importers"


class ImportError_(Exception):
    pass


def _vault(dest):
    dest = Path(dest).expanduser().resolve()
    if not (dest / ".scripts" / "vault.config.json").exists():
        raise ImportError_(f"{dest} is not an auxmem vault (no .scripts/vault.config.json)")
    return dest


def _run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def validate_and_moc(dest):
    """Run the target vault's own MOC generator and validator."""
    dest = _vault(dest)
    _run(["python3", ".scripts/gen_mocs.py"], cwd=dest)
    return _run(["python3", ".scripts/validate_vault.py", "--all"], cwd=dest)


def extract_export(export_file, staging, provider=None, since=None, min_messages=None):
    """Stage 1 of seeding: normalize a provider export into a staging corpus.
    Staging lives OUTSIDE any vault. Distillation into notes is an agent step
    (see importers/distill-seeds.md)."""
    cmd = ["python3", str(IMPORTERS / "seed_extract.py"), str(export_file), "--out", str(staging)]
    if provider:
        cmd += ["--provider", provider]
    if since:
        cmd += ["--since", since]
    if min_messages is not None:
        cmd += ["--min-messages", str(min_messages)]
    return _run(cmd)


def migrate_obsidian_single(src, dest, map_file=None, dry_run=False):
    """Single-script Obsidian import (no toolchain). Writes into the vault."""
    dest = _vault(dest)
    cfg = dest / ".scripts" / "vault.config.json"
    cmd = ["python3", str(IMPORTERS / "migrate_vault.py"), "--src", str(src), "--dst", str(dest),
           "--vault-config", str(cfg)]
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
    dest = _vault(dest)
    rc, out, err = _run(["bash", str(IMPORTERS / "export_vault.sh"), str(src), str(export_tmp)])
    if rc != 0:
        return rc, out, err
    cmd = ["python3", str(IMPORTERS / "restructure_export.py"),
           "--src", str(export_tmp), "--dst", str(dest),
           "--vault-config", str(dest / ".scripts" / "vault.config.json")]
    if map_file:
        cmd += ["--map", str(map_file)]
    if dry_run:
        cmd += ["--dry-run"]
    rc2, out2, err2 = _run(cmd)
    if rc2 == 0 and not dry_run:
        validate_and_moc(dest)
    return rc2, out + out2, err + err2
