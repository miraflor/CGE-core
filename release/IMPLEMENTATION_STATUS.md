# v0.7.0 implementation status

This release kit is an implementation of the practitioner-first direction in the v0.7.0 detailed plan, built as an overlay on the validated v0.6.0 release commit `7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2`.

## Implemented in this kit

- package-root `SimpleCGE`, `StandardCGE`, `CamCGE`, `IFPRICGE` entry points;
- model-owned default closure for Simple/Standard/CAM;
- central solver resolver plus `cge doctor`;
- one-concrete-model clone per new public scenario;
- explicit benchmark/base protection metadata in the v0.7 contract;
- StandardCGE semantic tariff, production-tax, and endowment shocks;
- `StandardCGE.from_sam()` using the validated SAM tooling;
- first-class wheel packaging of the existing `cam` package and its data;
- installed independently authored synthetic IFPRI dataset;
- explicit synthetic-versus-official IFPRI provenance boundary;
- function-based custom Python authoring with no inheritance requirement;
- experimental `.cge.md` parser, AST, semantic validation, source-located errors, narrow Pyomo compiler, and CLI check/solve;
- practitioner-first README and Jupyter Book structure;
- seven public/advanced notebooks with infrastructure bootstrap removed;
- v0.7 structural/behavioral tests and retirement of the v0.6 prose/notebook migration tests;
- compatibility exports for `CGE`, `Equilibrium`, `Scenario`, `Result`, `PyCGE`, `SplCGE`, and `StdCGE`.

## Deliberately not rewritten

- Hosoe simple equations;
- Hosoe standard equations/calibration formulas;
- CAMCGE equations;
- IFPRI model equations;
- the existing scientific validation targets/tolerances.

The release housekeeping script only inserts metadata and centralizes solver selection in retained v0.6 modules; it does not rewrite economic equations.

## Experimental / intentionally narrow

The `.cge.md` grammar is a version-0 experiment. It currently supports the small deterministic language documented in `docs/cge_md.md` and a two-good exchange reference model. It does **not** claim that StandardCGE, CAMCGE, or IFPRI are already fully expressible in the DSL. That larger equivalence work belongs in later v0.7.x/v0.8 development after the grammar proves stable.

External data declarations in grammar 0 are provenance-bearing references; arbitrary SAM-to-symbol binding is not guessed from files or prose.

## Validation status of this generated kit

Performed in the generation environment:

- Python syntax compilation of all new Python files;
- JSON validity of all seven notebooks;
- notebook forbidden-bootstrap scan;
- `.cge.md` parsing, semantic validation, and prose-inertness check;
- TOML parsing and packaging-manifest checks;
- static preflight checks for the release housekeeping/source transformation script;
- independent review reproduction and hardening for `.cge.md`, functional authoring, IFPRI solver propagation, CAM metadata, notebooks, and release preparation.

Not performed in the generation environment because Pyomo/IPOPT are not installed there:

- actual nonlinear benchmark solves;
- v0.6 numerical regression suite;
- CAMCGE published-target regression;
- IFPRI synthetic solver lane;
- wheel installation/solver smoke tests;
- executed-notebook numerical validation.

Those checks remain mandatory before tagging/publishing. The kit intentionally does not claim a numerical release certification it has not run.


## Independent review hardening (29 August 2026)

The release kit was revised after an adversarial review. Reproduced defects were fixed, the exact v0.6 baseline was checked for the scenario-clone and SAM concerns, and `prepare_release.py` was redesigned to preflight before mutation and support a no-write `--check` mode. Numerical benchmark certification is still intentionally deferred to the real merged repository with Pyomo/IPOPT.
