# IFPRI Standard CGE replication

CGE-Core includes an independently written Python/Pyomo implementation of the
**IFPRI Standard CGE test economy**. With the externally supplied IFPRI test
data, it reproduces the BASE benchmark and five recorded policy simulations to
numerical solver tolerance.

This is a precise, bounded claim. It does **not** mean that CGE-Core reproduces
every country application, database, closure, or later variant built with the
IFPRI Standard CGE framework.

## What is and is not distributed

The repository contains the clean-room Python equations, calibration,
closures, scenario definitions, tests, and full-precision validation targets.
It does not contain the official IFPRI source package or `test.dat`.

Point `IFPRI_SOURCE_DIR` to the folder containing your separately obtained
`test.dat`:

```powershell
$env:IFPRI_SOURCE_DIR = "C:\path\to\ifpri-test-folder"
```

```bat
set IFPRI_SOURCE_DIR=C:\path\to\ifpri-test-folder
```

The directory is resolved only at runtime. The source file is parsed and
validated but is neither copied into CGE-Core nor added to package artifacts.

## Load and calibrate the benchmark

```python
from cge_core.ifpri import (
    calibrate_ifpri_benchmark,
    load_ifpri_test_data,
    validate_ifpri_calibration,
)

dataset = load_ifpri_test_data()
calibration = calibrate_ifpri_benchmark(dataset)
validate_ifpri_calibration(dataset, calibration)
```

The loader validates set relationships, SAM membership and balance,
elasticity coverage and ranges, home-consumption shares, factor quantities,
and tax mappings. Calibration is algebraic: it reconstructs the normalized
benchmark prices and quantities before any nonlinear solve is attempted.

## Solve BASE

```python
from cge_core.ifpri import (
    build_ifpri_base_solve_model,
    perturb_ifpri_start,
    solve_ifpri_base,
)

base_model = build_ifpri_base_solve_model(dataset, calibration)
perturb_ifpri_start(base_model, 1.02)
base_report = solve_ifpri_base(base_model)

print(base_report.termination_condition)
print(base_report.max_abs_equation_residual)
```

The BASE closure fixes the CPI numeraire, foreign saving, investment scaling,
and government-demand scaling; applies the recorded labor and
activity-specific-capital closures; and minimizes the squared Walras residual.
The solve is accepted only after an optimal or locally optimal termination.

## Run the policy simulations

```python
from cge_core.ifpri import build_and_solve_ifpri_scenarios

results = build_and_solve_ifpri_scenarios(dataset)
```

`results` maps each scenario to `(model, solve_report)`:

| Scenario   | Shock and closure |
| ---------- | ----------------- |
| `TARCUT1`  | 50% tariff cut; flexible government saving |
| `TARCUT2`  | 50% tariff cut; fixed government saving and uniform direct-tax adjustment |
| `FSAVINCR` | 10% increase in foreign saving |
| `PWMINCR`  | 10% increase in world import prices |
| `DEVAL`    | 10% devaluation under a fixed-exchange-rate closure |

## Extract and report results

The reporting API returns pandas DataFrames rather than printing model
internals:

```python
from pathlib import Path

from cge_core.ifpri import (
    compare_ifpri_scenarios,
    extract_ifpri_solution,
    summarize_ifpri_results,
)

base_values = extract_ifpri_solution(base_model)
summary = summarize_ifpri_results(results)
changes = compare_ifpri_scenarios(base_model, results)

output = Path("ifpri-results")
output.mkdir(exist_ok=True)
base_values.to_csv(output / "base_values.csv", index=False)
summary.to_csv(output / "solve_summary.csv", index=False)
changes.to_csv(output / "scenario_changes.csv", index=False)
```

`extract_ifpri_solution` produces one row per active variable element, with up
to three explicit index columns, the value, and whether it is fixed.
`compare_ifpri_scenarios` reports **scenario minus BASE** and the percentage
change. Percentage changes are left undefined where the BASE value is
numerically zero. The comparison includes variables common to both models;
scenario-only closure variables can still be extracted directly from the
scenario model.

A smaller report can be requested by component name:

```python
changes = compare_ifpri_scenarios(
    base_model,
    results,
    components=("EXR", "CPI", "QA", "QH", "QM", "QE"),
)
```

## Validate against the GAMS reference

Within a repository checkout, the full-precision target table can be used for
an explicit comparison:

```python
from pathlib import Path

from cge_core.ifpri import (
    compare_ifpri_model_to_reference,
    load_ifpri_reference_targets,
)

reference = Path(
    "validation/gams/ifpri_standard/reference/full_precision_targets.csv"
)
targets = load_ifpri_reference_targets(reference, "NLP", "BASE")
comparison = compare_ifpri_model_to_reference(base_model, targets)

print(comparison.compared_values)
print(comparison.max_abs_difference)
print(comparison.max_relative_difference)
```

The external replication suite checks BASE and all five scenarios against the
full-precision targets. Public GitHub Actions cannot use the official
`test.dat`, so it instead exercises the same calibration, equation, closure,
shock, reporting, and IPOPT pathways with an independently authored,
redistributable synthetic economy. External-data tests and public tests are
marked separately so that unavailable official data cannot be mistaken for a
successful replication run.

## Clean-room boundary

The Python equations were implemented independently from public mathematical
descriptions. Official GAMS source files remain outside the repository and are
used only to produce or verify external reference results. The public synthetic
fixture is independently authored and is not copied or derived from the
official IFPRI test dataset.
