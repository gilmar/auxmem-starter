# Release and version policy

AuxMem is pre-release at version `0.0.0` in source. Do not publish to PyPI until integrity PRs AUX-001 through AUX-011 are complete and `bash scripts/check_release.sh` passes.

## Three coordinated versions

| version | bump when | source files |
| --- | --- | --- |
| CLI | command surface or package metadata changes | `pyproject.toml`, `auxmem/__init__.py` |
| Template | auxmem tooling/guidance changes users should adopt | `auxmem/version.py` (`TEMPLATE_VERSION`), manifest `template_version` |
| Conformance | validator or `check_auxmem` rules change valid-note contract | `auxmem/version.py` (`CONFORMANCE_VERSION`), manifest `conformance_version` |

After template or conformance bumps, run `uv run python build_manifest.py` and commit `auxmem/template/.auxmem-manifest.json`.

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

`check_release.sh` runs `check_repo.sh`, `python -m auxmem.release_check --strict`, and `compatibility_smoke.sh`.

Local iteration with uncommitted changes:

```bash
ALLOW_DIRTY_TREE=1 bash scripts/check_release.sh
```

## Mistaken 2.0.0 publication

The package index previously received a mistaken `2.0.0` release before the repository reset source versions to `0.0.0`.

Before the first intentional public release, choose one strategy and verify it:

### Option A — Yank mistaken release (recommended if index allows)

1. Yank `auxmem==2.0.0` on PyPI (and TestPyPI if applicable).
2. Publish the first intentional release as `0.1.0rc1` or `0.1.0` after hardening is complete.
3. Verify resolution:

```bash
pip index versions auxmem
pip install 'auxmem>=0.1.0' --dry-run
```

### Option B — Continue above 2.0.0

1. Bump to `2.0.1` or `2.1.0` in `pyproject.toml`, `auxmem/__init__.py`, and template/conformance versions together.
2. Verify `pip install auxmem` resolves to the new version, not the mistaken `2.0.0` artifact.

**Never** publish `0.0.0` or any version lower than an existing PyPI release without verifying index resolution in a clean environment.

## Pre-publish checklist

- `bash scripts/check_release.sh`
- `uv run python -m auxmem.evaluation`
- `docs/COMPATIBILITY.md` updated if support claims change
- `CHANGELOG.md` entry for the release version
- Confirm template manifest is fresh (`uv run python build_manifest.py`)
- Verify PyPI/TestPyPI resolution in a clean venv
