# CGE-Core v0.7.0 independent review resolution

**Review date:** 29 August 2026  
**Baseline checked:** v0.6.0 commit `7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2`

This note records how the independent review of the first v0.7.0 overlay was resolved. It distinguishes reproduced defects, baseline questions that were checked directly, non-defects, and deliberately deferred cleanup.

## Release-blocking defects — fixed

1. **Multi-dimensional `.cge.md` parameters** — fixed. Indexed parameter assignments now build tuple keys consistently with expression lookup.
2. **Explicit `shockable = set()`** — fixed. `None` now means “not declared/open authoring mode”; an explicitly empty set means nothing is shockable.
3. **Hyphenated component identifiers** — fixed by restricting grammar-0 identifiers to Python-style names. Set members use the same rule in grammar 0.
4. **Comparison operators in equations** — fixed with a named, source-located error for `==`, `>=`, `<=`, and `!=`; equations require exactly one standalone `=`.
5. **Parameter-only equations** — fixed. They are rejected instead of becoming live trivial constraints and distorting the DOF count.
6. **`FunctionalResult.compare` dead code / missing guards** — fixed. Dead code was removed; reference type, model identity, and structural compatibility are validated with clear errors; legacy objective metadata remains available.
7. **Functional immutable-parameter mutation** — fixed with an author-facing `ComponentError` before Pyomo mutation.
8. **IFPRI configured solver lost in scenarios** — fixed. The selected/configured solver is carried from `IFPRICGE` → equilibrium → scenario and can still be overridden per solve.
9. **Python 3.9/3.10 `tomllib` collection failure** — fixed with a `tomli` fallback and corresponding test/dev dependency marker.
10. **Known unused imports / lint setup** — fixed. The reviewed unused imports were removed and a minimal Ruff configuration was added.

## Benchmark-protection regression — fixed and hardened

The first overlay would have removed the old `name.endswith("0")` protection from CAMCGE without replacing it. This was a release blocker.

The revised kit now:

- declares all 20 CAMCGE trailing-`0` benchmark components explicitly in `CAM_SPEC`;
- injects the same declaration into retained `CamModelDef` for the legacy `PyCGE` path;
- preserves the Standard and Simple explicit declarations;
- runs a preflight that scans the retained v0.6 model sources and requires the explicit sets to match **every** `Param`/`Var` ending in `0` exactly before any file is changed;
- verifies the Standard/Simple SAM protection anchor separately.

This preserves the v0.6 protection semantics without continuing the runtime spelling heuristic.

## `prepare_release.py` — redesigned

The release preparation script now:

- validates **all** baseline files, metadata coverage, and patch anchors before mutation;
- supports `python release/prepare_release.py --check` as a complete no-write preflight;
- resolves the repository root from the script path rather than the current working directory;
- remains in `release/` instead of deleting itself;
- uses a unique IFPRI solver-patch sentinel;
- writes only files whose content actually changes;
- preserves each existing file's LF/CRLF newline convention;
- patches only the two known CAM replication scripts rather than rewriting every `cam/*.py`;
- changes their default solver to `None` only so the already-supported automatic resolver is used; downstream code passes that value directly to the resolver-compatible solve path;
- is idempotent after application.

A synthetic retained-tree test was used in the generation environment to exercise preflight → apply → second preflight and confirm zero planned changes on the second pass.

## Documentation / notebook gaps — fixed

- The Jupyter Book TOC now includes all seven notebooks through `docs/notebooks/` copies.
- `docs/check_docs.py` checks the retained baseline reference pages when it is run in the merged repository.
- The forbidden-notebook-plumbing scan is now actually used by the docs check.
- Notebook install cells no longer try PyPI first when CGE-Core is already installed locally. They conditionally install the package, then run the one-line solver helper.
- README Standard-CGE policy examples now use the bundled `BRD`/`MLK` labels rather than non-existent `AGR`/`MAN` labels.
- `90_internals.ipynb` is no longer exempted from the notebook cleanliness scan.
- The duplicate Control Room version-only test was removed; the stronger compatibility test remains.

## Questions that required the exact v0.6 baseline — resolved

1. **One-clone scenario architecture.** Checked against v0.6 `PyCGE.model_sim()`: the retained method deep-copies `base` and resets only `sim_results`, `sim_solved`, and `dict_sim`. The new `Equilibrium.scenario()` performs those same state changes on a shallow copy of engine bookkeeping while deep-copying the calibrated concrete model once. No additional hidden `model_sim()` state was found.
2. **Control Room fixture/app surfaces.** Both required retained files and strings exist in the v0.6 baseline. The revised preflight explicitly validates them before applying changes.
3. **`institutions=accounts.values()`.** `samtools.build_dataset` treats institutions as an iterable for membership/classification, not as a positional contract. Even so, v0.7 now passes an explicit six-role list to make the API contract obvious.
4. **`param-sam-.csv` in the SAM notebook.** Checked directly: the bundled Standard-CGE `param-sam-.csv` is the square, balanced SAM itself, so it is a valid `from_sam()` demonstration input. The notebook now states this explicitly.
5. **`SolveError(..., results=...)`.** Checked against v0.6: `SolveError.__init__(message, results=None)` supports the keyword. No defect.
6. **Functional example without an Objective.** Hardened anyway: the tutorial model now declares an explicit zero objective, making the intended feasibility solve explicit for NLP interfaces.

## Smaller review items

Fixed: DOF duplication in the functional adapter, practitioner CLI error handling, safe solver failure formatting, `SimpleCGE` path normalization, solver diagnostic wording, explicit temporary-SAM cleanup/context management, set-member/declaration collision validation, and scale-independent strict bounds using `math.nextafter`.

**Python 3.14 classifier:** retained. The v0.6 repository already has a structural CI matrix covering Python 3.9 through 3.14, so the review's “no CI lane” concern is not applicable.

**Duplicate scenario/component key helper:** intentionally left as a small internal cleanup item. Removing the duplication has no user-visible or scientific effect and is not worth widening the pre-release diff after the behavioral issues above were fixed.

## Release-document corrections

- `IMPLEMENTATION_STATUS.md` no longer claims an unavailable real-baseline dry run; it accurately records static/synthetic preflight validation and the remaining numerical checks.
- `CHANGELOG_v070.md` clarifies compatibility exports and records the independent-review hardening.
- `APPLY_OVERLAY.md` now documents the no-write preflight and the fact that `release/` remains available as auditable tooling/provenance.

## Validation performed on the revised overlay

Performed in the generation environment:

- `python -m compileall -q cge_core tests release examples`;
- `python docs/check_docs.py`;
- TOML and Jupyter Book YAML parsing;
- JSON validation of canonical and documentation notebook copies;
- byte-for-byte equality check between canonical notebooks and their Jupyter Book copies;
- notebook forbidden-plumbing scan;
- `pytest -q tests/test_v070_notebooks.py tests/test_v070_packaging.py` (**6 passed**);
- synthetic `prepare_release.py` preflight/apply/idempotence exercise.

Not performed here because Pyomo/IPOPT are not installed in the generation environment:

- `.cge.md` compiler execution against Pyomo;
- model-level tests that import Pyomo;
- Hosoe numerical regression;
- CAMCGE published benchmark/experiment regression;
- IFPRI synthetic solver lane;
- executed numerical notebook validation.

Those remain mandatory on the merged v0.6 + v0.7 tree before the tag is published.
