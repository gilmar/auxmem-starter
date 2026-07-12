"""Upgrade an existing corpus to the current template version.

Per-file policy:
  overwrite  tooling replaced with the new version (old backed up; user edits
             detected via the snapshot and flagged)
  merge      koinome.config.json: preserve user values, add new schema keys/options
  merge3     guidance/docs/templates: git 3-way merge (base = corpus snapshot,
             ours = current file, theirs = new template); clean merges applied,
             conflicts left with markers and flagged

User content (anything not in the manifest) is never touched. Managed files are
journaled before modification; failed post-upgrade checks roll back managed state.
Every replaced or merged file is also backed up under .koinome/backups/<timestamp>/.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .manifest import verify_bundled_template
from .paths import config_path, managed_path, resolve_corpus
from .version import TEMPLATE_VERSION

_PKG_ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = _PKG_ROOT / "template"
MANIFEST_SRC = TEMPLATE_DIR / ".koinome-manifest.json"
_PYTHON = sys.executable

FileJournal = dict[str, bytes | None]


class UpgradeError(Exception):
    pass


@dataclass
class PostCheckResult:
    moc_rc: int
    moc_detail: str
    val_rc: int
    val_detail: str

    @property
    def moc_failed(self) -> bool:
        return self.moc_rc != 0

    @property
    def validation_failed(self) -> bool:
        return self.val_rc != 0

    @property
    def should_rollback(self) -> bool:
        return self.moc_failed or self.validation_failed


@dataclass
class UpgradePlan:
    status: str
    old_version: str
    new_version: str
    changes: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    touched_files: list[str] = field(default_factory=list)
    created_folders: list[str] = field(default_factory=list)
    deprecated: list[str] = field(default_factory=list)
    post_check: PostCheckResult | None = None

    def to_result(self, *, backup: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        post_exit_code = OK
        post_phase = None
        post_detail = ""
        if self.post_check:
            if self.post_check.moc_failed:
                post_exit_code = OPERATION_FAILED
                post_phase = "MOC generation"
                post_detail = self.post_check.moc_detail
            elif self.post_check.validation_failed:
                post_exit_code = NON_CONFORMANT
                post_phase = "validation"
                post_detail = self.post_check.val_detail
        if self.conflicts and post_exit_code == OK:
            post_exit_code = NON_CONFORMANT
            post_phase = post_phase or "merge conflicts"
            post_detail = post_detail or f"{len(self.conflicts)} file(s) need manual review"

        out: dict[str, Any] = {
            "status": "dry-run" if dry_run else self.status,
            "from": self.old_version,
            "to": self.new_version,
            "changes": self.changes,
            "conflicts": self.conflicts,
            "deprecated": self.deprecated,
            "created_folders": self.created_folders,
            "post_exit_code": post_exit_code,
            "post_phase": post_phase,
            "post_detail": post_detail,
        }
        if backup:
            out["backup"] = backup
        if dry_run and self.post_check:
            out["post_validation_expected"] = not self.post_check.should_rollback
        return out


def _git_merge3(ours: Path, base: Path, theirs: Path) -> tuple[str, int]:
    proc = subprocess.run(
        ["git", "merge-file", "-p", "--", str(ours), str(base), str(theirs)],
        capture_output=True,
        text=True,
    )
    if proc.returncode < 0:
        raise UpgradeError(f"git merge-file failed: {proc.stderr}")
    return proc.stdout, proc.returncode


def _merge_config(current: dict, new: dict, report: list[str]) -> dict:
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


def _capture_journal(dest: Path, rels: list[str]) -> FileJournal:
    journal: FileJournal = {}
    for rel in rels:
        path = dest / rel
        journal[rel] = path.read_bytes() if path.is_file() else None
    return journal


def _restore_journal(dest: Path, journal: FileJournal) -> None:
    for rel, content in journal.items():
        path = dest / rel
        if content is None:
            if path.is_file():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def _chmod_managed(path: Path) -> None:
    if path.suffix in (".sh", ".py") or path.name == "pre-commit":
        path.chmod(0o755)


def _plan_merge3(
    cur_file: Path,
    snap_file: Path,
    new_file: Path,
    rel: str,
    report: list[str],
    conflicts: list[str],
) -> tuple[bytes | None, bool]:
    """Return (new_content, touch_file). None content means leave unchanged."""
    if not cur_file.exists():
        report.append(f"added: {rel}")
        return new_file.read_bytes(), True

    base = snap_file if snap_file.exists() else None
    cur_bytes = cur_file.read_bytes()
    new_bytes = new_file.read_bytes()
    if base and cur_bytes == base.read_bytes():
        if cur_bytes != new_bytes:
            report.append(f"updated: {rel} (unmodified by you)")
            return new_bytes, True
        return cur_bytes, False
    if base and base.read_bytes() == new_bytes:
        report.append(f"kept: {rel} (template unchanged; your edits preserved)")
        return cur_bytes, False
    if base is None:
        report.append(f"review: {rel} (no snapshot base; new version would be written as .new)")
        conflicts.append(rel)
        return None, False
    merged, n = _git_merge3(cur_file, base, new_file)
    if n == 0:
        report.append(f"merged: {rel} (your edits + template updates)")
    else:
        report.append(f"CONFLICT: {rel} ({n} conflict block(s); markers would be left in file)")
        conflicts.append(rel)
    return merged.encode("utf-8"), True


def _apply_overwrite(
    dest: Path,
    rel: str,
    new_file: Path,
    snap_file: Path,
    *,
    backup,
    report: list[str],
) -> None:
    cur_file = dest / rel
    if cur_file.exists():
        edited = snap_file.exists() and cur_file.read_bytes() != snap_file.read_bytes()
        backup(rel)
        if edited:
            report.append(f"overwrite: {rel} (YOUR EDITS were backed up and replaced)")
        else:
            report.append(f"overwrite: {rel}")
    else:
        report.append(f"added: {rel}")
    cur_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(new_file, cur_file)
    _chmod_managed(cur_file)


def _apply_merge3_no_snapshot_sidecar(
    dest: Path,
    rel: str,
    new_file: Path,
    report: list[str],
    conflicts: list[str],
    *,
    backup,
) -> None:
    cur_file = dest / rel
    backup(rel)
    sidecar = cur_file.with_suffix(cur_file.suffix + ".new")
    shutil.copy2(new_file, sidecar)
    report.append(f"review: {rel} (no snapshot base; new version at {sidecar.name})")
    conflicts.append(rel)


def build_plan(dest: Path, *, force: bool = False) -> UpgradePlan:
    aux = dest / ".koinome"
    old_manifest_path = aux / "manifest.json"
    has_state = old_manifest_path.exists()

    new_manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    new_version = new_manifest["template_version"]

    if has_state:
        old_manifest = json.loads(old_manifest_path.read_text(encoding="utf-8"))
        old_version = old_manifest.get("template_version", "unknown")
    else:
        old_manifest = {"files": {}}
        old_version = "pre-versioning"

    if old_version == new_version and not force:
        return UpgradePlan("up-to-date", old_version, new_version)

    report: list[str] = []
    conflicts: list[str] = []
    touched: list[str] = []
    snapshot = aux / "snapshot"

    for rel, meta in new_manifest["files"].items():
        policy = meta["policy"]
        new_file = TEMPLATE_DIR / rel
        cur_file = managed_path(dest, rel)
        snap_file = snapshot / rel

        if policy == "overwrite":
            touched.append(rel)
            if cur_file.exists():
                edited = snap_file.exists() and cur_file.read_bytes() != snap_file.read_bytes()
                if edited:
                    report.append(f"overwrite: {rel} (YOUR EDITS were backed up and replaced)")
                else:
                    report.append(f"overwrite: {rel}")
            else:
                report.append(f"added: {rel}")

        elif policy == "merge":
            touched.append(rel)
            current = json.loads(cur_file.read_text(encoding="utf-8"))
            new_cfg = json.loads(new_file.read_text(encoding="utf-8"))
            _merge_config(current, new_cfg, report)

        elif policy == "merge3":
            content, touch = _plan_merge3(cur_file, snap_file, new_file, rel, report, conflicts)
            if touch and content is not None:
                touched.append(rel)

    deprecated = [
        rel for rel in old_manifest.get("files", {}) if rel not in new_manifest["files"]
    ]
    for rel in deprecated:
        report.append(f"deprecated: {rel} (no longer in template; left in place)")

    merged_cfg = json.loads(config_path(dest).read_text(encoding="utf-8"))
    new_folders = list(merged_cfg.get("domains", {})) + merged_cfg.get("structural_folders", [])
    created_folders = [f for f in new_folders if not (dest / f).exists()]
    for f in created_folders:
        report.append(f"created folder: {f}")

    return UpgradePlan(
        status="planned",
        old_version=old_version,
        new_version=new_version,
        changes=report,
        conflicts=conflicts,
        touched_files=touched,
        created_folders=created_folders,
        deprecated=deprecated,
    )


def _apply_plan(dest: Path, plan: UpgradePlan, *, backup_dir: Path) -> None:
    new_manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    aux = dest / ".koinome"
    snapshot = aux / "snapshot"
    scratch_report: list[str] = []
    scratch_conflicts: list[str] = []

    def backup(rel: str) -> None:
        src = dest / rel
        if src.exists():
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    for rel, meta in new_manifest["files"].items():
        policy = meta["policy"]
        new_file = TEMPLATE_DIR / rel
        cur_file = managed_path(dest, rel)
        snap_file = snapshot / rel

        if policy == "overwrite":
            _apply_overwrite(
                dest, rel, new_file, snap_file, backup=backup, report=scratch_report
            )

        elif policy == "merge":
            backup(rel)
            current = json.loads(cur_file.read_text(encoding="utf-8"))
            new_cfg = json.loads(new_file.read_text(encoding="utf-8"))
            merged = _merge_config(current, new_cfg, scratch_report)
            cur_file.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

        elif policy == "merge3":
            if not cur_file.exists():
                cur_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(new_file, cur_file)
                continue
            base = snap_file if snap_file.exists() else None
            cur_bytes = cur_file.read_bytes()
            new_bytes = new_file.read_bytes()
            if base and cur_bytes == base.read_bytes():
                if cur_bytes != new_bytes:
                    backup(rel)
                    shutil.copy2(new_file, cur_file)
                continue
            if base and base.read_bytes() == new_bytes:
                continue
            if base is None:
                _apply_merge3_no_snapshot_sidecar(
                    dest, rel, new_file, scratch_report, scratch_conflicts, backup=backup
                )
                if rel not in plan.conflicts:
                    plan.conflicts.append(rel)
                continue
            backup(rel)
            merged, n = _git_merge3(cur_file, base, new_file)
            cur_file.write_text(merged, encoding="utf-8")
            if n != 0 and rel not in plan.conflicts:
                plan.conflicts.append(rel)

    for folder in plan.created_folders:
        fp = dest / folder
        fp.mkdir(parents=True, exist_ok=True)
        (fp / ".gitkeep").touch()


def _run_post_checks(dest: Path) -> PostCheckResult:
    moc = subprocess.run(
        [_PYTHON, ".scripts/gen_mocs.py"], cwd=dest, capture_output=True, text=True
    )
    moc_detail = (moc.stdout or moc.stderr or "").strip() or "no output captured"
    if moc.returncode != 0:
        return PostCheckResult(moc.returncode, moc_detail, 1, "")

    val = subprocess.run(
        [_PYTHON, ".scripts/validate_corpus.py", "--all"],
        cwd=dest,
        capture_output=True,
        text=True,
    )
    val_detail = (val.stdout or val.stderr or "").strip()
    return PostCheckResult(0, moc_detail, val.returncode, val_detail)


def _finalize_state(dest: Path, ts: str) -> None:
    aux = dest / ".koinome"
    snapshot = aux / "snapshot"
    new_manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))

    if snapshot.exists():
        shutil.rmtree(snapshot)
    snapshot.mkdir(parents=True, exist_ok=True)
    for rel in new_manifest["files"]:
        s = snapshot / rel
        s.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATE_DIR / rel, s)
    shutil.copy2(MANIFEST_SRC, aux / "manifest.json")


def _write_failure_log(dest: Path, ts: str, detail: str) -> Path:
    log_dir = dest / ".koinome" / "upgrade-failures"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{ts}.log"
    path.write_text(detail.rstrip() + "\n", encoding="utf-8")
    return path


def _predict_post_check(dest: Path, plan: UpgradePlan) -> PostCheckResult:
    with tempfile.TemporaryDirectory(prefix="koinome-upgrade-") as td:
        workspace = Path(td) / "workspace"
        shutil.copytree(dest, workspace, symlinks=True)
        backup_dir = workspace / ".koinome" / "backups" / "dry-run"
        backup_dir.mkdir(parents=True, exist_ok=True)
        _apply_plan(workspace, plan, backup_dir=backup_dir)
        return _run_post_checks(workspace)


def upgrade(dest, force=False, dry_run=False):
    try:
        verify_bundled_template(TEMPLATE_DIR, MANIFEST_SRC)
    except ValueError as exc:
        raise UpgradeError(str(exc)) from exc

    if not TEMPLATE_DIR.is_dir():
        raise UpgradeError(
            f"Koinome template not found at {TEMPLATE_DIR}. "
            "The installed package is missing template data; reinstall Koinome."
        )
    try:
        dest = resolve_corpus(dest)
    except Exception as e:
        raise UpgradeError(str(e)) from e

    plan = build_plan(dest, force=force)
    if plan.status == "up-to-date":
        return {"status": "up-to-date", "version": plan.new_version, "changes": []}

    if dry_run:
        plan.post_check = _predict_post_check(dest, plan)
        return plan.to_result(dry_run=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_dir = dest / ".koinome" / "backups" / ts
    journal = _capture_journal(dest, list(json.loads(MANIFEST_SRC.read_text())["files"]))

    try:
        _apply_plan(dest, plan, backup_dir=backup_dir)
        plan.post_check = _run_post_checks(dest)
        if plan.post_check.should_rollback:
            _restore_journal(dest, journal)
            detail = (
                f"upgrade rolled back at {ts}\n"
                f"MOC rc={plan.post_check.moc_rc}: {plan.post_check.moc_detail}\n"
                f"validation rc={plan.post_check.val_rc}: {plan.post_check.val_detail}\n"
            )
            _write_failure_log(dest, ts, detail)
            plan.status = "failed"
            return plan.to_result(backup=str(backup_dir))

        _finalize_state(dest, ts)
        _write_report(
            dest,
            plan.old_version,
            plan.new_version,
            plan.changes,
            plan.conflicts,
            ts,
        )
        plan.status = "upgraded"
        return plan.to_result(backup=str(backup_dir))
    except Exception:
        _restore_journal(dest, journal)
        raise


def _write_report(dest, old_v, new_v, report, conflicts, ts):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "---",
        f"title: Template upgrade {old_v} to {new_v}",
        f"summary: Koinome template upgrade from {old_v} to {new_v}. "
        f"{len(report)} change(s), {len(conflicts)} needing review. "
        f"Backups under .koinome/backups/{ts}.",
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
    lines += ["", f"Backups: .koinome/backups/{ts}/ (git-ignored, local only)."]
    if _is_major_rebrand(old_v, new_v):
        lines += [
            "",
            "## After this upgrade",
            "",
            "- Run `./bootstrap.sh` to refresh the git pre-commit hook.",
            "- If you use the sync timer, reinstall from `.scripts/koinome-sync.systemd` "
            "(unit `ExecStart` path changed from `vault-sync.sh` to `koinome-sync.sh`). "
            "Pass your corpus path explicitly.",
        ]
    out = dest / "00-inbox" / f"upgrade-report-{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _is_major_rebrand(old_v, new_v):
    if old_v in (new_v, "0.0.0"):
        return False
    if old_v in ("pre-versioning", "unknown"):
        return True
    try:
        return int(old_v.split(".")[0]) == 1
    except (ValueError, IndexError):
        return False


def _primary_domain(dest):
    cfg = json.loads(config_path(dest).read_text(encoding="utf-8"))
    domains = cfg.get("domains") or {}
    if not domains:
        return "general"
    return next(iter(domains.values()))
