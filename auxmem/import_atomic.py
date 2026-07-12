"""Atomic import orchestration for Obsidian migrations."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .exit_codes import NON_CONFORMANT, OK, OPERATION_FAILED
from .paths import config_path

_PYTHON = sys.executable


@dataclass
class ImportCounts:
    imported: int = 0
    skipped: int = 0
    renamed: int = 0
    rejected: int = 0
    conflicted: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ImportReport:
    counts: ImportCounts = field(default_factory=ImportCounts)
    moves: list[tuple[str, str]] = field(default_factory=list)
    manual: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        out = {"counts": self.counts.to_dict(), "moves": self.moves, "manual": self.manual, "warnings": self.warnings}
        out.update(self.details)
        return out


def resolves_within_root(root: Path, rel: Path | str) -> bool:
    try:
        (root / rel).resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def overlay_tree(src: Path, dest: Path) -> list[str]:
    """Copy every file under src into dest, preserving relative paths."""
    written: list[str] = []
    if not src.is_dir():
        return written
    for path in src.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if not resolves_within_root(dest, rel):
            raise ValueError(f"import path escapes auxmem root: {rel}")
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, out)
        written.append(str(rel).replace("\\", "/"))
    return written


def _run_validate_and_moc(auxmem: Path) -> tuple[int, str]:
    moc = subprocess.run([_PYTHON, ".scripts/gen_mocs.py"], cwd=auxmem, capture_output=True, text=True)
    if moc.returncode != 0:
        detail = (moc.stdout or moc.stderr or "").strip() or "MOC generation failed"
        return OPERATION_FAILED, detail
    val = subprocess.run(
        [_PYTHON, ".scripts/validate_auxmem.py", "--all"], cwd=auxmem, capture_output=True, text=True
    )
    detail = (val.stdout or val.stderr or "").strip()
    if val.returncode != 0:
        return NON_CONFORMANT, detail or "validation failed"
    return OK, detail or "auxmem validation clean."


def apply_validated_candidate(
    dest: Path,
    candidate: Path,
    *,
    report_writer,
    report_payload: dict,
) -> tuple[int, str, str]:
    """Validate candidate overlaid on a workspace copy, then apply to dest."""
    with tempfile.TemporaryDirectory(prefix="auxmem-import-") as td:
        workspace = Path(td) / "workspace"
        shutil.copytree(dest, workspace, symlinks=True)
        overlay_tree(candidate, workspace)
        rc, detail = _run_validate_and_moc(workspace)
        if rc != OK:
            log_dir = dest / ".auxmem" / "import-failures"
            log_dir.mkdir(parents=True, exist_ok=True)
            (log_dir / "latest.log").write_text(detail + "\n", encoding="utf-8")
            return rc, "Import candidate failed validation; target auxmem unchanged.\n" + detail, ""
        overlay_tree(candidate, dest)
        report_writer(dest, report_payload)
        final_rc, final_detail = _run_validate_and_moc(dest)
        if final_rc != OK:
            return final_rc, final_detail, ""
        return OK, final_detail, ""


def write_failure_note(dest: Path, summary: str, body: str) -> None:
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
    cfg = json.loads(config_path(dest).read_text(encoding="utf-8"))
    domain = next(iter(cfg.get("domains", {}).values()), "reference")
    path = dest / ".auxmem" / "import-failures" / "latest.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "title: Import failed",
                f"summary: {summary}",
                "type: log",
                "status: active",
                f"domain: {domain}",
                f"created: {today}",
                f"updated: {today}",
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
