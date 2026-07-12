# Koinome starter — agent guide

This repo is the **Koinome** CLI and versioned Koinome template (`koinome/` package). It is not a corpus itself — do not run corpus validation or bootstrap here unless testing scaffold output.

Use **uv** for Python environment, builds, and PyPI releases.

## Setup

```bash
uv sync --group dev
uv run koinome --help
```

Run without installing globally:

```bash
uv run python koinome-cli new --name t --path /tmp/t-test
```

## Common maintainer tasks

| task | command |
| --- | --- |
| Regenerate template manifest | `uv run python build_manifest.py` |
| Shell lint | `bash scripts/lint-shell.sh` |
| Bump template version | edit `koinome/version.py` (`TEMPLATE_VERSION`), then `build_manifest.py` |
| Bump CLI version | edit `pyproject.toml` and `koinome/__init__.py` (`__version__`) — keep both in sync |

After template changes, regenerate `.koinome-manifest.json` before committing.

## Release (PyPI)

```bash
# bump versions in pyproject.toml, koinome/__init__.py, koinome/version.py
uv run python build_manifest.py
uv build
uv publish --token pypi-<token> # or: UV_PUBLISH_TOKEN=pypi-... uv publish
```

## Conventions

- Managed knowledge collections are **corpora**; reserve **vault** for Obsidian import sources only.
- CLI product name **Koinome CLI** appears only in `--help`, `pyproject.toml` description, and the README anchor block — elsewhere write “the `koinome` CLI”.
- Template and CLI versions are tracked separately; `koinome upgrade` migrates existing corpora to newer template versions.
- Keep changes focused; match existing style in surrounding files.

## Key paths

| path | purpose |
| --- | --- |
| `koinome/cli.py` | CLI entry and help |
| `koinome/template/` | versioned Koinome template |
| `koinome/paths.py` | corpus path resolution and legacy Koinome migration |
| `koinome/upgrade.py` | template upgrade logic |
| `build_manifest.py` | manifest generator |
| `docs/USAGE.md` | user-facing command reference |
