"""Bootstrap script safety, idempotency, and skill handling."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from koinome.bash_path import resolve_bash
from tests.helpers import REPO_ROOT, scaffold_corpus, validate_corpus

TEMPLATE_BOOTSTRAP = REPO_ROOT / "koinome" / "template" / "bootstrap.sh"


def run_bootstrap(dest, *extra_args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    merged.setdefault("KOINOME_PYTHON", sys.executable)
    if env:
        merged.update(env)
    return subprocess.run(
        [resolve_bash(), "bootstrap.sh", *extra_args],
        cwd=dest,
        env=merged,
        capture_output=True,
        text=True,
    )


def test_bootstrap_does_not_auto_install_packages():
    text = TEMPLATE_BOOTSTRAP.read_text(encoding="utf-8")
    assert "--break-system-packages" not in text
    executable = []
    in_heredoc = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("cat <<"):
            in_heredoc = True
            continue
        if in_heredoc:
            if stripped == "EOF":
                in_heredoc = False
            continue
        if stripped.startswith("pip ") or stripped.startswith("python3 -m pip"):
            executable.append(stripped)
    assert not executable, f"bootstrap must not run pip automatically: {executable}"


def test_bootstrap_fails_without_pyyaml(tmp_path):
    if os.name == "nt":
        pytest.skip("venv PATH layout differs on Windows; covered on Unix CI")
    venv = tmp_path / "nopyyaml"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    env = {
        "PATH": f"{venv / 'bin'}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "KOINOME_PYTHON": str(venv / "bin" / "python"),
        "HOME": str(tmp_path / "empty-home"),
        "UV_TOOL_DIR": str(tmp_path / "empty-uv-tools"),
    }
    (tmp_path / "empty-home").mkdir()
    (tmp_path / "empty-uv-tools").mkdir()
    result = run_bootstrap(dest, env=env)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "PyYAML" in combined or "pyyaml" in combined.lower()
    assert "KOINOME_PYTHON" in combined or "uv tool install" in combined or "pip install pyyaml" in combined


def test_bootstrap_uses_koinome_python_env(tmp_path):
    """PATH python3 may lack PyYAML; KOINOME_PYTHON (tool/env) must win (issue #38)."""
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    broken = tmp_path / "broken-bin"
    broken.mkdir()
    fake = broken / "python3"
    fake.write_text("#!/bin/sh\necho 'no yaml here' >&2\nexit 1\n", encoding="utf-8")
    fake.chmod(0o755)
    env = {
        "PATH": f"{broken}{os.pathsep}{os.environ.get('PATH', '')}",
        "KOINOME_PYTHON": sys.executable,
    }
    result = run_bootstrap(dest, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (dest / ".koinome" / "python").is_file()
    recorded = (dest / ".koinome" / "python").read_text(encoding="utf-8").strip()
    assert recorded == sys.executable


def test_scaffold_passes_koinome_python(tmp_path, monkeypatch):
    """koinome new must set KOINOME_PYTHON so bootstrap does not rely on PATH."""
    import koinome.scaffold as scaffold_mod

    seen: dict[str, str] = {}

    def fake_run(cmd, **kwargs):
        env = kwargs.get("env") or {}
        seen["KOINOME_PYTHON"] = env.get("KOINOME_PYTHON", "")
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    monkeypatch.setattr(scaffold_mod.subprocess, "run", fake_run)
    dest = tmp_path / "corpus"
    scaffold_mod.scaffold("t", dest, {"10-projects": "projects"}, run_bootstrap=True)
    assert seen["KOINOME_PYTHON"] == sys.executable


def test_bootstrap_is_idempotent(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    first = run_bootstrap(dest)
    second = run_bootstrap(dest)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert (dest / ".git" / "hooks" / "pre-commit").is_file()


def test_bootstrap_with_spaces_in_path(tmp_path):
    dest = tmp_path / "my corpus"
    scaffold_corpus(dest, name="space-test", no_bootstrap=True)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr
    validation = validate_corpus(dest)
    assert validation.returncode == 0, validation.stdout + validation.stderr


def test_bootstrap_skips_existing_provider_skill_dir(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    user_skill = dest / ".claude" / "skills" / "my-skill" / "SKILL.md"
    user_skill.parent.mkdir(parents=True)
    user_skill.write_text("user content\n", encoding="utf-8")
    result = run_bootstrap(dest)
    assert result.returncode == 0
    assert "skipping to avoid overwriting" in result.stdout + result.stderr
    assert user_skill.read_text(encoding="utf-8") == "user content\n"


def test_refresh_skills_updates_copied_provider_dir(tmp_path):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    provider = dest / ".claude" / "skills"
    shutil.copytree(dest / ".skills", provider)
    (dest / ".koinome").mkdir(exist_ok=True)
    (dest / ".koinome" / "skills-copies").write_text(".claude/skills\n", encoding="utf-8")
    marker = "<!-- refresh-marker -->"
    skill_md = dest / ".skills" / "koinome-init" / "SKILL.md"
    skill_md.write_text(skill_md.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8")
    result = run_bootstrap(dest, "--refresh-skills")
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker in (provider / "koinome-init" / "SKILL.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "provider_dir",
    [".claude/skills", ".codex/skills", ".gemini/skills", ".cursor/skills"],
)
def test_bootstrap_links_or_copies_provider_skills(tmp_path, provider_dir: str):
    dest = tmp_path / "corpus"
    scaffold_corpus(dest, no_bootstrap=True)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr
    path = dest / provider_dir
    assert path.is_symlink() or path.is_dir()
    if path.is_symlink():
        assert path.resolve() == (dest / ".skills").resolve()
