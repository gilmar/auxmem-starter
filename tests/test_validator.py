"""Adversarial coverage for auxmem/template/.scripts/validate_auxmem.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.helpers import note_with_fm, run_validator, scaffold_auxmem, write_note

sys.dont_write_bytecode = True

_TEMPLATE_VALIDATOR = (
    Path(__file__).resolve().parent.parent / "auxmem" / "template" / ".scripts" / "validate_auxmem.py"
)
_spec = importlib.util.spec_from_file_location("validate_auxmem_test", _TEMPLATE_VALIDATOR)
va = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(va)

VALID_FM = dict(
    title="Test note",
    summary="Concrete nouns for grep retrieval in validator fixture tests here.",
    type="project-doc",
    status="active",
    domain="projects",
    created="2026-07-04",
    updated="2026-07-04",
)


def _write(auxmem: Path, rel: str, body: str = "Body.", **fm) -> Path:
    merged = {**VALID_FM, **fm}
    return write_note(auxmem, rel, note_with_fm(body, **merged))


def _validate(auxmem: Path, rel: str):
    return run_validator([rel], cwd=auxmem)


def _errors(auxmem: Path, rel: str) -> str:
    return _validate(auxmem, rel).stdout


# ---------------------------------------------------------------- frontmatter


def test_missing_frontmatter(validator_auxmem):
    write_note(validator_auxmem, "10-projects/no-fm.md", "# no frontmatter\n")
    assert "missing frontmatter" in _errors(validator_auxmem, "10-projects/no-fm.md")


def test_malformed_yaml(validator_auxmem):
    write_note(validator_auxmem, "10-projects/bad-yaml.md", "---\ntitle: [unclosed\n---\n")
    assert "not valid YAML" in _errors(validator_auxmem, "10-projects/bad-yaml.md")


def test_non_mapping_yaml(validator_auxmem):
    write_note(validator_auxmem, "10-projects/scalar-fm.md", "---\njust a string\n---\n")
    assert "not a mapping" in _errors(validator_auxmem, "10-projects/scalar-fm.md")


def test_duplicate_yaml_keys(validator_auxmem):
    write_note(
        validator_auxmem,
        "10-projects/dup-keys.md",
        "---\ntitle: A\nstatus: active\nstatus: done\ntype: project-doc\n"
        "summary: Concrete nouns for grep retrieval in validator fixture tests here.\n"
        "domain: projects\ncreated: 2026-07-04\nupdated: 2026-07-04\n---\n",
    )
    assert "duplicate key" in _errors(validator_auxmem, "10-projects/dup-keys.md")


def test_missing_required_field(validator_auxmem):
    write_note(
        validator_auxmem,
        "10-projects/missing.md",
        note_with_fm("Body.", **{k: v for k, v in VALID_FM.items() if k != "summary"}),
    )
    assert "missing required field" in _errors(validator_auxmem, "10-projects/missing.md")


def test_invalid_vocabulary_value(validator_auxmem):
    _write(validator_auxmem, "10-projects/bad-type.md", type="not-a-type")
    assert "not in controlled vocabulary" in _errors(validator_auxmem, "10-projects/bad-type.md")


def test_invalid_tag_field(validator_auxmem):
    _write(validator_auxmem, "10-projects/bad-tag.md", tag="solo")
    assert "use plural 'tags'" in _errors(validator_auxmem, "10-projects/bad-tag.md")


def test_tags_must_be_list(validator_auxmem):
    write_note(
        validator_auxmem,
        "10-projects/tags-scalar.md",
        note_with_fm("Body.", tags="not-a-list", **VALID_FM),
    )
    assert "tags must be a YAML list" in _errors(validator_auxmem, "10-projects/tags-scalar.md")


def test_empty_required_value(validator_auxmem):
    _write(validator_auxmem, "10-projects/empty-title.md", title="")
    assert "missing required field: title" in _errors(validator_auxmem, "10-projects/empty-title.md")


def test_impossible_date(validator_auxmem):
    write_note(
        validator_auxmem,
        "10-projects/bad-date.md",
        "---\n"
        + "\n".join(
            f"{k}: {v}" for k, v in [
                ("title", VALID_FM["title"]),
                ("summary", VALID_FM["summary"]),
                ("type", VALID_FM["type"]),
                ("status", VALID_FM["status"]),
                ("domain", VALID_FM["domain"]),
                ("created", '"2026-99-99"'),
                ("updated", VALID_FM["updated"]),
            ]
        )
        + "\n---\nBody.\n",
    )
    assert "not a valid ISO date" in _errors(validator_auxmem, "10-projects/bad-date.md")


def test_valid_iso_date(validator_auxmem):
    _write(validator_auxmem, "10-projects/good-date.md")
    assert _validate(validator_auxmem, "10-projects/good-date.md").returncode == 0


def test_summary_too_short(validator_auxmem):
    _write(validator_auxmem, "10-projects/short.md", summary="too short")
    assert "summary too short" in _errors(validator_auxmem, "10-projects/short.md")


def test_unicode_title_and_summary(validator_auxmem):
    _write(
        validator_auxmem,
        "10-projects/unicode.md",
        title="Réunion — données équipe",
        summary="Unicode résumé with enough concrete nouns for retrieval grep tests.",
    )
    assert _validate(validator_auxmem, "10-projects/unicode.md").returncode == 0


# ---------------------------------------------------------------- links


def test_valid_relative_link(validator_auxmem):
    _write(validator_auxmem, "10-projects/target.md")
    _write(
        validator_auxmem,
        "10-projects/linker.md",
        body="See [target](target.md).",
    )
    assert _validate(validator_auxmem, "10-projects/linker.md").returncode == 0


def test_broken_link(validator_auxmem):
    _write(validator_auxmem, "10-projects/broken-link.md", body="[x](missing.md)")
    assert "broken internal link" in _errors(validator_auxmem, "10-projects/broken-link.md")


def test_url_encoded_space_link(validator_auxmem):
    _write(validator_auxmem, "10-projects/my note.md")
    _write(validator_auxmem, "10-projects/encoded.md", body="[n](my%20note.md)")
    assert _validate(validator_auxmem, "10-projects/encoded.md").returncode == 0


def test_section_anchor_link(validator_auxmem):
    _write(validator_auxmem, "10-projects/anchored.md", body="## Section\n\n[x](target.md#section)")
    _write(validator_auxmem, "10-projects/target.md")
    assert _validate(validator_auxmem, "10-projects/anchored.md").returncode == 0


def test_link_escapes_root(validator_auxmem):
    _write(validator_auxmem, "10-projects/escape.md", body="[x](../../../outside.md)")
    assert "escapes auxmem root" in _errors(validator_auxmem, "10-projects/escape.md")


def test_root_relative_link(validator_auxmem):
    _write(validator_auxmem, "10-projects/rootrel.md", body="[x](/10-projects/target.md)")
    _write(validator_auxmem, "10-projects/target.md")
    assert _validate(validator_auxmem, "10-projects/rootrel.md").returncode == 0


def test_link_to_binary_asset(validator_auxmem):
    assets = validator_auxmem / "95-assets"
    assets.mkdir(exist_ok=True)
    (assets / "diagram.png").write_bytes(b"\x89PNG")
    _write(validator_auxmem, "10-projects/asset-link.md", body="![d](../95-assets/diagram.png)")
    # image syntax is not caught by INTERNAL_LINK; markdown link form:
    _write(validator_auxmem, "10-projects/asset-md-link.md", body="[d](../95-assets/diagram.png)")
    assert _validate(validator_auxmem, "10-projects/asset-md-link.md").returncode == 0


def test_skipped_directory_not_validated(validator_auxmem):
    tpl = validator_auxmem / "90-templates" / "bad.md"
    tpl.parent.mkdir(exist_ok=True)
    tpl.write_text("# no frontmatter\n")
    result = run_validator(["90-templates/bad.md"], cwd=validator_auxmem)
    assert result.returncode == 0


def test_symlink_escape_rejected(validator_auxmem):
    outside = validator_auxmem.parent / "outside-target.md"
    outside.write_text("outside\n")
    link = validator_auxmem / "10-projects" / "symlink.md"
    link.parent.mkdir(exist_ok=True)
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    _write(validator_auxmem, "10-projects/symlink-link.md", body="[x](symlink.md)")
    assert "escapes auxmem root" in _errors(validator_auxmem, "10-projects/symlink-link.md")


# ---------------------------------------------------------------- synthesis


def test_entity_without_synthesis_generated(validator_auxmem):
    _write(validator_auxmem, "85-synthesis/entity.md", type="entity")
    assert "synthesis: generated" in _errors(validator_auxmem, "85-synthesis/entity.md")


def test_synthesis_missing_sources(validator_auxmem):
    _write(
        validator_auxmem,
        "85-synthesis/no-src.md",
        type="entity",
        synthesis="generated",
        review="needed",
        generated_at="2026-07-04",
    )
    assert "must cite a non-empty" in _errors(validator_auxmem, "85-synthesis/no-src.md")


def test_synthesis_empty_sources(validator_auxmem):
    write_note(
        validator_auxmem,
        "85-synthesis/empty-src.md",
        note_with_fm(
            "Body.",
            type="entity",
            synthesis="generated",
            review="needed",
            generated_at="2026-07-04",
            sources=[],
            **{k: v for k, v in VALID_FM.items() if k not in ("type",)},
        ),
    )
    assert "must cite a non-empty" in _errors(validator_auxmem, "85-synthesis/empty-src.md")


def test_synthesis_nonexistent_source(validator_auxmem):
    _write(
        validator_auxmem,
        "85-synthesis/bad-src.md",
        type="entity",
        synthesis="generated",
        review="needed",
        generated_at="2026-07-04",
        sources=["05-sources/missing.md"],
    )
    assert "path does not resolve" in _errors(validator_auxmem, "85-synthesis/bad-src.md")


def test_synthesis_source_outside_root(validator_auxmem):
    _write(
        validator_auxmem,
        "85-synthesis/outside-src.md",
        type="entity",
        synthesis="generated",
        review="needed",
        generated_at="2026-07-04",
        sources=["../../outside.md"],
    )
    assert "escapes auxmem root" in _errors(validator_auxmem, "85-synthesis/outside-src.md")


def test_synthesis_invalid_review(validator_auxmem):
    _write(
        validator_auxmem,
        "05-sources/src.md",
        type="source",
        domain="projects",
    )
    _write(
        validator_auxmem,
        "85-synthesis/bad-review.md",
        type="entity",
        synthesis="generated",
        review="pending",
        generated_at="2026-07-04",
        sources=["05-sources/src.md"],
    )
    assert "needs review" in _errors(validator_auxmem, "85-synthesis/bad-review.md")


def test_synthesis_invalid_generated_date(validator_auxmem):
    _write(validator_auxmem, "05-sources/src.md", type="source", domain="projects")
    write_note(
        validator_auxmem,
        "85-synthesis/bad-gen.md",
        "---\n"
        + "\n".join(
            f"{k}: {v}"
            for k, v in [
                ("title", VALID_FM["title"]),
                ("summary", VALID_FM["summary"]),
                ("type", "entity"),
                ("status", VALID_FM["status"]),
                ("domain", VALID_FM["domain"]),
                ("created", VALID_FM["created"]),
                ("updated", VALID_FM["updated"]),
                ("synthesis", "generated"),
                ("review", "needed"),
                ("generated_at", '"2026-13-40"'),
                ("sources", "[05-sources/src.md]"),
            ]
        )
        + "\n---\nBody.\n",
    )
    out = _errors(validator_auxmem, "85-synthesis/bad-gen.md")
    assert "generated_at" in out or "not a valid ISO date" in out


def test_authored_note_falsely_marked_generated(validator_auxmem):
    _write(validator_auxmem, "10-projects/false-gen.md", synthesis="generated")
    assert "authored notes must not set synthesis: generated" in _errors(
        validator_auxmem, "10-projects/false-gen.md"
    )


def test_valid_synthesis_page(validator_auxmem):
    _write(validator_auxmem, "05-sources/src.md", type="source", domain="projects")
    write_note(
        validator_auxmem,
        "85-synthesis/valid.md",
        note_with_fm(
            "Synthesized body.",
            type="entity",
            synthesis="generated",
            review="needed",
            generated_at="2026-07-04",
            sources=["05-sources/src.md"],
            **{k: v for k, v in VALID_FM.items() if k not in ("type",)},
        ),
    )
    assert _validate(validator_auxmem, "85-synthesis/valid.md").returncode == 0


# ---------------------------------------------------------------- autofix


def test_autofix_body_bytes_unchanged(validator_auxmem):
    body = "Unique body marker XYZ-12345 must survive autofix.\n"
    path = _write(validator_auxmem, "10-projects/fix-body.md", body=body, updated="")
    before_body = path.read_text().split("---", 2)[2]
    run_validator(["--fix", "10-projects/fix-body.md"], cwd=validator_auxmem)
    after_body = path.read_text().split("---", 2)[2]
    assert before_body == after_body


def test_autofix_malformed_frontmatter_untouched(validator_auxmem):
    path = write_note(validator_auxmem, "10-projects/no-fix.md", "---\nbad: [\n---\nBody\n")
    before = path.read_text()
    run_validator(["--fix", "10-projects/no-fix.md"], cwd=validator_auxmem)
    assert path.read_text() == before


def test_autofix_idempotent(validator_auxmem):
    path = _write(validator_auxmem, "10-projects/idempotent.md", tag="solo", updated="")
    run_validator(["--fix", "10-projects/idempotent.md"], cwd=validator_auxmem)
    first = path.read_text()
    run_validator(["--fix", "10-projects/idempotent.md"], cwd=validator_auxmem)
    assert path.read_text() == first


def test_autofix_does_not_guess_domain(validator_auxmem):
    path = _write(validator_auxmem, "10-projects/no-guess.md", domain="not-in-vocab")
    before = path.read_text()
    run_validator(["--fix", "10-projects/no-guess.md"], cwd=validator_auxmem)
    assert path.read_text() == before


def test_autofix_normalizes_unambiguous_date(validator_auxmem):
    write_note(
        validator_auxmem,
        "10-projects/pad-date.md",
        "---\n"
        f"title: {VALID_FM['title']}\n"
        f"summary: {VALID_FM['summary']}\n"
        f"type: {VALID_FM['type']}\n"
        f"status: {VALID_FM['status']}\n"
        f"domain: {VALID_FM['domain']}\n"
        'created: "2026-7-4"\n'
        f"updated: {VALID_FM['updated']}\n"
        "---\nBody.\n",
    )
    run_validator(["--fix", "10-projects/pad-date.md"], cwd=validator_auxmem)
    assert "2026-07-04" in (validator_auxmem / "10-projects/pad-date.md").read_text()


# ---------------------------------------------------------------- JSON output


def test_json_stable_top_level_fields(validator_auxmem):
    _write(validator_auxmem, "10-projects/json-bad.md", type="not-a-type")
    result = run_validator(["--json", "10-projects/json-bad.md"], cwd=validator_auxmem)
    payload = json.loads(result.stdout)
    assert set(payload) == {"clean", "files"}
    assert payload["clean"] is False
    assert "errors" in payload["files"][0]
    assert set(payload["files"][0]["errors"][0]) == {"message", "fixable"}


def test_json_exit_code(validator_auxmem):
    good = run_validator(["--json", "--all"], cwd=validator_auxmem)
    assert good.returncode == 0
    _write(validator_auxmem, "10-projects/json-fail.md", type="bad")
    bad = run_validator(["--json", "10-projects/json-fail.md"], cwd=validator_auxmem)
    assert bad.returncode == 1


def test_json_unicode_filename(validator_auxmem):
    rel = "10-projects/unicode β.md"
    _write(validator_auxmem, rel, title="β note", type="bad-type")
    result = run_validator(["--json", rel], cwd=validator_auxmem)
    payload = json.loads(result.stdout)
    json.dumps(payload, ensure_ascii=False)
    assert payload["clean"] is False
    assert payload["files"][0]["file"].endswith("unicode β.md")


def test_json_fixable_classifications(validator_auxmem):
    _write(validator_auxmem, "10-projects/classify.md", type="bad-type", updated="")
    result = run_validator(["--json", "10-projects/classify.md"], cwd=validator_auxmem)
    payload = json.loads(result.stdout)
    tags = {e["fixable"] for e in payload["files"][0]["errors"]}
    assert "human" in tags
    assert "auto" in tags


# ---------------------------------------------------------------- path helpers / template


def test_resolves_within_root_unit():
    root = Path("/tmp/auxmem").resolve()
    assert va.resolves_within_root(root / "10-projects/note.md", root)
    assert not va.resolves_within_root(root.parent / "outside.md", root)


def test_template_notes_remain_valid(tmp_path):
    dest = tmp_path / "template-check"
    scaffold_auxmem(dest)
    result = run_validator(["--all"], cwd=dest)
    assert result.returncode == 0, result.stdout
