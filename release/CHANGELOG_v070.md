## v0.7.0 (2026) — Practitioner-first modelling system

CGE-Core v0.7.0 changes the software experience around the validated v0.6.0 scientific baseline without intentionally changing the validated economic equations.

### Practitioner API
- Add `SimpleCGE`, `StandardCGE`, `CamCGE`, and `IFPRICGE` package-root entry points.
- Add model-owned default closure for bundled Hosoe and CAMCGE models.
- Add `StandardCGE.from_sam(...)` with balance validation and explicit account-role mapping.
- Add StandardCGE semantic shock helpers: `tariff`, `production_tax`, and `endowment`.
- Add human-facing `summary()`, retained `compare()`, and advanced `raw` access.

### Scenario architecture
- New public scenarios shallow-copy engine bookkeeping and deep-copy only the calibrated concrete model: one scenario equals one independent model clone.
- Preserve benchmark/result snapshot safety and v0.6 lifecycle compatibility.

### Solver subsystem
- Add central `cge_core.solvers` resolver and `cge doctor` diagnostics.
- Ordinary public `.solve()` calls need no solver name once a supported backend is available.

### Bundled models and packaging
- Package the existing top-level `cam` implementation and data into wheels and expose `CamCGE` as first-class.
- Install the independently authored synthetic IFPRI demonstration economy.
- Keep the synthetic/official IFPRI validation boundary explicit.
- Add canonical model-family namespaces without mechanically rewriting validated equation modules.

### Model authoring
- Add function-based custom-model adapter (`model_from_module`) requiring no inheritance.
- Add explicit model metadata for closure, benchmark-only components, protected base quantities, required data, and semantic shocks.
- The v0.7 public engine no longer infers benchmark-only economic meaning from symbol spelling.

### Experimental `.cge.md`
- Add deterministic fenced-block parser, AST, semantic validation, narrow Pyomo compiler, source-located errors, `cge check`, and `cge solve`.
- Markdown prose is computationally inert.
- Syntax is explicitly experimental before 1.0 and intentionally does not clone GAMS syntax.

### Documentation and notebooks
- Replace the outward-facing path with practitioner-first tutorials.
- Public notebooks remove Git branch/bootstrap, `sys.path`, repository-root, PATH, and solver-selection plumbing.
- Retain internals as advanced material rather than prerequisite knowledge.

### Compatibility
- Preserve `CGE`, `Equilibrium`, `Scenario`, `Result`, `PyCGE`, `SplCGE`, and `StdCGE` public imports.
- Keep the v0.6 lower-level `PyCGE` path as the compatibility/advanced layer.


### Review hardening

- fixed multidimensional `.cge.md` parameter indexing and rejected ambiguous identifiers/comparison syntax early;
- made explicit empty `shockable` declarations restrictive rather than permissive;
- restored explicit CAMCGE benchmark-protection metadata;
- preserved configured IFPRI solver choice across scenarios;
- hardened functional-model mutability and comparison errors;
- made notebook bootstrap compatible with both local pre-release validation and clean Colab installs;
- added release-script preflight/`--check` behavior and deterministic line-ending-safe writes.
