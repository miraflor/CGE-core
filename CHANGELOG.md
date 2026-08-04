# Changelog

## v0.4.0 (2026) — IFPRI Standard CGE replication

CGE-Core now includes a separate, independently written Python/Pyomo
implementation of the IFPRI Standard CGE test economy. This is a bounded
replication claim: it covers the recorded test benchmark and five policy
simulations, not every IFPRI database, country application, closure, or later
model variant.

### IFPRI data, calibration, and model

- Parse a separately supplied `test.dat` without copying or packaging the
  official IFPRI source files.
- Validate declared sets, SAM dimensions and balance, calibration-input
  coverage and ranges, home-consumption shares, factor quantities, and tax
  mappings.
- Reconstruct normalized benchmark prices, quantities, production and trade
  parameters, institutions, LES demand, taxes, savings-investment aggregates,
  and price indices algebraically before building a solver model.
- Build the initialized Pyomo equilibrium system and validate every active
  benchmark equation before numerical solution.

### Closures, policy simulations, and replication

- Implement the recorded BASE closure and five counterfactuals: `TARCUT1`,
  `TARCUT2`, `FSAVINCR`, `PWMINCR`, and `DEVAL`.
- Solve BASE and scenarios with IPOPT or cyipopt, require optimal or locally
  optimal termination, and report degrees of freedom and maximum equation
  residuals.
- Compare the Python results with full-precision external GAMS MCP/PATH and
  NLP/CONOPT targets. BASE and all five policy simulations reproduce the
  recorded NLP results to numerical solver tolerance.

### Public testing and clean-room boundary

- Add an independently authored, redistributable synthetic IFPRI-format
  economy covering traded, pure-import, and pure-export commodities, tariffs,
  foreign saving, calibration, closures, shocks, reporting, and real IPOPT
  solves.
- Mark official-data tests as `external_ifpri` and public synthetic tests as
  `public_ifpri`, preventing unavailable external data from being mistaken for
  a successful public replication run.
- Keep the official IFPRI source package and `test.dat` outside the repository
  and package artifacts. Only independently written Python code, synthetic
  inputs, reporting helpers, and numerical validation targets are committed.

### Reporting, documentation, and hardening

- Add long-form pandas extraction, BASE-versus-scenario comparison tables,
  multi-scenario summaries, percentage changes, and structured solver
  diagnostics.
- Add a complete IFPRI documentation chapter covering setup, calibration,
  solving, scenarios, reporting, validation, and the clean-room boundary.
- Reject merely feasible solver termination, normalize solver exceptions,
  calculate equality and inequality violations correctly, and strengthen
  validation of numeric tolerances and economic input ranges.
- Expand CI across Python 3.9–3.14 with a dedicated real-IPOPT public solver
  lane, clean wheel installation, package-content checks, and warning-free
  documentation builds.

### Validation completed

- 83 complete IFPRI tests passed locally using the external test data.
- 126 public tests passed with 47 external tests explicitly deselected.
- 173 full project tests passed locally.
- GitHub Actions passed structural tests on Python 3.9–3.14, public IPOPT
  solver coverage, packaging, and documentation.

## v0.3.0 (2026) — programmatic API, generic SAMs, PSL compliance

The model equations are untouched — the base equilibrium still reproduces
the SAM exactly (`Z = (73, 72)`, `Xp = (20, 30)`, `M = (13, 11)`,
`E = (8, 4)`) and both bundled experiments give identical results
(tariff abolition EV = +1.1450; production-tax abolition EV = +4.8840) —
but the engine's *interface* changes deliberately. Suite: 86 test functions
across five modules; CI includes a real-IPOPT lane that fails if any test is
skipped.

### Final audit hardening

- SAM balance tolerance is now relative to each account, so a very large
  account cannot hide a material imbalance in a small account.
- Walras-law removal is restricted to model-declared market-clearing
  equations; an arbitrary behavioural equation can no longer be dropped just
  because doing so happens to produce zero degrees of freedom.
- Benchmark-only SAM/`*0` edits are blocked on SIM as well as BASE, preventing
  silent no-op shocks; factor endowments remain legitimate SIM shocks.
- Shock values must be finite numeric scalars. Failed edits restore the prior
  value, fixed state, and undo history transactionally.
- The chosen numeraire is tracked, persisted, and cannot be accidentally
  unfixed through the modification API; bundled models also reject quantity
  and accounting variables as economically invalid numeraires.
- Solver execution exceptions are normalized to `SolveError`, and comparison
  solved-state labels use success flags rather than the mere presence of
  diagnostic result objects.
- Bundled model definitions now declare their required dataset files, so an
  incomplete data directory fails early with a precise validation error.
- Goods, factor, institutional, and full-account sets are cross-checked against
  the SAM, and typo/stale CSVs targeting unknown model components are rejected
  rather than loaded ambiguously.

### Breaking: exceptions instead of print-and-return-None

Misuse now raises typed exceptions whose messages carry the guidance the
old guards printed:

- `WorkflowError` — methods called out of order ("Call `model_calibrate`
  first").
- `ComponentError` — unknown component or index, immutable parameter,
  protected calibration input, undo with no stored original.
- `DataValidationError` — missing/invalid data directory (previously
  print + `None`), in addition to its existing SAM-validation role.
- `SolveError` — unchanged.
- Out-of-bounds shock values raise `ValueError` (previously printed).

Rationale: a printed message and a `None` return cannot be handled by
calling code, so scripted pipelines silently marched on after failed
steps. Every guard's exception type and message is pinned by a test.

### Breaking: logging instead of stdout chatter

Progress reporting moved to the standard `logging` module (`cge_core`
logger). Nothing is written to stdout except displays explicitly
requested (`model_compare('print')`, `model_postprocess(..., 'print')`);
a test asserts the happy path is print-free. The bundled examples call
`logging.basicConfig(level=logging.INFO)` so their console behaviour is
unchanged.

### Breaking: `model_compare` returns a pandas DataFrame

One row per variable element (`component`, `index_1..N`, `base_value`,
`sim_value`, `difference`, `pct_change`), with the objective comparison
in `frame.attrs['objective']` and the solved-state note in
`frame.attrs['solved']`. `verbose` is now optional: `None` just returns
the frame, `'print'` prints it, a path writes **`compared.csv`** (the
file gains its extension). Sign conventions are unchanged and remain
pinned by tests. `model_postprocess('params')` now returns a dict of
parameter values instead of printing them. pandas becomes a hard
dependency.

### New: load any standard-structure SAM without editing model code

- **`cge_core.samtools`** builds a loadable data directory from a single
  SAM CSV: the user names the factor and institutional accounts, every
  remaining account is a good, and `set-i-.csv`/`set-h-.csv`/`set-u-.csv`
  are derived and written next to a validated copy of the SAM.
- **`StdModelDef(accounts=...)` / `SplModelDef(accounts=...)`** relabel
  the institutional accounts the equations read (`hoh`, `gov`, `inv`,
  `ext`, `idt`, `trf`), so a SAM using e.g. `HH`/`GOVT`/`ROW` loads
  as-is. The test suite verifies that a fully relabelled SAM calibrates
  to the *identical* equilibrium — the strongest available check that the
  mapping reaches every equation.

### New: PSL-style project scaffolding

- Jupyter Book documentation under `docs/` (intro, workflow, the model
  reference, and the OG-Core crosswalk as chapters); builds cleanly, and
  a new CI `docs` job keeps it building.
- `CODE_OF_CONDUCT.md` (Contributor Covenant by reference),
  `GOVERNANCE.md`, and `CONTRIBUTING.md`.

### Consistency

- `splcge`'s `sam` parameter is now immutable, matching `stdcge`;
  benchmark data was already protected from in-place edits by the
  engine, so this closes a loophole rather than changing behaviour.
- Model-definition load messages moved to the same logger.


## v0.2.3 (2026) — OG-Core-style documentation harmonization

No changes to model equations, workflow logic, or numerical behaviour: the
full 55-test suite (including all solver tests under real IPOPT) passes
unchanged, and the base equilibrium still reproduces the SAM exactly
(`Z = (73, 72)`, `Xp = (20, 30)`, `M = (13, 11)`, `E = (8, 4)`).

### Documentation

- **Model definitions rewritten in OG-Core house style** (DeBacker & Evans,
  PSLmodels/OG-Core). Every calibration initializer and constraint rule in
  `stdcge_model_def.py` and `splcge_model_def.py` now carries a NumPy-style
  docstring with the relationship stated in a `.. math::` block, Args/Returns
  sections, and the corresponding GAMS equation name (`stdcge.gms` SEQ=276 /
  `splcge.gms` SEQ=275) so every line can be diffed against the reference.
- **`docs/OG_CORE_CROSSWALK.md` is new**: a concept-, file-, and
  workflow-level mapping from OG-Core conventions to CGE-Core, including why
  Walras' law surfaces here as a degrees-of-freedom problem when OG-Core's
  fixed-point construction absorbs it.
- **Engine docstrings harmonized.** `PyCGE` and its public methods
  (`model_instance`, `model_drop_redundant`, `model_sim`,
  `model_modify_base/sim`, `model_calibrate`, `model_solve`,
  `model_compare`, `model_data`) now document Args/Returns/Raises in the
  same convention, with cross-references to the OG-Core analogues.

### Attribution

- README gains an **Authorship** section; `CITATION.cff` added with
  machine-readable metadata. Both state explicitly that the fork is
  maintained by James Matthew Miraflor, that its revisions were produced
  through an AI-assisted ("vibecoded") workflow he directed and reviewed,
  and that **the underlying model port is not his original work** (it is
  Burtwistle & Fung, NIST 2017, public domain; the model is Hosoe et al.
  2010). The same provenance block heads both model-definition modules and
  the engine.

### Code hygiene (no behavioural change)

- `from pyomo.environ import *` replaced with explicit imports in both
  model-definition modules.
- Tax-revenue variables' zero lower bounds and the numerical lower-bound
  constants are now explained where they are declared.


## v0.2.2 (2026) — correctness hardening

- Corrected the bundled simple-model SAM and removed its duplicate data folder.
- Added structural SAM validation before Pyomo model construction.
- Failed or infeasible solves no longer set calibrated/solved flags; they raise `SolveError`.
- Made redundant-equation removal transactional, constraint-only, single-equation, and DOF-checked.
- Restored explicit numerical lower bounds from the reference models.
- Made simulation/base edits reversible, preserving original values and fixed status across repeated shocks.
- Blocked in-place changes to benchmark calibration inputs that would leave derived parameters stale.
- Centralized state invalidation so old simulations/results cannot survive a rebuilt or modified base.
- Replaced malformed tuple-index exports with valid multidimensional CSV and added structured comparison records.
- Added installation-independent `example_data()` paths and optional local solver auto-detection.
- Persistence now stores solved state and results, while retaining compatibility with v0.2.1 raw dill files.
- Expanded the regression suite to 55 tests across four modules.

## v0.2.1 (2026) — packaging, robustness, and test coverage

Follow-up to the v0.2.0 fork. No changes to the model equations; the base
equilibrium and all published results are unchanged.

### Bug fixes

- **[Significant] Objective difference used the wrong sign.** `model_compare`
  reported per-variable differences as `sim - base` but the objective
  difference as `base - sim`. A welfare *gain* therefore printed as a negative
  number, contradicting the variable columns immediately above it. The
  objective now follows the same sim-minus-base convention as everything else.

- **[Significant] Guard clauses were unreachable.** `__init__` never
  initialised `self.base`, `self.sim`, `self.data`, `self.base_results`, or
  `self.sim_results`, so calling any method out of order raised a bare
  `AttributeError` from inside the engine instead of the intended message.
  Most visibly, `model_drop_redundant` resolved `self.base` *before* its
  `try` block, making its "You must create the BASE instance first" branch
  dead code. All state is now initialised in `__init__` and every guard is
  reachable and tested.

- **[Significant] Undeclared hard dependency on pandas.** `engine.py` imported
  `pandas` and `numpy` at module level. Neither was used anywhere in the file,
  and neither was declared as a dependency, so a clean install per the
  project's own metadata failed at `import cge_core`. Both imports removed,
  along with the unused `SolverResults` and `importlib` imports.

- **[Minor] Bare `except:` clauses masked real errors.** Five of them, most
  consequentially in `model_instance`, where any failure while fixing the
  numeraire printed "index does not exist" *and* skipped the
  `base_calibrated` assignment, leaving the object in a state that produced
  an unrelated `AttributeError` on the next call. Replaced with targeted
  `AttributeError` / `KeyError` handling.

- **[Minor] File handle leak in `model_compare`.** The output file was closed
  only on the success path; an exception mid-write left it open.

### Packaging

- **Migrated to `pyproject.toml`** (PEP 621); `setup.py` removed.
- **`tests` no longer ships in the wheel.** `find_packages()` picked it up as
  a top-level package and installed it into `site-packages`, where it collides
  with any other project doing the same. Packaging is now restricted to
  `cge_core*`, and CI asserts the wheel stays clean.
- **Corrected the repository URL.** Metadata and the README install
  instructions pointed at `github.com/jamesmiraflor/CGE-Core`, which does not
  exist; the project is at `github.com/miraflor/CGE-core`. The documented
  `git clone` therefore failed, as did the subsequent `cd` on case-sensitive
  filesystems.
- **Single source of truth for the version.** `__version__` is now read from
  installed distribution metadata rather than restated in `__init__.py`, where
  it had already drifted from the packaged version.
- **Consolidated licensing.** `LICENSE` and `LICENSE.txt` both existed with
  differing copyright lines, so GitHub reported ambiguous licensing. One
  `LICENSE` remains, alongside the preserved `LICENSE_NIST.txt`.
- Added `MANIFEST.in`; expanded `.gitignore`.

### Examples

- Both examples **detect an available solver** instead of hard-coding
  `'cyipopt'`, and raise an actionable error naming both install routes if
  none is found.
- **Module-level execution removed.** Importing `cge_core.examples.stdcge`
  previously ran two full solve-and-compare experiments as a side effect. The
  work now lives in `main()` behind an `if __name__ == '__main__'` guard;
  `python -m cge_core.examples.stdcge` is unchanged.

### Tests

Suite grew from 7 tests to 39, in three modules.

- **`tests/test_splcge.py` is new.** The simple model had no coverage at all,
  despite being modified in v0.2.0 (`np.prod` → Pyomo `prod` in the production
  function, scale-parameter calibration, and objective). That change is silent
  when wrong, so the SAM-reproduction assertion is the guard that matters.
  Also covers goods-market clearing and zero-profit factor-income exhaustion.
- **`tests/test_engine.py` is new.** The v0.2.0 bug fixes — sim export writing
  base values, and the inverted comparison percentage — were both
  silent-wrong-answer defects with no regression test. Both are now pinned,
  along with the objective sign, the dill round-trip, shock undo, and every
  out-of-order guard.
- **`test_tariff_abolition_raises_welfare` now uses the public API.** It
  previously reached past `model_sim` / `model_modify_sim` / `model_solve`
  with `copy.deepcopy` and a direct `SolverFactory` call, so the workflow the
  README teaches was never exercised.
- Added a check that solving the counterfactual leaves the calibrated base
  untouched, and that `model_instance` actually fixes the numeraire it
  reports fixing.
- Shared setup moved to `tests/_util.py`.

### Continuous integration

Added `.github/workflows/tests.yml` with three jobs:

1. **structural** — Python 3.9–3.12, no solver; catches import, packaging, and
   degree-of-freedom regressions quickly.
2. **solver** — real IPOPT from conda-forge, and **fails if any test skips**,
   so the solver-dependent path cannot rot unnoticed.
3. **packaging** — builds both artefacts, runs `twine check`, asserts the
   wheel leaks no `tests` package and bundles all 8 SAM CSVs, then installs
   from the wheel and smoke-tests the import.

---

## v0.2.0 (2026) — CGE-Core fork of juanfung/pycge

Forked, renamed to CGE-Core (aligning with the PSL `OG-Core` naming
convention), corrected, validated against Hosoe's standard model, and given a
regression test suite.

### Major fix: degrees-of-freedom / Walras' law

The original PyCGE could not be solved by a local IPOPT installation. A CGE
model is a square system once a numeraire price is fixed, but Walras' law makes
one market-clearing equation redundant. With every market-clearing equation
retained, the assembled system is **over-determined by exactly one equation**:

    free variables (47) - equality constraints (48) = -1

IPOPT rejects this with return code -10, "Problem has too few degrees of
freedom." The original package side-stepped the issue by solving on the
NEOS-hosted CONOPT/MINOS solvers, which absorb the redundancy internally; a
local IPOPT workflow does not.

**Fix:** a new method `PyCGE.model_drop_redundant(name, index)` deactivates one
redundant market-clearing equation, restoring a square system (DOF = 0) that
IPOPT solves via Newton iterations. By Walras' law the dropped market clears
automatically at the solution; this is asserted in the test suite as a
consistency check.

This was verified empirically: before the fix, "solving" from a +50% perturbed
starting point returned the perturbed values unchanged (the solver was not
iterating). After the fix, the solver recovers the exact SAM-consistent
equilibrium from the same perturbed start, and the tariff-abolition experiment
reproduces Hosoe's qualitative result (welfare rises ~2.3%).

### Bug fixes

- **[Critical] Sim variable export wrote base values.** In the engine, the
  simulation-variable export path used `getattr(self.base, ...)` instead of
  `getattr(self.sim, ...)`, silently writing base-case values to files labelled
  as simulation output.

- **[Significant] Comparison percentage was inverted.** `model_compare`
  computed `base/sim * 100` (a ratio) instead of `(sim - base)/base * 100`
  (percentage change), and the difference direction was flipped.

- **[Significant] `np.prod` replaced with Pyomo `prod`.** The model definition
  classes used `numpy.prod()` to build Pyomo product expressions — fragile,
  relying on NumPy's `__mul__` delegation and unsupported by Pyomo's
  expression system. Replaced with Pyomo's native `prod()` in the
  Cobb-Douglas production constraint, the scale-parameter calibration, and the
  objective, for both `splcge` and `stdcge`.

- **[Minor] Tax-revenue variable domains.** `Td`, `Tz`, `Tm`, and `Sg` were
  declared `PositiveReals`, so abolishing a tax (revenue -> 0) drove a variable
  to the boundary and triggered domain warnings. Changed to `NonNegativeReals`.

### Changes

- **Renamed** package `pycge` -> `cge_core`, module `pycge.py` -> `engine.py`.
- **Numeraire matches Hosoe.** Examples fix `pf('LAB') = 1`, matching
  `stdcge.gms` (`pf.fx("LAB") = 1`); the original examples fixed `pf('CAP')`.
- **Local solver.** Examples and tests use a local NLP solver (`cyipopt` or an
  `ipopt` executable) rather than the NEOS remote solver.
- **Removed** the incomplete, non-importing `cedar_rapids_model_def.py`
  (syntax error: `Parame` for `Param`).
- **Removed** unused `numpy` imports from the model definition modules.
- **Replaced** the old standalone demo scripts with a pytest suite
  (`tests/test_stdcge.py`).

### Tests

`tests/test_stdcge.py` (7 tests, all passing) covers:

1. the abstract model builds and a concrete instance is created;
2. the system is over-determined by exactly one equation before the drop;
3. the system is square after dropping one market-clearing equation;
4. the base case calibrates to the SAM-consistent equilibrium;
5. the solver recovers that equilibrium from a +50% perturbed start;
6. the dropped market clears automatically at the solution (Walras' law);
7. abolishing import tariffs raises welfare.

Solver-dependent tests auto-skip if no local NLP solver is found.

### Verified against reference

All 24 constraints in `stdcge_model_def.py` were checked equation-by-equation
against the GAMS Model Library `stdcge.gms` (SEQ=276). The SAM
(`param-sam-.csv`) is numerically identical to Hosoe's original. The base
equilibrium reproduces the SAM (Z = 73, 72; Xp = 20, 30; M = 13, 11;
E = 8, 4).
