"""Upgrade an existing auxmem to the current template version.

Per-file policy:
  overwrite  tooling replaced with the new version (old backed up; user edits
             detected via the snapshot and flagged)
  merge      auxmem.config.json: preserve user values, add new schema keys/options
  merge3     guidance/docs/templates: git 3-way merge (base = auxmem snapshot,
             ours = current file, theirs = new template); clean merges applied,
             conflicts left with markers and flagged

User content (anything not in the manifest) is never touched. Every replaced or
merged file is backed up under .auxmem/backups/<timestamp>/ first. An upgrade
report is written to 00-inbox/. After file work, MOCs are regenerated and the
validator is run.
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .paths import CONFIG_NEW, migrate_legacy_layout, remap_manifest_keys, resolve_auxmem
from .version import TEMPLATE_VERSION

_PKG_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = _PKG_ROOT / "template"
MANIFEST_SRC = TEMPLATE_DIR / ".auxmem-manifest.json"
_PYTHON = sys.executable


class UpgradeError(Exception):
    pass


def _git_merge3(ours: Path, base: Path, theirs: Path):
    """Return (merged_text, conflicts). conflicts is an int (0 = clean)."""
    proc = subprocess.run(
        ["git", "merge-file", "-p", "--", str(ours), str(base), str(theirs)],
        capture_output=True, text=True,
    )
    if proc.returncode < 0:
        raise UpgradeError(f"git merge-file failed: {proc.stderr}")
    return proc.stdout, proc.returncode


def _merge_config(current: dict, new: dict, report: list):
    """Preserve user-owned values; add new schema keys and list options."""
    user_owned = {"name", "created", "domains"}
    out = dict(current)
    out["template_version"] = TEMPLATE_VERSION
    for key, new_val in new.items():
        if key in user_owned or key == "template_version":
            continue
        if key not in out:
            out[key] = new_val
            report.append(f"config: added key '{key}'")
        elif isinstance(new_val, list) and isinstance(out.get(key), list):
            added = [x for x in new_val if x not in out[key]]
            if added:
                out[key] = out[key] + added
                report.append(f"config: added to '{key}': {', '.join(map(str, added))}")
        elif isinstance(new_val, dict) and isinstance(out.get(key), dict):
            for k2, v2 in new_val.items():
                if k2 not in out[key]:
                    out[key][k2] = v2
                    report.append(f"config: added '{key}.{k2}'")
                elif isinstance(v2, list) and isinstance(out[key].get(k2), list):
                    added2 = [x for x in v2 if x not in out[key][k2]]
                    if added2:
                        out[key][k2] = out[key][k2] + added2
                        report.append(
                            f"config: added to '{key}.{k2}': {', '.join(map(str, added2))}"
                        )
    return out


def upgrade(dest, force=False):
    if not TEMPLATE_DIR.is_dir():
        raise UpgradeError(
            f"auxmem template not found at {TEMPLATE_DIR}. "
            "The installed package is missing template data; reinstall AuxMem "
            "(python3 auxmem-cli new) or upgrade the package."
        )
    try:
        dest = resolve_auxmem(dest)
    except Exception as e:
        raise UpgradeError(str(e)) from e

    aux = dest / ".auxmem"
    old_manifest_path = aux / "manifest.json"
    has_state = old_manifest_path.exists()

    new_manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    new_version = new_manifest["template_version"]

    if has_state:
        old_manifest = remap_manifest_keys(
            json.loads(old_manifest_path.read_text(encoding="utf-8"))
        )
        old_version = old_manifest.get("template_version", "unknown")
    else:
        old_manifest = {"files": {}}
        old_version = "pre-versioning"

    if old_version == new_version and not force:
        return {"status": "up-to-date", "version": new_version, "changes": []}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = aux / "backups" / ts
    snapshot = aux / "snapshot"
    report = []
    conflicts = []

    migrate_legacy_layout(dest, report)

    def backup(rel):
        src = dest / rel
        if src.exists():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for rel, meta in new_manifest["files"].items():
        policy = meta["policy"]
        new_file = TEMPLATE_DIR / rel
        cur_file = dest / rel
        snap_file = snapshot / rel

        if policy == "overwrite":
            if cur_file.exists():
                edited = snap_file.exists() and (
                    cur_file.read_bytes() != snap_file.read_bytes()
                )
                backup(rel)
                if edited:
                    report.append(f"overwrite: {rel} (YOUR EDITS were backed up and replaced)")
                else:
                    report.append(f"overwrite: {rel}")
            else:
                report.append(f"added: {rel}")
            cur_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(new_file, cur_file)
            if cur_file.suffix in (".sh", ".py") or cur_file.name == "pre-commit":
                cur_file.chmod(0o755)

        elif policy == "merge":
            backup(rel)
            current = json.loads(cur_file.read_text(encoding="utf-8"))
            new_cfg = json.loads(new_file.read_text(encoding="utf-8"))
            merged = _merge_config(current, new_cfg, report)
            cur_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

        elif policy == "merge3":
            if not cur_file.exists():
                cur_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(new_file, cur_file)
                report.append(f"added: {rel}")
                continue
            base = snap_file if snap_file.exists() else None
            cur_bytes = cur_file.read_bytes()
            new_bytes = new_file.read_bytes()
            if base and cur_bytes == base.read_bytes():
                if cur_bytes != new_bytes:
                    backup(rel)
                    shutil.copy2(new_file, cur_file)
                    report.append(f"updated: {rel} (unmodified by you)")
                continue
            if base and base.read_bytes() == new_bytes:
                report.append(f"kept: {rel} (template unchanged; your edits preserved)")
                continue
            if base is None:
                backup(rel)
                sidecar = cur_file.with_suffix(cur_file.suffix + ".new")
                shutil.copy2(new_file, sidecar)
                report.append(f"review: {rel} (no snapshot base; new version at {sidecar.name})")
                conflicts.append(rel)
                continue
            backup(rel)
            merged, n = _git_merge3(cur_file, base, new_file)
            cur_file.write_text(merged, encoding="utf-8")
            if n == 0:
                report.append(f"merged: {rel} (your edits + template updates)")
            else:
                report.append(f"CONFLICT: {rel} ({n} conflict block(s); markers left in file)")
                conflicts.append(rel)

    for rel in old_manifest["files"]:
        if rel not in new_manifest["files"]:
            report.append(f"deprecated: {rel} (no longer in template; left in place)")

    merged_cfg = json.loads((dest / CONFIG_NEW).read_text(encoding="utf-8"))
    new_folders = list(merged_cfg.get("domains", {})) + merged_cfg.get("structural_folders", [])
    created_folders = []
    for f in new_folders:
        fp = dest / f
        if not fp.exists():
            fp.mkdir(parents=True, exist_ok=True)
            (fp / ".gitkeep").touch()
            created_folders.append(f)
    for f in created_folders:
        report.append(f"created folder: {f}")

    if snapshot.exists():
        shutil.rmtree(snapshot)
    snapshot.mkdir(parents=True, exist_ok=True)
    for rel in new_manifest["files"]:
        s = snapshot / rel
        s.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATE_DIR / rel, s)
    shutil.copy2(MANIFEST_SRC, old_manifest_path)

    _write_report(dest, old_version, new_version, report, conflicts, ts)

    moc = subprocess.run(
        [_PYTHON, ".scripts/gen_mocs.py"], cwd=dest, capture_output=True, text=True
    )
    if moc.returncode != 0:
        detail = (moc.stdout or moc.stderr or "").strip() or "no output captured"
        return {
            "status": "upgraded",
            "from": old_version,
            "to": new_version,
            "changes": report,
            "conflicts": conflicts,
            "backup": str(backup_dir),
            "post_exit_code": OPERATION_FAILED,
            "post_phase": "MOC generation",
            "post_detail": detail,
        }

    val = subprocess.run(
        [_PYTHON, ".scripts/validate_auxmem.py", "--all"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    post_exit_code = OK if val.returncode == 0 else NON_CONFORMANT

    return {
        "status": "upgraded",
        "from": old_version,
        "to": new_version,
        "changes": report,
        "conflicts": conflicts,
        "backup": str(backup_dir),
        "post_exit_code": post_exit_code,
        "post_phase": "validation" if post_exit_code != OK else None,
        "post_detail": (val.stdout or val.stderr or "").strip(),
    }


def _write_report(dest, old_v, new_v, report, conflicts, ts):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        f"title: Template upgrade {old_v} to {new_v}",
        f"summary: AuxMem template upgrade from {old_v} to {new_v}. "
        f"{len(report)} change(s), {len(conflicts)} needing review. "
        f"Backups under .auxmem/backups/{ts}.",
        "type: log",
        "status: active",
        f"domain: {_primary_domain(dest)}",
        f"created: {today}",
        f"updated: {today}",
        "---",
        "",
    ]
    if conflicts:
        lines += ["## Needs your review", ""]
        lines += [f"- {c}" for c in conflicts]
        lines += [
            "",
            "Files with CONFLICT contain git conflict markers (<<<<<<< ======= >>>>>>>). "
            "Resolve them, then commit. Files marked .new hold the new template version "
            "next to your unchanged one; merge by hand and delete the .new.",
            "",
        ]
    lines += ["## All changes", ""]
    lines += [f"- {r}" for r in report]
    lines += ["", f"Backups: .auxmem/backups/{ts}/ (git-ignored, local only)."]
    if _is_major_rebrand(old_v, new_v):
        lines += [
            "",
            "## After this upgrade",
            "",
            "- Run `./bootstrap.sh` to refresh the git pre-commit hook.",
            "- If you use the sync timer, reinstall from `.scripts/auxmem-sync.systemd` "
            "(unit `ExecStart` path changed from `vault-sync.sh` to `auxmem-sync.sh`). "
            "Pass your auxmem path explicitly if it is not `~/auxmem`.",
        ]
    out = dest / "00-inbox" / f"upgrade-report-{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_major_rebrand(old_v, new_v):
    """1.x vault layout → auxmem rename; show bootstrap/timer notes once."""
    if old_v in (new_v, "0.0.0"):
        return False
    if old_v in ("pre-versioning", "unknown"):
        return True
    try:
        return int(old_v.split(".")[0]) == 1
    except (ValueError, IndexError):
        return False


def _primary_domain(dest):
    cfg = json.loads((dest / CONFIG_NEW).read_text(encoding="utf-8"))
    domains = cfg.get("domains") or {}
    if not domains:
        return "general"
    return next(iter(domains.values()))
