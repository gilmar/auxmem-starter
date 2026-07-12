# Koinome starter — agent guide

This repo is the **Koinome** CLI and versioned Koinome template (`koinome/` package). It is not a corpus itself — do not run corpus validation or bootstrap here unless testing scaffold output.

**[docs/STRATEGY.md](docs/STRATEGY.md)** is the source of truth for positioning, terminology, and honest-scope rules when editing docs.

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

Examples: `feature/koinome-transform`, `fix/upgrade-config-merge`, `chore/update-agents-md`.

### Agent checklist

1. `git checkout master && git pull origin master`
2. `git checkout -b <type>/<short-description>` — **before** making changes or commits
3. Commit on the feature branch; push with `git push -u origin HEAD`
4. Open a PR to `master` — **never** commit or push to `master` directly

If you accidentally commit on `master`, move the commit to a feature branch (`git branch <name>` then `git reset --hard origin/master` on `master`) before pushing.

## Setup

```bash
uv sync --group dev   # install package + pytest, ruff, etc.
uv run koinome --help
bash scripts/check_repo.sh   # full verification (tests, lint, build, smoke)
```

Run without installing globally:

```bash
uv run python koinome-cli new --name t --path /tmp/t-test
```

## Common maintainer tasks

| task | command |
| --- | --- |
| Full repository check | `bash scripts/check_repo.sh` |
| PyPI name availability | `bash scripts/check_pypi_registry.sh` |
| Regenerate template manifest | `uv run python build_manifest.py` |
| Shell lint | `bash scripts/lint-shell.sh` |
| Full release gate | `bash scripts/check_release.sh` |
| Reference corpus evaluation | `uv run python -m koinome.evaluation` |
| Rebuild reference examples | `uv run python examples/build_references.py` |
| Bump template version | edit `koinome/version.py` (`TEMPLATE_VERSION`), then `build_manifest.py` |
| Bump conformance version | edit `koinome/version.py` (`CONFORMANCE_VERSION`), then `build_manifest.py` |
| Bump CLI version | edit `pyproject.toml` and `koinome/__init__.py` (`__version__`) — keep both in sync |

**Versioning is paused at 0.0.0.** Do not bump versions unless the user explicitly asks to resume versioning.

After template changes, regenerate `.koinome-manifest.json` before committing.

## Release (PyPI)

```bash
# bump versions in pyproject.toml, koinome/__init__.py, koinome/version.py
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

- Managed knowledge collections are **corpora**; reserve **vault** for Obsidian import sources only.
- CLI product name **Koinome CLI** appears only in `--help`, `pyproject.toml` description, and the README anchor block — elsewhere write “the `koinome` CLI”.
- Template, conformance, and CLI versions are tracked separately; see `docs/RELEASE.md` and `docs/COMPATIBILITY.md`.
- `koinome upgrade` migrates existing corpora to newer template versions.
- Keep changes focused; match existing style in surrounding files.

## Key paths

| path | purpose |
| --- | --- |
| `koinome/cli.py` | CLI entry and help |
| `koinome/template/` | versioned Koinome template |
| `koinome/paths.py` | corpus path resolution |
| `koinome/upgrade.py` | template upgrade logic |
| `build_manifest.py` | manifest generator |
| `docs/RELEASE.md` | release and version policy |
| `docs/COMPATIBILITY.md` | supported environments matrix |
| `docs/EVALUATION.md` | reference corpus and evaluation methodology |
| `docs/USAGE.md` | user-facing command reference |
