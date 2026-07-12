# Changelog

## How to read this file

AuxMem tracks **three coordinated versions**:

| version | where | meaning |
| --- | --- | --- |
| **CLI** | `pyproject.toml`, `auxmem/__init__.py` | AuxMem Manager package (PyPI) |
| **Template** | `auxmem/version.py`, manifest `template_version` | Auxmem folder tooling/guidance (`auxmem upgrade`) |
| **Conformance** | `auxmem/version.py`, manifest `conformance_version` | Validator and `check_auxmem` contract |

A template or conformance change that alters what constitutes a valid note is **compatibility-relevant**. See `docs/COMPATIBILITY.md`.

Versioning is **paused at 0.0.0** during the reliability hardening cycle (AUX-001–AUX-011). The first intentional public release will use an explicit **prerelease** designation (for example `0.1.0rc1`), not `1.0`.

## Accidental / unsupported index releases

### PyPI 2.0.0 (mistaken — do not use)

Published in error before the repository reset source versions to `0.0.0`. Not a supported release. See `docs/RELEASE.md` for yank or supersede strategy before publishing.

## Unreleased — hardening cycle (CLI 0.0.0, template 0.0.0, conformance 0.0.0)

Reliability and release-hardening work on `master` after the version reset:

- Validator and git gates (staged snapshot, exit codes, conformance check)
- Sync integrity (quarantine branches, per-repo lock)
- Config as canonical authority in agent guidance
- Transactional upgrade with manifest verification
- Atomic Obsidian import
- Bootstrap/packaging safety (no system Python mutation, skill refresh, wheel coverage)
- Release and compatibility discipline (AUX-011)
- Reference auxmems and deterministic evaluation harness (AUX-012)

Verify with `bash scripts/check_release.sh` before any publish.

## Historical development (pre-hardening reset)

The entries below describe early development **before** the `0.0.0` pause. They are archived context, not supported releases under current governance. Template and CLI version numbers in these sections do not match current source.

### 1.3.1 — portable shell scripts (template)

- Fix pre-commit hook on macOS bash 3.2: replace `mapfile` with a NUL-delimited read loop.
- Make `auxmem-sync.sh` portable: drop Linux-only `flock`, replace GNU `date -Iseconds`.
- Document bash 3.2 / POSIX baseline; re-run `./bootstrap.sh` after upgrade to refresh the hook.
- Add `scripts/lint-shell.sh` and CI shellcheck workflow.

### 1.3.0 — setup-domains skill (template)

- New `setup-domains` skill: interview, propose domains, update config and folders, regenerate MOCs, validate, commit.
- AGENTS.md points new auxmems at `setup-domains` first.

### 1.2.0 — agent skills (template)

- Provider-agnostic Agent Skills in `.skills/` (session close, validation fix, synthesis, new note, ADR, todo, weekly review, seed distillation).
- `bootstrap.sh` links skills into `.claude/skills`, `.codex/skills`, `.gemini/skills`, and `.cursor/skills/`.
- `skip_dirs` extended so skill directories are excluded from validation and MOC generation.

### 1.2.1 — CLI help clarity (CLI)

- Print usage instead of an error when `auxmem` is invoked with no subcommand.
- Clarify in help text which commands run outside an auxmem versus which take an auxmem path.

### 1.2.0 — domain bootstrap skill (CLI)

- Simplify `auxmem new` wizard to three steps (name, location, review); no preset domains.
- Add `setup-domains` agent skill for tailoring subject folders after creation.

### 1.1.0 — guided auxmem creation (CLI)

- Rework `auxmem new` interactive wizard: plain-language steps, domain preset, creation preview, live bootstrap progress, agent-oriented next steps.

### 1.0.1 — packaging fix (CLI)

- Ship `template/` and `importers/` inside the installed package so `uv tool install` and `pip install` can run `auxmem new`, `auxmem upgrade`, and `auxmem seed`.
- Remove stray root-level `done.txt` from the template (tasks live in `72-tasks/`).

### 1.0.0 — initial public experiment (CLI + template)

Early public experiment before governance hardening:

- `auxmem new`, `auxmem seed`, `auxmem import-obsidian`, `auxmem doctor`, `auxmem upgrade`
- Governed auxmem: config-driven validator, pre-commit hook, generated MOCs, git sync with conflict quarantine
- Synthesis layer with provenance and staleness detection
