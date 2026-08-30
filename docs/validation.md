# Validation and provenance

CGE-Core distinguishes software convenience from scientific validation.

## Hosoe Simple and Standard

The pre-v0.7 scientific baseline established benchmark reproduction for the bundled Hosoe implementations. The Standard model also carries policy-experiment regression evidence. v0.8.0 consolidates package architecture and release surfaces around those equations rather than casually rewriting them.

## CAMCGE

The CAMCGE regression material checks the published 1987 objective (`omega`), 98 reported base-equilibrium variable levels, the dropped current-account residual, and the three published policy experiments. See `CAMCGE_VALIDATION_REPORT.md` and `validation/cam/replicate_*.py`.

## IFPRI

Keep two lanes separate:

1. **Redistributable synthetic public lane** — independently authored and runnable in CI/Colab.
2. **Official-source replication lane** — requires separately supplied external source material and supports the benchmark-comparison claim.

See [IFPRI public path and clean-room boundary](ifpri_cleanroom.md).

## Release rule

An architectural refactor must not be used as a reason to loosen tolerances or silently change equations, calibration, closure, or reference targets. A future equation change must be described and validated as a scientific change.

v0.8.0 therefore treats namespace cleanup, notebook consolidation, documentation, packaging, and shared-engine refactoring as software changes around the model-specific scientific cores.
