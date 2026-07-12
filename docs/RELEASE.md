# Release and version policy

Koinome is pre-release at version `0.0.0` in source. Do not publish to PyPI until integrity PRs AUX-001 through AUX-011 are complete and `bash scripts/check_release.sh` passes.

## Three coordinated versions

| version | bump when | source files |
| --- | --- | --- |
| CLI | command surface or package metadata changes | `pyproject.toml`, `koinome/__init__.py` |
| Template | corpus tooling/guidance changes users should adopt | `koinome/version.py` (`TEMPLATE_VERSION`), manifest `template_version` |
| Conformance | validator or `check_corpus` rules change valid-note contract | `koinome/version.py` (`CONFORMANCE_VERSION`), manifest `conformance_version` |

After template or conformance bumps, run `uv run python build_manifest.py` and commit `koinome/template/.koinome-manifest.json`.

## Release candidate policy

- Use an explicit prerelease tag (for example `0.1.0rc1`). Do not call the project stable or `1.0` during the hardening cycle.
- The release command refuses `0.0.0`, stable `1.0`, and versions at or below mistaken PyPI `2.0.0` (unless continuing in the `0.x` line).
- Every compatibility claim in `docs/COMPATIBILITY.md` must reference a reproducible smoke procedure.

## Release gate

```bash
# Full P0 gate (clean tree required)
bash scripts/check_release.sh

# Prepare a specific version (refuses inconsistent sources)
bash scripts/check_release.sh --target-version 0.1.0rc1
```

`check_release.sh` runs `check_repo.sh`, `python -m koinome.release_check --strict`, and `compatibility_smoke.sh`.

Local iteration with uncommitted changes:

```bash
ALLOW_DIRTY_TREE=1 bash scripts/check_release.sh
```

## Package registry

The PyPI package name is **`koinome`** (`pyproject.toml` `name`). Check registry status:

```bash
bash scripts/check_pypi_registry.sh
```

Publish **only** under `koinome`. Intentional releases use semver on that project (for example `0.0.0alpha1`, then `0.1.0rc1` or `0.1.0` after hardening).

Recommended first upload (TestPyPI, after `bash scripts/check_release.sh` passes and versions are bumped):

```bash
uv build
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-...
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ koinome
```

Production publish uses `uv publish` (see [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) in `AGENTS.md`).

## Mistaken 2.0.0 publication (pre-rename)

Before the repository reset to `0.0.0`, a mistaken `2.0.0` was published on PyPI under an **abandoned project name** from an earlier iteration. That artifact is unsupported. Yank it on the index if PyPI allows. Koinome ships only as **`koinome`** on PyPI.

Before each publish, verify resolution in a clean environment:

```bash
pip index versions koinome
pip install 'koinome>=0.1.0' --dry-run
```

**Never** publish `0.0.0` or any version lower than an existing PyPI release without verifying index resolution.

## Pre-publish checklist

- `bash scripts/check_release.sh`
- `uv run python -m koinome.evaluation`
- `docs/COMPATIBILITY.md` updated if support claims change
- `CHANGELOG.md` entry for the release version
- Confirm template manifest is fresh (`uv run python build_manifest.py`)
- Verify PyPI/TestPyPI resolution in a clean venv (`bash scripts/check_pypi_registry.sh` before first publish)
