# IFPRI Standard CGE Model 1.01 — GAMS reference record

This directory contains a compact validation record for the official IFPRI/TMD
Standard CGE Model, Version 1.01. It does **not** contain a CGE-Core/Pyomo port.

## Status

- Official benchmark model (`mod101.gms`, `TEST.DAT`): reproduced in GAMS 54.2.1.
- Official six simulations: reproduced as MCP/PATH and NLP/CONOPT.
- CGE-Core implementation: not yet built.
- CGE-Core replication against these results: not yet performed.

## Source

Downloaded package: `StdCGEMod1.01-030317.zip`

SHA-256:

```text
8e3a383b2bfc6bc7e1ecd2571a52b20c13cac3954a3012609e8842ec37a15544
```

The extracted files in `original/` were byte-for-byte identical to the files in
the downloaded ZIP. See `source_sha256.txt`.

The official source identifies itself as Copyright (c) 2002 IFPRI and licensed
under GNU GPL version 2. The source package is deliberately omitted from this
compact record; retain the original notice and GPL terms if redistributing it.

## Compatibility change

GAMS 54 does not recognize the historical solver name `CONOPT2`. The run copy
changed only:

```text
NLP=CONOPT2
```

to:

```text
NLP=CONOPT
```

See `compatibility_conopt.patch`. No economic equation, data value, shock, or
closure was changed.

For the separate NLP reference run, all simulations were switched from MCP to
NLP by changing `SIMMCP(SIM) = YES` to `NO`; see
`nlp_reference_switch.patch`.

## Reference environment

- GAMS 54.2.1
- PATH 5.2.01
- CONOPT 4.39.1
- Dataset: `TEST.DAT`
- Run date: 2026-08-03

The original logs were produced under a GAMS demo licence. Logs and licence
files are intentionally excluded from this record.

## Simulations

- `BASE`: benchmark
- `TARCUT1`: 50% tariff cut; flexible government savings
- `TARCUT2`: 50% tariff cut; fixed government savings with direct-tax adjustment
- `FSAVINCR`: 10% increase in foreign savings
- `PWMINCR`: 10% increase in import prices
- `DEVAL`: 10% devaluation; fixed exchange rate and flexible foreign savings

See `reference/shocks_and_closures.csv`.

## Important closure note

The simulation descriptions call `TARCUT1` and `TARCUT2` “mobile factors” and
`DEVAL` “activity-specific capital.” However, the active code and the generated
`FACCLOS` report set:

- labor: mobile and fully employed for **all** simulations;
- capital: activity-specific and fully employed for **all** simulations.

A faithful port should reproduce the active code and recorded closure tables,
while documenting this discrepancy in the source descriptions.

## Results

- MCP/PATH: GAMS model status 1 (optimal), solver status 1 (normal completion).
- NLP/CONOPT: GAMS model status 2 (locally optimal), solver status 1
  (normal completion).
- All official diagnostic warning parameters were zero.
- The MCP and NLP summary tables match exactly at the precision printed by
  GAMS. See `reference/mcp_nlp_comparison.csv`.

Reference tables:

- `reference/solver_checks.csv`
- `reference/welfare_results.csv`
- `reference/macro_results.csv`
- `reference/activity_results.csv`
- `reference/shocks_and_closures.csv`

## What this proves

This record proves that the official IFPRI GAMS model and its supplied test
simulations run successfully in modern GAMS with the solver-name compatibility
change. It supplies targets for a future Pyomo implementation.

It does **not** prove that CGE-Core replicates IFPRI. That claim becomes valid
only after a CGE-Core/Pyomo implementation reproduces these reference results
within documented tolerances.
