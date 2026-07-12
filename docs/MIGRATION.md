# Migrating from AuxMem to Koinome

Koinome replaces AuxMem as the product name. A **corpus** is the governed knowledge collection that was previously called an auxmem.

## Upgrade path

From any legacy AuxMem folder:

```bash
koinome upgrade --dry-run /path/to/corpus   # inspect planned renames
koinome upgrade /path/to/corpus             # migrate managed state and template
```

The migration:

1. Detects legacy `.auxmem/` state, config, scripts, skills, and manifests.
2. Backs up every managed file it changes.
3. Renames product-owned paths to Koinome names (for example `.koinome/`, `koinome.config.json`, `validate_corpus.py`).
4. Preserves your configuration values and user-edited managed guidance (merge policy unchanged).
5. Never rewrites ordinary user-authored notes.
6. Reports legacy command or link references found in your notes for manual review.
7. Rolls back managed state if post-migration validation fails.

## What changes on disk

| Legacy (AuxMem) | Koinome |
|---|---|
| `.auxmem/` | `.koinome/` |
| `.auxmem-manifest.json` | `.koinome-manifest.json` |
| `.scripts/auxmem.config.json` | `.scripts/koinome.config.json` |
| `.scripts/validate_corpus.py` | `.scripts/validate_corpus.py` |
| `.scripts/check_auxmem.py` | `.scripts/check_corpus.py` |
| `.skills/auxmem-*` | `.skills/koinome-*` |

User notes, Git history, and domain folders are unchanged.

## Command rename

The CLI command is now `koinome`. There is no `auxmem` shim — use `koinome upgrade` on legacy folders.
