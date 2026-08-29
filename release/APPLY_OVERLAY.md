# CGE-Core v0.7.0 — commit-ready release overlay

This archive is designed for the validated **v0.6.0 baseline** (`7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2`). It intentionally does **not** duplicate unchanged scientific equation files: extract it over that checkout so Git preserves the exact validated baseline and shows only the v0.7 changes.

## Apply

1. Check out the v0.6.0 baseline (or a branch based on it).
2. Extract the contents of this archive **into the repository root**, allowing the new v0.7 files to overwrite same-named files.
3. Run once:

```bash
python release/prepare_release.py --check
python release/prepare_release.py
```

The `--check` pass validates the baseline and every patch anchor without writing. The apply pass then deletes obsolete migration-era notebooks/tests, merges the v0.7 changelog/CITATION metadata while preserving history, and applies the retained-source compatibility edits. The `release/` directory is retained as auditable release tooling and provenance; remove only files you deliberately do not want to publish.

## Verify before publishing

```bash
python -m compileall -q cge_core
python docs/check_docs.py
pytest
python -m build
```

With a supported local solver available, also run the solver/validation lanes used by the existing repository and execute the seven notebooks in a clean environment.

Then review `git diff`, commit, and tag **v0.7.0**.

## Why an overlay instead of a synthetic full clone?

The release rule is to preserve the validated v0.6 equation implementations exactly unless a scientific change is intended. An overlay against the known baseline is auditable: unchanged files remain byte-for-byte the baseline; v0.7 is a focused architectural/user-experience diff.
