# Changelog

## v0.7.0 (2026) — Practitioner-first modelling architecture

CGE-Core 0.7.0 makes the ordinary workflow about economics rather than repository, solver, and framework setup while preserving the model-specific scientific implementations and validation boundaries.

### Practitioner API

- Add `SimpleCGE`, `StandardCGE`, `CamCGE`, and `IFPRICGE` model façades.
- Let bundled models declare their canonical closure so a first solve does not require users to manually name the numeraire and redundant equation.
- Add semantic Standard-CGE helpers for tariffs, production taxes and factor endowments.
- Keep advanced generic component changes available through `Scenario.set()`.
- Keep benchmark and sibling scenarios isolated; solved results remain numerical snapshots.

### Data and model access

- Add `StandardCGE.from_sam()` so a balanced SAM can be supplied as one file with explicit economic account roles.
- Package CAMCGE as a first-class installed model while preserving its own closure and published replication targets.
- Add an independently authored, redistributable synthetic IFPRI-format economy for public CI, notebooks and tutorials.
- Preserve the separate official-source IFPRI replication lane and its external-data boundary.

### Solver and user experience

- Add centralized solver discovery and `install_solver()` / `cge install-solver` helpers for the practitioner path.
- Replace infrastructure-heavy Colab material with canonical notebooks that contain one installation cell and no Git checkout/reset, repository `chdir`, `sys.path`, PATH injection or solver-name plumbing.
- Retain earlier notebook filenames only as clean redirect notebooks so old links do not strand users.
- Replace the Control Room code generator with v0.7.0 practitioner-API code.

### Learning and documentation

The canonical notebook path is:

1. `01_first_cge.ipynb`
2. `02_policy_experiments.ipynb`
3. `03_your_own_sam.ipynb`
4. `04_camcge.ipynb`
5. `05_ifpri.ipynb`
6. `06_build_a_model.ipynb`
7. `90_internals.ipynb`

Documentation is reorganized around first solve, policy experiments, SAM use, model choice, IFPRI clean-room boundaries, model authoring, validation, and advanced internals.

### Authoring

- Add function-based custom-model authoring without requiring inheritance from a CGE-Core class.
- Add an experimental deterministic `.cge.md` syntax in which only fenced `cge` blocks are executable and Markdown prose is inert.

### Scientific scope

v0.7.0 is principally an architecture, packaging and usability release. It does not claim a new economic model merely because the public API changed. Hosoe, CAMCGE and IFPRI retain distinct equations, closures, provenance and validation evidence.

---

## Earlier releases

Detailed historical changelog text remains preserved in the repository tags for the releases below.

### v0.6.0 — Public scientific API and isolated scenario workflow

Introduced the `CGE → Equilibrium → Scenario → Result` lifecycle for the Hosoe models, isolated scenario state, immutable result snapshots, stable comparison semantics, outward-facing API migration, and a protected downstream interface while retaining `PyCGE` as the lower-level compatibility path.

### v0.5.0 — CAMCGE benchmark and adversarial-review hardening

Added the published Cameroon CAMCGE replication benchmark and three policy experiments, strengthened solver probing, packaging/CI metadata, validation documentation, and correctness linting.

### v0.4.0 — IFPRI Standard CGE replication

Added the independent Python/Pyomo IFPRI Standard CGE implementation, recorded BASE and five policy scenarios, reporting/validation machinery, official-source comparison targets, and an independently authored public synthetic IFPRI-format economy with an explicit clean-room boundary.

### v0.3.0 — Programmatic API, generic SAMs and project hardening

Moved engine misuse to typed exceptions, logging-based progress, DataFrame comparisons, generic SAM tooling and stronger benchmark/shock/closure validation.

### v0.2.3 — Documentation harmonization

Reworked model and engine documentation in an equation-oriented scientific style, added crosswalks, attribution and code-hygiene improvements without changing numerical behavior.

### v0.2.2 — Correctness hardening

Strengthened SAM validation, transactional redundant-equation handling, solver-state integrity, reversible shocks, persistence, comparison/export behavior and package data paths.

### v0.2.1 — Packaging, robustness and test coverage

Migrated packaging to `pyproject.toml`, fixed comparison/objective-sign and guard-state defects, cleaned dependencies, expanded tests and added multi-lane CI.

### v0.2.0 — CGE-Core fork of PyCGE

Renamed the fork, corrected the local-IPOPT degrees-of-freedom/Walras-law workflow, fixed silent comparison/export defects, replaced NumPy expression products with Pyomo-native products, and established the first regression suite against the Hosoe reference model.
