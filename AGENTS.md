# AuxMem starter — agent guide

This repo is the **AuxMem** CLI and versioned auxmem template (`auxmem/` package). It is not an auxmem folder itself — do not run auxmem validation or bootstrap here unless testing scaffold output.

Use **uv** for Python environment, builds, and PyPI releases.

## Git workflow

**Never commit or push directly to `master`.** All work starts from an up-to-date `master`, on a short-lived branch, merged via pull request.

### Branch naming ([Conventional Branch](https://conventionalbranch.org/))

Format: `<type>/<description>` — lowercase, hyphens between words, no spaces or underscores.

| prefix | use for |
| --- | --- |
| `feature/` or `feat/` | new functionality |
| `bugfix/` or `fix/` | bug fixes |
| `hotfix/` | urgent production fixes |
| `release/` | release prep (e.g. `release/v0.2.0`) |
| `chore/` | docs, deps, tooling, housekeeping |
| `cursor/` | branches created by Cursor agents |

Examples: `feature/add-import-flag`, `fix/upgrade-config-merge`, `chore/update-agents-md`, `cursor/logo-banner-refresh`.

### Agent checklist

1. `git checkout master && git pull origin master`
2. `git checkout -b <type>/<short-description>`
3. Commit; push the branch (`git push -u origin HEAD`)
4. Open a PR to `master` — do not push to `master`

## Setup

```bash
uv sync --group dev   # install package + pytest, ruff, etc.
uv run auxmem --help
bash scripts/check_repo.sh   # full verification (tests, lint, build, smoke)
```

Run without installing globally:

```bash
uv run python auxmem-cli new --name t --path /tmp/t-test
```

## Common maintainer tasks

| task | command |
| --- | --- |
| Full repository check | `bash scripts/check_repo.sh` |
| Regenerate template manifest | `uv run python build_manifest.py` |
| Shell lint | `bash scripts/lint-shell.sh` |
| Bump template version | edit `auxmem/version.py` (`TEMPLATE_VERSION`), then `build_manifest.py` |
| Bump CLI version | edit `pyproject.toml` and `auxmem/__init__.py` (`__version__`) — keep both in sync |

**Versioning is paused at 0.0.0.** Do not bump versions unless the user explicitly asks to resume versioning.

After template changes, regenerate `.auxmem-manifest.json` before committing.

## Release (PyPI)

```bash
# bump versions in pyproject.toml, auxmem/__init__.py, auxmem/version.py
uv run python build_manifest.py
uv build
uv publish --token pypi-<token>    # or: UV_PUBLISH_TOKEN=pypi-... uv publish
```

Test on TestPyPI first when unsure:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-...
```

For CI, prefer [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) with `uv publish` (no long-lived token).

## Conventions

- Managed folders are **auxmems**; reserve **vault** for Obsidian import sources only.
- CLI product name **AuxMem Manager** appears only in `--help`, `pyproject.toml` description, and the README anchor block — elsewhere write “the `auxmem` CLI”.
- Template and CLI versions are tracked separately; `auxmem upgrade` migrates existing auxmems to newer template versions.
- Keep changes focused; match existing style in surrounding files.

## Key paths

| path | purpose |
| --- | --- |
| `auxmem/cli.py` | CLI entry and help |
| `auxmem/template/` | versioned auxmem template |
| `auxmem/paths.py` | legacy 1.x file rename map |
| `auxmem/upgrade.py` | template upgrade logic |
| `build_manifest.py` | manifest generator |
| `docs/USAGE.md` | user-facing command reference |
