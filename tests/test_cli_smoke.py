"""CLI smoke tests for the corpus command."""

from __future__ import annotations

import subprocess
import sys

import pytest

from koinome.cli import main
from tests.helpers import run_koinome, validate_corpus


def test_main_without_args_prints_help(capsys):
    assert main([]) == 0
    captured = capsys.readouterr()
    assert "Koinome CLI" in captured.out
    assert "commands:" in captured.out


@pytest.mark.parametrize(
    "args,needle",
    [
        (["seed", "--help"], "normalize"),
        (["check", "--help"], "moc freshness"),
    ],
)
def test_help_subcommands(args, needle):
    result = run_koinome(args)
    assert result.returncode == 0
    assert needle.lower() in (result.stdout + result.stderr).lower()


def test_new_creates_scaffold(tmp_path):
    dest = tmp_path / "fresh"
    result = run_koinome(
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
    assert (dest / ".scripts" / "koinome.config.json").is_file()
    assert (dest / ".koinome" / "manifest.json").is_file()


def test_doctor_validates_scaffold(tmp_corpus):
    result = run_koinome(["doctor", str(tmp_corpus)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validation" in (result.stdout + result.stderr).lower()


def test_upgrade_reports_up_to_date(tmp_corpus):
    result = run_koinome(["upgrade", str(tmp_corpus)])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "already at template version" in result.stdout


def test_scaffold_passes_validator(tmp_corpus):
    result = validate_corpus(tmp_corpus)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wheel_install_new_smoke(tmp_path):
    """Install the built wheel in an isolated venv and run koinome new."""
    from tests.helpers import build_wheel

    wheel = build_wheel(tmp_path / "dist")
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    pip = venv / "bin" / "pip"
    if not pip.exists():
        pip = venv / "Scripts" / "pip.exe"
    subprocess.run([str(pip), "install", str(wheel)], check=True, capture_output=True, text=True)

    koinome_bin = venv / "bin" / "koinome"
    if not koinome_bin.exists():
        koinome_bin = venv / "Scripts" / "corpus.exe"

    dest = tmp_path / "installed-corpus"
    proc = subprocess.run(
        [str(koinome_bin), "new", "--name", "wheel-test", "--path", str(dest),
         "--domain", "10-projects=projects"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert dest.is_dir()
    assert (dest / ".scripts" / "validate_corpus.py").is_file()
