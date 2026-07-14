# Compatibility matrix

Koinome support claims are limited to environments verified by the procedures below.
**Status** meanings:

| status | meaning |
| --- | --- |
| **tested** | Automated or documented smoke passed on the date shown |
| **expected** | Should work; not re-verified on every commit |
| **unsupported** | Known gaps; use at your own risk |

Do not treat a provider directory (`.claude/skills/`, etc.) as proof an agent works — run the smoke procedure.

## Reproducible smoke procedure

Deterministic checks (no agent CLI required):

```bash
bash scripts/compatibility_smoke.sh
```

This runs fresh scaffold validation, conformance check, upgrade dry-run, and wheel install smoke (including a path with spaces).

Windows Git Bash coverage (CI job `windows-bootstrap`, issue #36):

```bash
bash scripts/windows_ci_smoke.sh
```

Full release gate (maintainers, pre-publish):

```bash
bash scripts/check_release.sh
```

## Agent providers

| environment | status | OS | Python | skill-discovery path | instruction-file path | last verified | smoke procedure | known limitations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Code | expected | macOS 14+, Linux | 3.10+ (validator) | `.claude/skills/` | `CLAUDE.md`, `AGENTS.md` | 2026-07-12 | Manual: open corpus, run `koinome-init` skill, create one note | Skill discovery version-dependent; symlink vs copy per `bootstrap.sh` |
| Codex CLI | expected | macOS 14+, Linux | 3.10+ | `.codex/skills/` | `AGENTS.md` | 2026-07-12 | Manual: same as Claude with Codex pointed at corpus root | Provider CLI version not pinned in CI |
| Gemini CLI | expected | macOS 14+, Linux | 3.10+ | `.gemini/skills/` | `GEMINI.md`, `AGENTS.md` | 2026-07-12 | Manual: same with Gemini CLI | Provider CLI version not pinned in CI |
| Cursor | expected | macOS 14+, Linux | 3.10+ | `.cursor/skills/` (also reads `.claude/skills/`) | `AGENTS.md` | 2026-07-12 | Manual: open folder in Cursor, invoke a template skill | Cursor agent behavior is model-dependent |

### Agent-assisted smoke (manual, same for all providers)

1. Scaffold: `koinome new --name compat --path /tmp/compat-test`
2. Point the agent at the corpus root.
3. Run the `koinome-init` skill (or confirm pre-set domains).
4. Create one note via `koinome-new-note` skill; commit passes pre-commit hook.
5. Run `koinome doctor /tmp/compat-test` — exit 0.

Record the provider CLI version and date in this table when re-verifying.

## Host platforms

| environment | status | OS version | Python | agent version | last verified | smoke procedure | known limitations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| macOS | tested | macOS 14+ (CI: macos-latest) | 3.10, 3.12, 3.13 | n/a (deterministic) | 2026-07-12 | `bash scripts/check_repo.sh` on macOS | None for core CLI/template |
| Linux | tested | Ubuntu (CI: ubuntu-latest) | 3.10, 3.12, 3.13 | n/a | 2026-07-12 | `bash scripts/check_repo.sh` on Linux | None for core CLI/template |
| WSL2 | expected | Ubuntu on WSL2 | 3.10+ | n/a | 2026-07-12 | Keep corpus on Linux filesystem (`~/my-corpus`); run `compatibility_smoke.sh` | `/mnt/c/` paths are slow; see template `docs/SETUP.md` |
| Windows (Git Bash / PowerShell) | tested | Windows 10+ (CI: windows-latest) | 3.12 | n/a | 2026-07-14 | `bash scripts/windows_ci_smoke.sh` (CI job `windows-bootstrap`) | Native cmd.exe without bash is unsupported; shell scripts are forced LF (`eol=lf` + scaffold normalization) so Git `autocrlf` does not break `bootstrap.sh` (issue #36) |

## Package install paths

| path | status | last verified | smoke procedure |
| --- | --- | --- | --- |
| `uv sync` (dev) | tested | 2026-07-12 | `bash scripts/check_repo.sh` |
| `uv tool install` / `pipx install` | expected | 2026-07-12 | `bash scripts/smoke_install.sh` after `uv build` |
| wheel in venv | tested | 2026-07-12 | `scripts/smoke_install.sh` |
| system `pip install` without venv | unsupported | — | Bootstrap refuses to mutate system Python |

## Version coordination

| artifact | source | compatibility impact |
| --- | --- | --- |
| CLI | `pyproject.toml`, `koinome/__init__.py` | Package install and command surface |
| Template | `koinome/version.py`, manifest `template_version` | `koinome upgrade` behavior |
| Conformance | `koinome/version.py`, manifest `conformance_version` | What notes pass `validate_corpus.py` / `check_corpus.py` |

Bump conformance when validator rules change what constitutes a valid note. Document the change in `CHANGELOG.md` and re-run `bash scripts/check_release.sh` before publishing.

## PyPI history

Publish and install **`koinome`** only. See `docs/RELEASE.md` for version policy and the mistaken pre-rename index release.
