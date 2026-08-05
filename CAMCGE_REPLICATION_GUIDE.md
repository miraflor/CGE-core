# Step-by-step CAMCGE validation of CGE-Core

## Purpose

Use the Cameroon CGE model of Condon, Dahl, and Devarajan (1987) as an
independent regression benchmark for CGE-Core. The test compares the CGE-Core
solution with the paper's printed 1987 base solution and its three policy
experiments.

This prepared package corrects two issues in the earlier draft:

1. `make_data.py` now writes to `cam/data` regardless of the current working
   directory; and
2. the base comparison contains 98 printed variable levels, not 106.

It also makes the experiment script self-contained, adds permanent pytest
coverage, uses the paper-consistent real-wage deflator, and documents all known
Experiment 1 residuals.

## What was already checked before local integration

The package has undergone the following offline checks:

- archive contents and Python syntax inspected;
- source-table adding-up checks executed;
- all eight generated CSV files compared cell-for-cell with the supplied data;
- set headers and first members checked;
- the full 242-variable, 242-equation system independently reconstructed and
  solved with SciPy, outside CGE-Core and Pyomo;
- base objective and all 98 published levels independently compared;
- all three policy experiments independently solved and audited; and
- regression tests written for the data, closure, base solution, Walras gap,
  and policy experiments.

The independent solve is a mathematical cross-check, not a substitute for the
remaining local test: executing the same model through your actual CGE-Core
checkout and IPOPT installation.

---

## Local Step 1 — Start from a clean feature branch

Run in Anaconda Prompt:

```bat
conda activate cgecore
cd "C:\Users\James Matthew\Documents\GitHub\CGE-core"
git status --short
git switch main
git pull --ff-only origin main
git switch -c feature/camcge-replication
```

Do not continue if `git status --short` shows unrelated local changes. If the
branch already exists, use:

```bat
git switch feature/camcge-replication
```

## Local Step 2 — Establish the unchanged baseline

```bat
python -m pytest tests -q
```

Record the result. This must succeed before adding the CAMCGE files, so any
later failure can be attributed to the integration rather than the existing
repository.

## Local Step 3 — Extract the prepared package at the repository root

Using the `.tar.gz` package:

```bat
tar -xzf "C:\path\to\camcge-integration-ready.tar.gz"
```

It should add only:

```text
cam/  (including cam/NOTICE.md)
tests/cam/
CAMCGE_REPLICATION_GUIDE.md
CAMCGE_VALIDATION_REPORT.md
```

Then inspect:

```bat
git status --short
```

## Local Step 4 — Run the solver-free checks

```bat
python cam\make_data.py
python -m pytest tests\cam\test_data.py -v
```

Expected data-generator output begins with:

```text
data written; adding-up checks passed; ls0 = {'rural': 2270.04, 'urban-unsk': 515.064, 'urban-skil': 132.515}
```

The focused test file should report five passes. It exercises the source-table
identities, exact CSV regeneration, set headers, model metadata, and the
closure count before solving.

## Local Step 5 — Confirm the solver interface

```bat
python -c "from pyomo.environ import SolverFactory; print('ipopt=', SolverFactory('ipopt').available(exception_flag=False)); print('cyipopt=', SolverFactory('cyipopt').available(exception_flag=False))"
```

Use whichever prints `True`. In your previous CGE-Core work this is likely
`cyipopt`.

## Local Step 6 — Replicate the published base equilibrium

For `cyipopt`:

```bat
python cam\replicate_base.py --solver cyipopt
```

For the IPOPT executable:

```bat
python cam\replicate_base.py --solver ipopt
```

Required checks:

```text
DOF before drop: -1   after: 0
omega: got 191.7346  published 191.7346
max |level - published| across 98 reported variable levels: about 5e-05
ALL reported levels match the 1987 published solution to < 5e-3
current-account gap (dropped caeq): approximately zero
```

The script also saves `cam/cge_base.dill`. That file is a local generated
artifact and should normally not be committed.

## Local Step 7 — Replicate the three policy experiments

```bat
python cam\replicate_experiments.py --solver cyipopt
```

Substitute `ipopt` when applicable. The final line must be:

```text
ALL CAMCGE experiment regression checks passed.
```

The script deliberately fails if an asserted published comparison moves beyond
its tolerance. Known Experiment 1 residuals are explicitly excluded and
printed, not silently treated as matches.

## Local Step 8 — Run the permanent CAMCGE regression suite

```bat
python -m pytest tests\cam -v -rs
```

Required result: seven tests pass and none skip. A skip in
`test_replication.py` means no local NLP solver was detected; it is not a
successful validation.

## Local Step 9 — Prove no regression elsewhere in CGE-Core

```bat
python -m pytest tests -q
```

Then run the IFPRI subsystem explicitly as an additional diagnostic:

```bat
python -m pytest tests\ifpri -q
```

The complete `tests` run remains the authoritative regression check for the
Hosoe models, engine, IFPRI subsystem, and CAMCGE integration together.

## Local Step 10 — Inspect before any commit

```bat
git status --short
git diff --stat
git diff -- cam tests\cam CAMCGE_REPLICATION_GUIDE.md CAMCGE_VALIDATION_REPORT.md
```

Remove generated local artifacts before staging:

```bat
del cam\cge_base.dill 2>nul
for /d /r %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
```

Check status again. Do not stage, commit, push, or open a pull request until the
outputs from Steps 6–9 have been reviewed.

## Acceptance criteria

The integration is ready for review only when all of these are true:

- existing tests passed before extraction;
- all five solver-free CAMCGE tests passed;
- base degrees of freedom changed from `-1` to `0` after dropping `caeq`;
- `omega` matched `191.7346` within `1e-3`;
- all 98 printed levels matched within `5e-3`;
- base and experiment current-account gaps were below `1e-8`;
- all three experiment regression checks passed;
- all seven CAMCGE tests passed without skips; and
- the complete CGE-Core suite still passed.
