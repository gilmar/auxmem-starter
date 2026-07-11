# AuxMem starter — agent guide

This repo is the **AuxMem** CLI and versioned auxmem template (`auxmem/` package). It is not an auxmem folder itself — do not run auxmem validation or bootstrap here unless testing scaffold output.

Use **uv** for Python environment, builds, and PyPI releases.

## Setup

```bash
uv sync          # create .venv and install the package (editable)
uv run auxmem --help
```

Run without installing globally:

```bash
uv run python auxmem-cli new --name t --path /tmp/t-test
```

## Common maintainer tasks

| task | command |
| --- | --- |
| Regenerate template manifest | `uv run python build_manifest.py` |
| Shell lint | `bash scripts/lint-shell.sh` |
| Bump template version | edit `auxmem/version.py` (`TEMPLATE_VERSION`), then `build_manifest.py` |
| Bump CLI version | edit `pyproject.toml` and `auxmem/__init__.py` (`__version__`) — keep both in sync |

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
