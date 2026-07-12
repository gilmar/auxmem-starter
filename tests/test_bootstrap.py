"""Bootstrap script safety, idempotency, and skill handling."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pytest

from tests.helpers import REPO_ROOT, scaffold_auxmem, validate_auxmem

TEMPLATE_BOOTSTRAP = REPO_ROOT / "auxmem" / "template" / "bootstrap.sh"


def run_bootstrap(dest, *extra_args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "bootstrap.sh", *extra_args],
        cwd=dest,
        env=env,
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
    venv = tmp_path / "nopyyaml"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest, no_bootstrap=True)
    env = os.environ.copy()
    env["PATH"] = f"{venv / 'bin'}:{env['PATH']}"
    result = run_bootstrap(dest, env=env)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "PyYAML" in combined or "pyyaml" in combined.lower()
    assert "uv tool install" in combined or "pipx install" in combined


def test_bootstrap_is_idempotent(tmp_path):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest, no_bootstrap=True)
    first = run_bootstrap(dest)
    second = run_bootstrap(dest)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert (dest / ".git" / "hooks" / "pre-commit").is_file()


def test_bootstrap_with_spaces_in_path(tmp_path):
    dest = tmp_path / "my auxmem"
    scaffold_auxmem(dest, name="space-test", no_bootstrap=True)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr
    validation = validate_auxmem(dest)
    assert validation.returncode == 0, validation.stdout + validation.stderr


def test_bootstrap_skips_existing_provider_skill_dir(tmp_path):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest, no_bootstrap=True)
    user_skill = dest / ".claude" / "skills" / "my-skill" / "SKILL.md"
    user_skill.parent.mkdir(parents=True)
    user_skill.write_text("user content\n", encoding="utf-8")
    result = run_bootstrap(dest)
    assert result.returncode == 0
    assert "skipping to avoid overwriting" in result.stdout + result.stderr
    assert user_skill.read_text(encoding="utf-8") == "user content\n"


def test_refresh_skills_updates_copied_provider_dir(tmp_path):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest, no_bootstrap=True)
    provider = dest / ".claude" / "skills"
    shutil.copytree(dest / ".skills", provider)
    (dest / ".auxmem").mkdir(exist_ok=True)
    (dest / ".auxmem" / "skills-copies").write_text(".claude/skills\n", encoding="utf-8")
    marker = "<!-- refresh-marker -->"
    skill_md = dest / ".skills" / "auxmem-init" / "SKILL.md"
    skill_md.write_text(skill_md.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8")
    result = run_bootstrap(dest, "--refresh-skills")
    assert result.returncode == 0, result.stdout + result.stderr
    assert marker in (provider / "auxmem-init" / "SKILL.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "provider_dir",
    [".claude/skills", ".codex/skills", ".gemini/skills", ".cursor/skills"],
)
def test_bootstrap_links_or_copies_provider_skills(tmp_path, provider_dir: str):
    dest = tmp_path / "auxmem"
    scaffold_auxmem(dest, no_bootstrap=True)
    result = run_bootstrap(dest)
    assert result.returncode == 0, result.stdout + result.stderr
    path = dest / provider_dir
    assert path.is_symlink() or path.is_dir()
    if path.is_symlink():
        assert path.resolve() == (dest / ".skills").resolve()
