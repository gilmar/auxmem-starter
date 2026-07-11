# Changelog

Template version and CLI version are tracked independently. `auxmem upgrade`
migrates existing auxmems to newer template versions.

## 0.1.0 - AuxMem product rename (pre-alpha)

CLI 0.1.0. Template 0.1.0.

- Project renamed from auxmem-starter to **AuxMem**; PyPI package `auxmem`.
- Managed folders are **auxmems** (not vaults); internal files renamed (`auxmem.config.json`, `validate_auxmem.py`, `auxmem-sync.sh`, …).
- `auxmem upgrade` migrates 1.x folders: renames legacy files, reports timer reinstall steps.
- Obsidian import sources still called vaults.

## 1.2.1 - CLI help clarity

CLI 1.2.1.

- Print usage instead of an error when `auxmem` is invoked with no subcommand.
- Clarify in help text which commands run outside an auxmem versus which take an auxmem path.

## 1.2.0 - domain bootstrap skill

CLI 1.2.0.

- Simplify `auxmem new` wizard to three steps (name, location, review); no preset domains.
- Add `setup-domains` agent skill for tailoring subject folders after creation.

## 1.3.1 - portable shell scripts

Template 1.3.1.

- Fix pre-commit hook on macOS bash 3.2: replace `mapfile` with a NUL-delimited read loop.
- Make `auxmem-sync.sh` portable: drop Linux-only `flock`, replace GNU `date -Iseconds`.
- Document bash 3.2 / POSIX baseline; re-run `./bootstrap.sh` after upgrade to refresh the hook.
- Add `scripts/lint-shell.sh` and CI shellcheck workflow.

## 1.3.0 - setup-domains skill

Template 1.3.0.

- New `setup-domains` skill: interview, propose domains, update config and folders, regenerate MOCs, validate, commit.
- AGENTS.md points new vaults at `setup-domains` first.

## 1.1.0 - guided vault creation

CLI 1.1.0.

- Rework `auxmem new` interactive wizard: plain-language steps, domain preset, creation preview, live bootstrap progress, agent-oriented next steps.

## 1.0.1 - packaging fix

CLI 1.0.1.

- Ship `template/` and `importers/` inside the installed package so `uv tool install` and `pip install` can run `auxmem new`, `auxmem upgrade`, and `auxmem seed`.
- Remove stray root-level `done.txt` from the template (tasks live in `72-tasks/`).

## 1.2.0 - agent skills

Template 1.2.0.

- Provider-agnostic Agent Skills in `.skills/` (session close, validation fix, synthesis, new note, ADR, todo, weekly review, seed distillation).
- `bootstrap.sh` links skills into `.claude/skills`, `.codex/skills`, `.gemini/skills`, and `.cursor/skills/`.
- `skip_dirs` extended so skill directories are excluded from vault validation and MOC generation.

## 1.0.0 - initial public release

Template 1.0.0. CLI 1.0.0.

- `auxmem new`: create a vault via interactive wizard or flags, from a versioned template.
- `auxmem seed`: normalize Claude, ChatGPT, and Gemini exports into a staging corpus, hardened against branch selection, multimodal parts, title escaping, and collisions.
- `auxmem import-obsidian`: import an existing Obsidian vault, pipeline or single-script.
- `auxmem doctor`: validate a vault and refresh its maps of content.
- `auxmem upgrade`: migrate a vault to the current template version with per-file policies (overwrite tooling, structured-merge config, 3-way-merge guidance) and a backup, never touching your notes.
- Governed vault: config-driven validator, pre-commit hook, generated maps of content, transparent git sync with conflict quarantine.
- Synthesis layer: raw sources versus derived entity and concept pages, with enforced provenance, review gating, and deterministic staleness detection.
- Graph and gap report: deterministic hubs, orphans, backlinks, co-citation, and structural gaps, no model and no database.
- Tiered fix workflow: deterministic auto-fix, agent-assisted drafting, and human decision, so a strict gate stays ergonomic.
