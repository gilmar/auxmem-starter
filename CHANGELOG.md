# Changelog

Template version and CLI version are tracked independently. `auxmem upgrade`
migrates existing vaults to newer template versions.

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
