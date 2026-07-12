"""Deterministic evaluation harness for reference corpora (AUX-012).

Measures structural guarantees Koinome provides without invoking an LLM.
Agent-assisted evaluation uses the prompt set in examples/evaluation/.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_ROOT = REPO_ROOT / "examples"
REFERENCE_NAMES = ("software-project", "consulting-engagement", "research-project")


@dataclass
class EvalResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class ReferenceReport:
    corpus: str
    results: list[EvalResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results)


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _python_script(script: str, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return _run([sys.executable, script, *args], cwd=cwd)


def evaluate_validation(corpus: Path) -> EvalResult:
    proc = _python_script(".scripts/validate_corpus.py", "--all", cwd=corpus)
    if proc.returncode != 0:
        return EvalResult("validation", False, proc.stdout + proc.stderr)
    return EvalResult("validation", True)


def evaluate_conformance(corpus: Path) -> EvalResult:
    proc = _python_script(".scripts/check_corpus.py", cwd=corpus)
    if proc.returncode != 0:
        return EvalResult("conformance", False, proc.stdout + proc.stderr)
    return EvalResult("conformance", True)


def evaluate_moc_freshness(corpus: Path) -> EvalResult:
    proc = _python_script(".scripts/gen_mocs.py", "--check", cwd=corpus)
    if proc.returncode != 0:
        return EvalResult("moc-freshness", False, proc.stdout + proc.stderr)
    return EvalResult("moc-freshness", True)


def evaluate_synthesis_signals(corpus: Path) -> EvalResult:
    proc = _python_script(".scripts/synthesis_status.py", "--json", cwd=corpus)
    if proc.returncode != 0:
        return EvalResult("synthesis-signals", False, proc.stderr)
    data = json.loads(proc.stdout)
    if not data.get("stale"):
        return EvalResult(
            "synthesis-signals",
            False,
            "expected at least one stale synthesis in reference corpus",
        )
    if not data.get("review"):
        return EvalResult(
            "synthesis-signals",
            False,
            "expected synthesized pages awaiting review",
        )
    return EvalResult("synthesis-signals", True, f"stale={len(data['stale'])}")


def evaluate_superseded_adr(corpus: Path) -> EvalResult:
    decisions = corpus / "60-decisions"
    if not decisions.is_dir():
        return EvalResult("superseded-adr", False, "60-decisions missing")
    found_superseded = False
    found_active_successor = False
    for path in decisions.glob("adr-*.md"):
        text = path.read_text(encoding="utf-8")
        if "status: superseded" in text:
            found_superseded = True
        if "status: active" in text and "Supersedes" in text:
            found_active_successor = True
    if not found_superseded or not found_active_successor:
        return EvalResult(
            "superseded-adr",
            False,
            "need one superseded ADR and one active successor",
        )
    return EvalResult("superseded-adr", True)


def evaluate_unresolved_contradiction(corpus: Path) -> EvalResult:
    markers = ("contradiction", "conflict", "disagree", "unresolved")
    synthesis = corpus / "85-synthesis"
    if not synthesis.is_dir():
        return EvalResult("unresolved-contradiction", False, "85-synthesis missing")
    for path in synthesis.rglob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        if any(m in text for m in markers):
            return EvalResult("unresolved-contradiction", True, path.name)
    return EvalResult(
        "unresolved-contradiction",
        False,
        "no documented contradiction in synthesis pages",
    )


def evaluate_broken_link_detection(corpus: Path) -> EvalResult:
    with tempfile.TemporaryDirectory(prefix="corpus-eval-broken-") as td:
        copy = Path(td) / "copy"
        shutil.copytree(corpus, copy, dirs_exist_ok=True)
        cfg = json.loads((copy / ".scripts/koinome.config.json").read_text(encoding="utf-8"))
        folder, slug = next(iter(cfg["domains"].items()))
        bad = copy / folder / "broken-link-probe.md"
        bad.write_text(
            "---\n"
            "title: Broken link probe\n"
            "summary: Probe note with an internal link that should fail validation.\n"
            "type: project-doc\n"
            "status: active\n"
            f"domain: {slug}\n"
            "created: 2026-07-01\n"
            "updated: 2026-07-01\n"
            "---\n"
            "See [missing](../99-archive/does-not-exist.md).\n",
            encoding="utf-8",
        )
        proc = _python_script(".scripts/validate_corpus.py", "--all", cwd=copy)
        combined = proc.stdout + proc.stderr
        if proc.returncode == 0 or "broken internal link" not in combined:
            return EvalResult(
                "broken-link-detection",
                False,
                "validator did not reject broken internal link",
            )
    return EvalResult("broken-link-detection", True)


def evaluate_recovery_from_deletion(corpus: Path) -> EvalResult:
    with tempfile.TemporaryDirectory(prefix="corpus-eval-delete-") as td:
        copy = Path(td) / "copy"
        shutil.copytree(corpus, copy, dirs_exist_ok=True)
        hits = list((copy / "60-decisions").glob("adr-0002*.md"))
        if not hits:
            return EvalResult("recovery-deletion", False, "no ADR-0002 note to delete")
        victim = hits[0]
        victim.unlink()
        proc = _python_script(".scripts/validate_corpus.py", "--all", cwd=copy)
        combined = proc.stdout + proc.stderr
        if proc.returncode == 0:
            return EvalResult(
                "recovery-deletion",
                False,
                "validator should fail after deleting a linked ADR",
            )
        if "broken internal link" not in combined:
            return EvalResult(
                "recovery-deletion",
                False,
                f"expected broken internal link, got: {combined[:300]}",
            )
    return EvalResult("recovery-deletion", True)


def evaluate_upgrade_preservation(corpus: Path) -> EvalResult:
    proc = _run(
        [sys.executable, "-m", "koinome.cli", "upgrade", str(corpus), "--dry-run"],
        cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        return EvalResult("upgrade-preservation", False, proc.stdout + proc.stderr)
    lowered = proc.stdout.lower()
    if "up-to-date" not in lowered and "already at template version" not in lowered:
        return EvalResult(
            "upgrade-preservation",
            False,
            f"unexpected upgrade output: {proc.stdout}",
        )
    return EvalResult("upgrade-preservation", True)


def evaluate_plain_text_readability(corpus: Path) -> EvalResult:
    for path in corpus.rglob("*.md"):
        if ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return EvalResult("plain-text-readability", False, f"{path}: {exc}")
        if not text.strip():
            return EvalResult("plain-text-readability", False, f"empty note: {path}")
    return EvalResult("plain-text-readability", True)


def evaluate_reference(corpus: Path) -> ReferenceReport:
    name = corpus.name
    checks = [
        evaluate_validation,
        evaluate_conformance,
        evaluate_moc_freshness,
        evaluate_synthesis_signals,
        evaluate_superseded_adr,
        evaluate_unresolved_contradiction,
        evaluate_broken_link_detection,
        evaluate_recovery_from_deletion,
        evaluate_upgrade_preservation,
        evaluate_plain_text_readability,
    ]
    report = ReferenceReport(corpus=name)
    for check in checks:
        report.results.append(check(corpus))
    return report


def evaluate_all_references(root: Path | None = None) -> list[ReferenceReport]:
    base = root or EXAMPLES_ROOT
    reports = []
    for name in REFERENCE_NAMES:
        path = base / name
        if not path.is_dir():
            raise FileNotFoundError(f"reference corpus missing: {path}")
        reports.append(evaluate_reference(path))
    return reports


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run deterministic reference corpus evaluation")
    parser.add_argument(
        "--examples-root",
        type=Path,
        default=EXAMPLES_ROOT,
        help="directory containing reference corpus folders",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    reports = evaluate_all_references(args.examples_root)
    failed = [r for r in reports if not r.passed]

    if args.json:
        payload = {
            r.corpus: {res.name: {"ok": res.ok, "detail": res.detail} for res in r.results}
            for r in reports
        }
        print(json.dumps(payload, indent=2))
    else:
        for report in reports:
            print(f"== {report.corpus} ==")
            for res in report.results:
                status = "ok" if res.ok else "FAIL"
                suffix = f" ({res.detail})" if res.detail else ""
                print(f"  [{status}] {res.name}{suffix}")

    if failed:
        print(f"\nevaluation failed for: {', '.join(r.corpus for r in failed)}", file=sys.stderr)
        return 1
    print("\ndeterministic evaluation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
