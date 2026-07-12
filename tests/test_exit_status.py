"""Failure propagation for corpus CLI operations (AUX-007)."""

from __future__ import annotations

import stat

import pytest

from koinome import exit_codes
from koinome.cli import main
from tests.helpers import note_with_fm, scaffold_corpus, write_note

VALID_FM = dict(
    title="Test note",
    summary="Concrete nouns for grep retrieval in exit-status fixture tests.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


@pytest.fixture
def doctor_corpus(tmp_path):
    dest = tmp_path / "doctor"
    scaffold_corpus(dest)
    return dest


def test_doctor_succeeds_on_valid_corpus(doctor_corpus):
    rc = main(["doctor", str(doctor_corpus)])
    assert rc == exit_codes.OK


def test_doctor_returns_non_conformant_on_invalid_note(doctor_corpus):
    write_note(
        doctor_corpus,
        "10-projects/bad.md",
        note_with_fm("Body.", **{**VALID_FM, "type": "not-a-type"}),
    )
    rc = main(["doctor", str(doctor_corpus)])
    assert rc == exit_codes.NON_CONFORMANT


def test_doctor_returns_operation_failed_when_moc_fails(doctor_corpus):
    moc = doctor_corpus / ".scripts/gen_mocs.py"
    moc.write_text("#!/usr/bin/env python3\nimport sys\nprint('moc broke')\nsys.exit(1)\n")
    moc.chmod(moc.stat().st_mode | stat.S_IXUSR)
    rc = main(["doctor", str(doctor_corpus)])
    assert rc == exit_codes.OPERATION_FAILED


def test_validate_and_moc_reports_moc_phase(doctor_corpus):
    from koinome import importers

    moc = doctor_corpus / ".scripts/gen_mocs.py"
    moc.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(2)\n")
    moc.chmod(moc.stat().st_mode | stat.S_IXUSR)
    code, message = importers.validate_and_moc(doctor_corpus)
    assert code == exit_codes.OPERATION_FAILED
    assert "MOC generation failed" in message


def test_validate_and_moc_reports_validation_phase(doctor_corpus):
    from koinome import importers

    write_note(
        doctor_corpus,
        "10-projects/bad.md",
        note_with_fm("Body.", **{**VALID_FM, "status": "not-valid"}),
    )
    code, message = importers.validate_and_moc(doctor_corpus)
    assert code == exit_codes.NON_CONFORMANT
    assert "Validation failed" in message


def test_upgrade_returns_non_conformant_when_validation_fails(tmp_path, monkeypatch):
    from koinome import upgrade as upgrade_mod

    dest = tmp_path / "upgrade-target"
    scaffold_corpus(dest)
    write_note(
        dest,
        "10-projects/bad.md",
        note_with_fm("Body.", **{**VALID_FM, "domain": "not-in-vocab"}),
    )

    def fake_upgrade(path, force=False, dry_run=False):
        return {
            "status": "upgraded",
            "from": "0.0.0",
            "to": "0.0.0",
            "changes": ["test change"],
            "conflicts": [],
            "backup": str(dest / ".koinome/backups/test"),
            "post_exit_code": exit_codes.NON_CONFORMANT,
            "post_phase": "validation",
            "post_detail": "corpus validation failed.",
        }

    monkeypatch.setattr(upgrade_mod, "upgrade", fake_upgrade)
    rc = main(["upgrade", str(dest)])
    assert rc == exit_codes.NON_CONFORMANT


def test_upgrade_returns_operation_failed_when_moc_fails(tmp_path, monkeypatch):
    from koinome import upgrade as upgrade_mod

    dest = tmp_path / "upgrade-target"
    scaffold_corpus(dest)

    def fake_upgrade(path, force=False, dry_run=False):
        return {
            "status": "upgraded",
            "from": "0.0.0",
            "to": "0.0.0",
            "changes": [],
            "conflicts": [],
            "backup": str(dest / ".koinome/backups/test"),
            "post_exit_code": exit_codes.OPERATION_FAILED,
            "post_phase": "MOC generation",
            "post_detail": "moc broke",
        }

    monkeypatch.setattr(upgrade_mod, "upgrade", fake_upgrade)
    rc = main(["upgrade", str(dest)])
    assert rc == exit_codes.OPERATION_FAILED


def test_seed_does_not_print_success_after_failure(tmp_path, capsys):
    bad_export = tmp_path / "bad.json"
    bad_export.write_text("{not json", encoding="utf-8")
    rc = main(["seed", str(bad_export), "--staging", str(tmp_path / "staging")])
    assert rc != exit_codes.OK
    captured = capsys.readouterr()
    assert "Stage 2" not in captured.out


def test_doctor_does_not_print_clean_after_validation_failure(doctor_corpus, capsys):
    write_note(
        doctor_corpus,
        "10-projects/bad.md",
        note_with_fm("Body.", **{**VALID_FM, "type": "bad-type"}),
    )
    rc = main(["doctor", str(doctor_corpus)])
    captured = capsys.readouterr()
    assert rc == exit_codes.NON_CONFORMANT
    assert "validation clean" not in captured.out.lower()
