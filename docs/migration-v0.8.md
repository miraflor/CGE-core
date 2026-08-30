# Migrating to v0.8.0

v0.8.0 removes historical redirect modules from the active package. The
practitioner API remains unchanged: `SimpleCGE`, `StandardCGE`, `CamCGE`,
`IFPRICGE`, `CGE`, and `PyCGE` are still available from `cge_core`.

## Import-path changes

| Before v0.8 | v0.8 canonical location |
|---|---|
| `cge_core.api` | `cge_core.workflow` or top-level `cge_core` |
| `cge_core.engine` | top-level `cge_core.PyCGE` |
| `cge_core.modern_engine` | internal; use the public workflow |
| `cge_core.solvers` | `cge_core.solver` |
| `cge_core.samtools` | `cge_core.sam` |
| `cge_core.ifpri.*` | `cge_core.models.ifpri.*` |
| `cge_core.authoring.*` | `cge_core.experimental.authoring.*` |
| `cge_core.spec.*` | `cge_core.experimental.spec.*` |
| `cge_core.examples.*_model_def` | `cge_core.models.simple/standard` |
| `cam.cam_model_def` | `cge_core.models.camcge.model` |

The inherited PyCGE implementation now lives at `cge_core._pycge`; ordinary
advanced code should continue importing `PyCGE` from the package root.

## Notebook course

The active `notebooks/` directory now contains exactly seven notebooks:
`01` through `06`, plus `90_internals`. Redirect notebooks from earlier
releases are intentionally absent. Their historical contents remain available
through Git tags.

## Why the break

CGE-Core is still pre-1.0. v0.8 uses that window to establish one namespace,
one implementation location, and one course before those historical aliases
become long-term maintenance obligations.
