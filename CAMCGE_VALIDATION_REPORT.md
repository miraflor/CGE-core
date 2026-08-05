# CAMCGE validation report

**Status:** Completed. CGE-Core reproduced the published Cameroon base
equilibrium and all three policy experiments through the local Pyomo/IPOPT
stack. The full 180-test suite passed locally, all nine GitHub Actions checks
passed, and pull request #2 was merged into `main`.

## Scope

The reviewed package implements the Cameroon CGE benchmark associated with
Condon, Dahl, and Devarajan (1987), World Bank DRD290, and the GAMS Model
Library `camcge` example. The objective is to test CGE-Core against printed
historical results independent of the Hosoe and IFPRI benchmarks.

## Corrections made during review

1. Fixed `make_data.py` so `python cam/make_data.py` writes to `cam/data` from
   the repository root. The supplied draft instead attempted to write to a
   nonexistent root-level `data/` directory.
2. Refactored data generation so importing the module does not write files.
3. Corrected an adding-up assertion from `abs(sum(values)) - 1` to
   `abs(sum(values) - 1)`.
4. Regenerated all eight CSVs and verified exact cell-for-cell equality with
   the supplied benchmark data.
5. Corrected the documented published-level count from 106 to 98.
6. Made base and experiment scripts independent of the caller's working
   directory.
7. Made the experiments build a fresh calibrated base instead of depending on
   a pre-existing pickle.
8. Reconciled real-wage comparisons with the paper's base-quantity-weighted
   composite-price deflator.
9. Added structural and solver-backed pytest regression tests.
10. Documented an additional small Experiment 1 residual: forestry imports
    reproduce approximately `+4.6%`, while the paper prints `+4.8%`.

## Independent numerical audit

A separate NumPy/SciPy reconstruction was used only as an audit tool and is not
included in the integration package. It solved 242 variables against 242 active
equations after imposing the savings closure and dropping the current-account
equation.

### Base equilibrium

- maximum scaled residual: approximately `1.85e-15`;
- objective: `191.7346242369`;
- difference from printed `191.7346`: approximately `2.42e-05`;
- maximum absolute discrepancy across the 98 compared printed levels:
  approximately `4.98e-05`;
- dropped current-account equation gap: approximately `-5.61e-13`.

### Experiment 1 — oil windfall (`fsav = 500`)

- real investment: `+33.717%`;
- aggregate domestic prices: `+27.362%`;
- aggregate composite prices: `+20.968%`;
- nominal wage bill: `+25.359%`;
- paper-deflated real wages: approximately `+1.489%`, `+5.109%`, and
  `+5.308%`.

The accepted table cells were within approximately `0.10` percentage points.
The disclosed residuals are the two near-zero services output cells and the
forestry-import cell. The paper's printed export total is not used as a
regression target because it is inconsistent with aggregation of the printed
sector rows.

### Experiment 2 — double the food-crop tariff

- food-crop imports: `-21.783%`;
- food-crop output: `+0.0368%`;
- largest absolute output movement among the other sectors: approximately
  `0.110%`;
- tariff revenue: `+0.4215%`.

### Experiment 3 — double tariffs on intermediate and construction materials

- maximum output-table discrepancy: approximately `0.0734` percentage points;
- maximum domestic-price-table discrepancy: approximately `0.0853` points;
- maximum composite-price-table discrepancy: approximately `0.0480` points;
- tariff revenue: `+39.208%`;
- real investment: `+9.319%`;
- intermediate-goods imports: `-7.806%`;
- construction-material imports: `+0.412%`;
- paper-deflated real wages: approximately `-3.332%`, `-3.058%`, and
  `-3.194%`.

## Completed integration validation

The replication was subsequently executed through the actual CGE-Core engine
on Windows with Python 3.11 and the IPOPT executable:

- base degrees of freedom changed from `-1` to `0` after dropping `caeq`;
- welfare reproduced `191.7346` with a difference of approximately `2.42e-05`;
- the maximum discrepancy across 98 published variable levels was
  approximately `4.98e-05`;
- the dropped current-account equation cleared with a gap of approximately
  `-7.89e-13`;
- all three published experiment regression checks passed;
- all seven CAMCGE tests passed locally;
- the complete project suite passed with 180 tests and no skips or failures;
- all nine GitHub Actions checks passed, including packaging, documentation,
  IPOPT solver, and structural tests across supported Python versions; and
- pull request #2 was merged into `main` as merge commit `c9a4782`.

These results support the claim that CGE-Core itself reproduces the historical
Cameroon benchmark within the documented tolerances.

## Repository status

The CAMCGE benchmark is integrated into `main`. Generated artifacts such as
`cam/cge_base.dill`, `__pycache__`, solver logs, and other runtime outputs must
remain uncommitted. The provenance notice should accompany any redistribution
or publication derived from the model port and transcribed benchmark data.
