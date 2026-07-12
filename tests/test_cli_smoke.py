"""CLI smoke tests for the auxmem command."""

from __future__ import annotations

import subprocess
import sys

import pytest

from auxmem.cli import main
from tests.helpers import run_auxmem, validate_auxmem


def test_main_without_args_prints_help(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "AuxMem Manager" in captured.out
    assert "commands:" in captured.out


@pytest.mark.parametrize(
    "args,needle",
    [
        (["seed", "--help"], "normalize"),
        (["check", "--help"], "moc freshness"),
    ],
)
def test_help_subcommands(args, needle):
    result = run_auxmem(args)
    assert result.returncode == 0
    assert needle.lower() in (result.stdout + result.stderr).lower()


def test_new_creates_scaffold(tmp_path):
    dest = tmp_path / "fresh"
    result = run_auxmem(
        [
            "new",
            "--name",
            "fresh",
            "--path",
            str(dest),
            "--domain",
            "10-projects=projects",
            "--domain",
            "20-governance=governance",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert dest.is_dir()
    assert (dest / ".scripts" / "auxmem.config.json").is_file()
    assert (dest / ".auxmem" / "manifest.json").is_file()


def test_doctor_validates_scaffold(tmp_auxmem):
    result = run_auxmem(["doctor", str(tmp_auxmem)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation" in (result.stdout + result.stderr).lower()


def test_upgrade_reports_up_to_date(tmp_auxmem):
    result = run_auxmem(["upgrade", str(tmp_auxmem)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "already at template version" in result.stdout


def test_scaffold_passes_validator(tmp_auxmem):
    result = validate_auxmem(tmp_auxmem)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wheel_install_new_smoke(tmp_path):
    """Install the built wheel in an isolated venv and run auxmem new."""
    from tests.helpers import build_wheel

    wheel = build_wheel(tmp_path / "dist")
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    pip = venv / "bin" / "pip"
    if not pip.exists():
        pip = venv / "Scripts" / "pip.exe"
    subprocess.run([str(pip), "install", str(wheel)], check=True, capture_output=True, text=True)

    auxmem_bin = venv / "bin" / "auxmem"
    if not auxmem_bin.exists():
        auxmem_bin = venv / "Scripts" / "auxmem.exe"

    dest = tmp_path / "installed-auxmem"
    proc = subprocess.run(
        [str(auxmem_bin), "new", "--name", "wheel-test", "--path", str(dest),
         "--domain", "10-projects=projects"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert dest.is_dir()
    assert (dest / ".scripts" / "validate_auxmem.py").is_file()
