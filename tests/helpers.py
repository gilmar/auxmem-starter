"""Shared helpers for AuxMem repository tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DOMAINS = [
    "10-projects=projects",
    "20-governance=governance",
]


class CommandResult:
    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def run_cmd(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> CommandResult:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    proc = subprocess.run(
        args,
        cwd=cwd,
        env=merged,
        capture_output=True,
        text=True,
        input=input_text,
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def run_auxmem(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    return run_cmd([sys.executable, "-m", "auxmem.cli", *args], cwd=cwd, env=env)


def run_git(args: list[str], *, cwd: Path) -> CommandResult:
    return run_cmd(["git", *args], cwd=cwd)


def init_git_repo(path: Path, *, user_name: str = "auxmem-test", user_email: str = "test@auxmem") -> None:
    run_git(["init", "-q"], cwd=path)
    run_git(["config", "user.name", user_name], cwd=path)
    run_git(["config", "user.email", user_email], cwd=path)


def create_bare_remote(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    run_cmd(["git", "init", "--bare", "-q", str(path)])
    return path


def scaffold_auxmem(
    dest: Path,
    *,
    name: str = "test-auxmem",
    domains: list[str] | None = None,
    no_bootstrap: bool = False,
) -> Path:
    args = ["new", "--name", name, "--path", str(dest)]
    for domain in domains or DEFAULT_DOMAINS:
        args.extend(["--domain", domain])
    if no_bootstrap:
        args.append("--no-bootstrap")
    result = run_auxmem(args)
    if result.returncode != 0:
        raise RuntimeError(
            f"auxmem new failed ({result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return dest.resolve()


def validate_auxmem(path: Path) -> CommandResult:
    return run_cmd(
        [sys.executable, ".scripts/validate_auxmem.py", "--all"],
        cwd=path,
    )


def run_validator(args: list[str], *, cwd: Path) -> CommandResult:
    return run_cmd([sys.executable, ".scripts/validate_auxmem.py", *args], cwd=cwd)


def run_staged_snapshot_check(path: Path) -> CommandResult:
    return run_cmd([sys.executable, ".scripts/check_staged_snapshot.py"], cwd=path)


def run_conformance_check(path: Path, *extra_args: str) -> CommandResult:
    return run_cmd([sys.executable, ".scripts/check_auxmem.py", *extra_args], cwd=path)


def run_sync(path: Path, *, env: dict[str, str] | None = None) -> CommandResult:
    return run_cmd([sys.executable, ".scripts/auxmem_sync.py", str(path)], cwd=path, env=env)


def gen_mocs(path: Path) -> CommandResult:
    return run_cmd([sys.executable, ".scripts/gen_mocs.py"], cwd=path)


def commit_all_valid(path: Path, message: str = "initial") -> None:
    init_git_repo(path)
    gen_mocs(path)
    run_git(["add", "-A"], cwd=path)
    result = run_git(["commit", "-m", message], cwd=path)
    if result.returncode != 0:
        raise RuntimeError(
            f"commit failed ({result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def attach_bare_remote(auxmem: Path, remote: Path, *, remote_name: str = "origin") -> str:
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=auxmem).stdout.strip()
    if run_git(["remote", "get-url", remote_name], cwd=auxmem).returncode != 0:
        run_git(["remote", "add", remote_name, str(remote)], cwd=auxmem)
    push = run_git(["push", "-u", remote_name, branch], cwd=auxmem)
    if push.returncode != 0:
        raise RuntimeError(f"push failed:\n{push.stdout}\n{push.stderr}")
    return branch


def clone_from_bare(bare: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    result = run_cmd(["git", "clone", "-q", str(bare), str(dest)])
    if result.returncode != 0:
        raise RuntimeError(f"clone failed:\n{result.stdout}\n{result.stderr}")
    init_git_repo(dest)
    return dest.resolve()


def git_branches(repo: Path, *, all_refs: bool = False) -> list[str]:
    args = ["branch", "--format=%(refname:short)"]
    if all_refs:
        args.insert(1, "-a")
    proc = run_git(args, cwd=repo)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def tree_bytes_snapshot(root: Path) -> dict[str, bytes]:
    snap: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        snap[str(path.relative_to(root))] = path.read_bytes()
    return snap


def git_add(path: Path, *rel_paths: str) -> CommandResult:
    return run_git(["add", *rel_paths], cwd=path)


def write_note(auxmem: Path, rel: str, content: str) -> Path:
    path = auxmem / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def note_with_fm(body: str = "Body text.", **fields) -> str:
    lines = ["---"]
    for key, val in fields.items():
        if isinstance(val, list):
            inner = ", ".join(str(v) for v in val)
            lines.append(f"{key}: [{inner}]")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append(body)
    return "\n".join(lines) + "\n"


def read_auxmem_config(path: Path) -> dict:
    cfg_path = path / ".scripts" / "auxmem.config.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def newest_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.glob("auxmem-*.whl"), key=lambda p: p.stat().st_mtime)
    if not wheels:
        raise FileNotFoundError(f"no wheel found under {dist_dir}")
    return wheels[-1]


def wheel_members(wheel_path: Path) -> set[str]:
    with zipfile.ZipFile(wheel_path) as zf:
        return set(zf.namelist())


def build_wheel(dist_dir: Path | None = None) -> Path:
    out = dist_dir or (REPO_ROOT / "dist")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["uv", "build", "--out-dir", str(out)], cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"uv build failed:\n{result.stdout}\n{result.stderr}")
    return newest_wheel(out)
