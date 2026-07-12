"""Release and version consistency checks (AUX-011).

Run via ``python -m koinome.release_check`` or ``bash scripts/check_release.sh``.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from koinome import __version__
from koinome.manifest import verify_bundled_template
from koinome.upgrade import MANIFEST_SRC, TEMPLATE_DIR
from koinome.version import CONFORMANCE_VERSION, TEMPLATE_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
COMPATIBILITY = REPO_ROOT / "docs" / "COMPATIBILITY.md"
RELEASE_DOC = REPO_ROOT / "docs" / "RELEASE.md"
MISTAKEN_PYPI_VERSION = "2.0.0"

FIXTURE_SCAN_DIRS = (
    REPO_ROOT / "tests" / "fixtures",
    REPO_ROOT / "tests" / "helpers.py",
)

FORBIDDEN_FIXTURE_PATTERNS = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"@[a-z0-9.-]+\.(com|org|net|io)\b", re.I),
)

ALLOWED_FIXTURE_EMAILS = frozenset(
    {
        "test@koinome",
        "test@example.com",
        "user@example.com",
    }
)

REQUIRED_COMPATIBILITY_HEADERS = (
    "Claude Code",
    "Codex CLI",
    "Gemini CLI",
    "Cursor",
    "macOS",
    "Linux",
    "WSL2",
)

REQUIRED_COMPATIBILITY_COLUMNS = (
    "status",
    "last verified",
    "smoke procedure",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


class ReleaseCheckError(Exception):
    """One or more release checks failed."""


def _read_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise ReleaseCheckError("pyproject.toml missing version field")
    return match.group(1)


def _version_tuple(version: str) -> tuple[int, ...]:
    match = re.match(r"^(\d+(?:\.\d+)*)", version)
    if not match:
        raise ReleaseCheckError(f"invalid version for release check: {version}")
    return tuple(int(part) for part in match.group(1).split("."))


def check_cli_version_consistency() -> CheckResult:
    pyproject = _read_pyproject_version()
    if pyproject != __version__:
        return CheckResult(
            "cli-version",
            False,
            f"pyproject.toml ({pyproject}) != koinome.__version__ ({__version__})",
        )
    return CheckResult("cli-version", True, pyproject)


def check_template_version_consistency() -> CheckResult:
    manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    manifest_version = manifest.get("template_version")
    if manifest_version != TEMPLATE_VERSION:
        return CheckResult(
            "template-version",
            False,
            f"manifest template_version ({manifest_version}) != "
            f"TEMPLATE_VERSION ({TEMPLATE_VERSION})",
        )
    return CheckResult("template-version", True, TEMPLATE_VERSION)


def check_conformance_version_consistency() -> CheckResult:
    manifest = json.loads(MANIFEST_SRC.read_text(encoding="utf-8"))
    manifest_version = manifest.get("conformance_version")
    if manifest_version != CONFORMANCE_VERSION:
        return CheckResult(
            "conformance-version",
            False,
            f"manifest conformance_version ({manifest_version}) != "
            f"CONFORMANCE_VERSION ({CONFORMANCE_VERSION})",
        )
    return CheckResult("conformance-version", True, CONFORMANCE_VERSION)


def check_target_version(target: str) -> CheckResult:
    if target == __version__:
        return CheckResult("target-version", True, target)
    return CheckResult(
        "target-version",
        False,
        f"requested release version {target} does not match source {__version__}",
    )


def check_prerelease_not_stable(target: str) -> CheckResult:
    if target in {"1.0.0", "1.0", "1"}:
        return CheckResult(
            "prerelease-policy",
            False,
            "refusing stable 1.0 release during hardening cycle",
        )
    if target == "0.0.0":
        return CheckResult(
            "prerelease-policy",
            False,
            "refusing to publish 0.0.0; use an explicit prerelease (e.g. 0.1.0rc1)",
        )
    if _version_tuple(target) <= _version_tuple(MISTAKEN_PYPI_VERSION) and not target.startswith(
        "0."
    ):
        return CheckResult(
            "prerelease-policy",
            False,
            f"refusing version {target} at or below mistaken PyPI {MISTAKEN_PYPI_VERSION}",
        )
    return CheckResult("prerelease-policy", True, target)


def check_changelog_entry(version: str) -> CheckResult:
    text = CHANGELOG.read_text(encoding="utf-8")
    if version == "0.0.0":
        if "Unreleased" in text or "0.0.0" in text:
            return CheckResult("changelog", True, "pre-release cycle documented")
        return CheckResult("changelog", False, "CHANGELOG missing Unreleased or 0.0.0 section")
    if version in text:
        return CheckResult("changelog", True, f"mentions {version}")
    return CheckResult("changelog", False, f"CHANGELOG missing entry for {version}")


def check_release_docs() -> CheckResult:
    missing = [path.name for path in (RELEASE_DOC, COMPATIBILITY) if not path.is_file()]
    if missing:
        return CheckResult("release-docs", False, f"missing: {', '.join(missing)}")
    return CheckResult("release-docs", True)


def check_compatibility_matrix() -> CheckResult:
    text = COMPATIBILITY.read_text(encoding="utf-8")
    missing_headers = [h for h in REQUIRED_COMPATIBILITY_HEADERS if h not in text]
    missing_columns = [c for c in REQUIRED_COMPATIBILITY_COLUMNS if c.lower() not in text.lower()]
    if missing_headers or missing_columns:
        parts = []
        if missing_headers:
            parts.append(f"missing environments: {missing_headers}")
        if missing_columns:
            parts.append(f"missing columns: {missing_columns}")
        return CheckResult("compatibility-matrix", False, "; ".join(parts))
    if "compatibility_smoke.sh" not in text:
        return CheckResult(
            "compatibility-matrix",
            False,
            "must reference scripts/compatibility_smoke.sh smoke procedure",
        )
    return CheckResult("compatibility-matrix", True)


def check_bundled_template() -> CheckResult:
    try:
        verify_bundled_template(TEMPLATE_DIR, MANIFEST_SRC)
    except ValueError as exc:
        return CheckResult("bundled-template", False, str(exc))
    return CheckResult("bundled-template", True)


def check_fixture_hygiene() -> CheckResult:
    violations: list[str] = []
    paths: list[Path] = []
    for item in FIXTURE_SCAN_DIRS:
        if item.is_file():
            paths.append(item)
        elif item.is_dir():
            paths.extend(p for p in item.rglob("*") if p.is_file())

    for path in paths:
        if path.suffix in {".pyc", ".png", ".jpg"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(REPO_ROOT)
        for pattern in FORBIDDEN_FIXTURE_PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(0)
                if "@" in value:
                    email = value.lstrip("@")
                    if email in ALLOWED_FIXTURE_EMAILS:
                        continue
                violations.append(f"{rel}: {value}")
    if violations:
        return CheckResult("fixture-hygiene", False, "\n".join(violations[:10]))
    return CheckResult("fixture-hygiene", True)


def check_generated_corpus_ci() -> CheckResult:
    workflow = TEMPLATE_DIR / ".github" / "workflows" / "koinome-check.yml"
    if not workflow.is_file():
        return CheckResult("corpus-ci", False, "template workflow missing")
    text = workflow.read_text(encoding="utf-8")
    if "check_corpus.py" not in text:
        return CheckResult("corpus-ci", False, "workflow must run check_corpus.py")
    return CheckResult("corpus-ci", True)


def check_fresh_scaffold_and_upgrade() -> CheckResult:
    try:
        run_scaffold_smoke()
    except ReleaseCheckError as exc:
        return CheckResult("scaffold-upgrade", False, str(exc))
    return CheckResult("scaffold-upgrade", True)


def run_scaffold_smoke() -> None:
    """Fresh scaffold, validate, upgrade dry-run, and conformance check."""
    import tempfile

    from tests.helpers import (
        run_conformance_check,
        run_koinome,
        scaffold_corpus,
        validate_corpus,
    )

    with tempfile.TemporaryDirectory(prefix="corpus-release-") as td:
        dest = Path(td) / "release-smoke"
        scaffold_corpus(dest)
        validation = validate_corpus(dest)
        if validation.returncode != 0:
            raise ReleaseCheckError(
                "fresh scaffold failed validation:\n"
                f"{validation.stdout}\n{validation.stderr}"
            )
        conformance = run_conformance_check(dest)
        if conformance.returncode != 0:
            raise ReleaseCheckError(
                "fresh scaffold failed conformance:\n"
                f"{conformance.stdout}\n{conformance.stderr}"
            )
        upgrade = run_koinome(["upgrade", str(dest), "--dry-run"])
        if upgrade.returncode != 0:
            raise ReleaseCheckError(
                "upgrade dry-run failed on fresh scaffold:\n"
                f"{upgrade.stdout}\n{upgrade.stderr}"
            )
        workflow = dest / ".github" / "workflows" / "koinome-check.yml"
        if not workflow.is_file():
            raise ReleaseCheckError("scaffold missing generated koinome-check.yml")


def check_clean_git_tree() -> CheckResult:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return CheckResult("clean-tree", False, proc.stderr.strip())
    if proc.stdout.strip():
        return CheckResult(
            "clean-tree",
            False,
            "working tree is not clean; commit or stash before release",
        )
    return CheckResult("clean-tree", True)


def run_checks(
    *,
    strict: bool = False,
    target_version: str | None = None,
    require_clean_tree: bool = False,
    skip_scaffold: bool = False,
) -> list[CheckResult]:
    results = [
        check_cli_version_consistency(),
        check_template_version_consistency(),
        check_conformance_version_consistency(),
        check_release_docs(),
        check_compatibility_matrix(),
        check_changelog_entry(target_version or __version__),
        check_bundled_template(),
        check_fixture_hygiene(),
        check_generated_corpus_ci(),
    ]
    if target_version:
        results.extend(
            [
                check_target_version(target_version),
                check_prerelease_not_stable(target_version),
                check_changelog_entry(target_version),
            ]
        )
    if require_clean_tree:
        results.append(check_clean_git_tree())
    if strict and not skip_scaffold:
        results.append(check_fresh_scaffold_and_upgrade())
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Koinome release consistency checks")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="run scaffold/upgrade smoke in addition to static checks",
    )
    parser.add_argument(
        "--target-version",
        metavar="VERSION",
        help="refuse release unless source versions match VERSION",
    )
    parser.add_argument(
        "--require-clean-tree",
        action="store_true",
        help="fail when git working tree is dirty",
    )
    parser.add_argument(
        "--scaffold-smoke",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    if args.scaffold_smoke:
        try:
            run_scaffold_smoke()
        except ReleaseCheckError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0

    results = run_checks(
        strict=args.strict,
        target_version=args.target_version,
        require_clean_tree=args.require_clean_tree,
        skip_scaffold=False,
    )
    failed = [r for r in results if not r.ok]
    for result in results:
        status = "ok" if result.ok else "FAIL"
        suffix = f" ({result.detail})" if result.detail and not result.ok else ""
        print(f"  [{status}] {result.name}{suffix}")
    if failed:
        print(f"\nrelease check failed ({len(failed)} check(s))", file=sys.stderr)
        return 1
    print("\nrelease check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
