# Release and version policy

AuxMem is pre-release at version `0.0.0` in source. Do not publish to PyPI until integrity PRs AUX-001 through AUX-011 are complete and `bash scripts/check_repo.sh` passes.

## Mistaken 2.0.0 publication

The package index previously received a mistaken `2.0.0` release before the repository reset source versions to `0.0.0`.

Before the first intentional public release, choose one strategy and verify it:

### Option A — Yank mistaken release (recommended if index allows)

1. Yank `auxmem==2.0.0` on PyPI (and TestPyPI if applicable).
2. Publish the first intentional release as `0.1.0` or `1.0.0` after hardening is complete.
3. Verify resolution:

```bash
pip index versions auxmem
pip install 'auxmem>=0.1.0' --dry-run
```

### Option B — Continue above 2.0.0

1. Bump to `2.0.1` or `2.1.0` in `pyproject.toml`, `auxmem/__init__.py`, and `auxmem/version.py` together.
2. Verify `pip install auxmem` resolves to the new version, not the mistaken `2.0.0` artifact.

**Never** publish `0.0.0` or any version lower than an existing PyPI release without verifying index resolution in a clean environment.

## Pre-publish checklist

- `bash scripts/check_repo.sh`
- `bash scripts/smoke_install.sh` (wheel install + `auxmem new`)
- Confirm template manifest is fresh (`uv run python build_manifest.py`)
- Run `tests/test_release_policy.py`
