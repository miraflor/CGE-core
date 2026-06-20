# Changelog

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
