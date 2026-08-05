# CAMCGE replication benchmark

This module tests CGE-Core against the Cameroon model published by Condon,
Dahl, and Devarajan (1987), *Implementing a Computable General Equilibrium
Model on GAMS: The Cameroon Model* (World Bank DRD290), and distributed as
`camcge.gms` in the GAMS Model Library (SEQ=81).

The validation is a three-way comparison:

1. the numerical solution and experiment tables printed in the 1987 paper;
2. the published CAMCGE model specification; and
3. the Pyomo model executed through CGE-Core's public `PyCGE` workflow.

The module is intentionally outside the installed `cge_core` package. It is a
replication and regression benchmark, not a new claim that CAMCGE was authored
as part of CGE-Core. See `NOTICE.md` for provenance notes.

## Contents

- `make_data.py` transcribes the benchmark tables, checks adding-up identities,
  and writes the eight CGE-Core CSV input files.
- `cam_model_def.py` expresses the CAMCGE equations as a CGE-Core model
  definition.
- `replicate_base.py` solves the base equilibrium and compares 98 published
  variable levels plus the objective value.
- `replicate_experiments.py` solves the paper's three policy experiments and
  checks the published percentage changes.
- `data/` contains the generated CSV files committed for reproducibility.
- `../tests/cam/` contains structural and numerical regression tests.

## Run from the repository root

Generate and verify the data:

```bash
python cam/make_data.py
python -m pytest tests/cam/test_data.py -v
```

Run the base replication and policy experiments with `cyipopt`:

```bash
python cam/replicate_base.py --solver cyipopt
python cam/replicate_experiments.py --solver cyipopt
python -m pytest tests/cam -v
```

Use `--solver ipopt` instead when the IPOPT executable, rather than Pyomo's
`cyipopt` interface, is installed.

## Expected base result

The base run should report:

- degrees of freedom: `-1` before dropping `caeq`, then `0`;
- objective `omega` approximately `191.7346`;
- maximum absolute discrepancy across 98 printed variable levels below
  `5e-3` (normally about `5e-5`); and
- the dropped current-account equation clearing to below `1e-8`.

The count is 98, obtained directly from the ten compared groups:
`x`, `xd`, `xxd`, `e`, `mq`, `pva`, `wa`, `cd`, `intm`, and `idv`.
An earlier draft incorrectly described this as 106.

## Experiment interpretation

Experiment 3 is the strongest table-level replication: all output, domestic
price, and composite-price cells are required to match within 0.15 percentage
points. Experiment 2 reproduces the paper's near-zero response to doubling the
food-crop tariff.

Experiment 1 contains documented residuals rather than hidden exclusions:

- services output is approximately `-0.7%` while the paper prints `+0.1%`;
- public-services output is approximately `+0.4%` while the paper prints
  `-0.4%`;
- forestry imports are approximately `+4.6%` while the paper prints `+4.8%`;
- the paper's printed export total is inconsistent with aggregation of its own
  sector rows, so the regression checks the sector rows rather than that total.

For real wages, the scripts use the paper-consistent base-quantity-weighted
composite-price index. A consumption-price index produces different numbers
and should not be compared directly with the paper's real-wage row.

## Data transcription notes

Two fixed-width entries are positionally ambiguous in plain-text extraction of
the source table. Their placements are resolved using identities and printed
solution values from the same published model:

- `itax`: construction `0.034`, services `0.076`, public services `0`;
- `id`: `113.36` for capital goods and `138.13` for construction.

The set CSVs must retain their header rows (`i`, `lc`, and `zrow`). CGE-Core's
loader consumes the first row as the set name; omitting it would discard the
first actual member.
