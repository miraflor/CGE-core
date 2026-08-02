# The Standard CGE Model (`stdcge`)

This document maps each equation in `cge_core/examples/stdcge_model_def.py` to
Hosoe, Gasawa & Hashimoto (2010), Chapters 5–6, and to the GAMS Model Library
file `stdcge.gms` (SEQ=276). Sets: goods `i ∈ {BRD, MLK}`, factors
`h ∈ {CAP, LAB}`.

## Production and factors

| Code      | Equation                                                        | Meaning                                  |
| --------- | --------------------------------------------------------------- | ---------------------------------------- |
| `eqpy`    | `Y_i = b_i · Π_h F_{h,i}^{β_{h,i}}`                              | Cobb-Douglas composite-factor production |
| `eqF`     | `F_{h,i} = β_{h,i} · py_i · Y_i / pf_h`                          | Factor demand (cost minimisation)        |
| `eqX`     | `X_{i,j} = ax_{i,j} · Z_j`                                       | Leontief intermediate demand             |
| `eqY`     | `Y_i = ay_i · Z_i`                                               | Leontief composite-factor demand         |
| `eqpzs`   | `pz_j = ay_j · py_j + Σ_i ax_{i,j} · pq_i`                       | Unit cost / zero-profit price            |

## Taxes

| Code   | Equation                          | Meaning             |
| ------ | --------------------------------- | ------------------- |
| `eqTd` | `Td = τ^d · Σ_h pf_h · FF_h`       | Direct tax revenue  |
| `eqTz` | `Tz_i = τ^z_i · pz_i · Z_i`        | Production tax      |
| `eqTm` | `Tm_i = τ^m_i · pm_i · M_i`        | Import tariff       |

## Final demand and saving

| Code    | Equation                                                  | Meaning                          |
| ------- | --------------------------------------------------------- | -------------------------------- |
| `eqXp`  | `Xp_i = α_i · (Σ_h pf_h·FF_h − Sp − Td) / pq_i`           | Household demand (Cobb-Douglas)  |
| `eqXg`  | `Xg_i = μ_i · (Td + ΣTz + ΣTm − Sg) / pq_i`               | Government demand                |
| `eqXv`  | `Xv_i = λ_i · (Sp + Sg + ε·Sf) / pq_i`                    | Investment demand                |
| `eqSp`  | `Sp = ssp · Σ_h pf_h · FF_h`                              | Private saving                   |
| `eqSg`  | `Sg = ssg · (Td + ΣTz + ΣTm)`                             | Government saving                |

## Trade (Armington / CET) and the rest of the world

| Code     | Equation                                                                 | Meaning                          |
| -------- | ------------------------------------------------------------------------ | -------------------------------- |
| `eqpqs`  | `Q_i = γ_i [δ^m_i M_i^{η_i} + δ^d_i D_i^{η_i}]^{1/η_i}`                   | Armington composite (CES)        |
| `eqM`    | `M_i = (γ_i^{η_i} δ^m_i pq_i / ((1+τ^m_i)pm_i))^{1/(1−η_i)} Q_i`          | Import demand                    |
| `eqD`    | `D_i = (γ_i^{η_i} δ^d_i pq_i / pd_i)^{1/(1−η_i)} Q_i`                     | Domestic demand for composite    |
| `eqpzd`  | `Z_i = θ_i [ξ^e_i E_i^{φ_i} + ξ^d_i D_i^{φ_i}]^{1/φ_i}`                   | CET transformation               |
| `eqE`    | `E_i = (θ_i^{φ_i} ξ^e_i (1+τ^z_i)pz_i / pe_i)^{1/(1−φ_i)} Z_i`            | Export supply                    |
| `eqDs`   | `D_i = (θ_i^{φ_i} ξ^d_i (1+τ^z_i)pz_i / pd_i)^{1/(1−φ_i)} Z_i`            | Domestic supply of the composite |
| `eqpe`   | `pe_i = ε · pWe_i`                                                        | Export price (world × FX)        |
| `eqpm`   | `pm_i = ε · pWm_i`                                                        | Import price (world × FX)        |
| `eqepsilon` | `Σ_i pWe_i·E_i + Sf = Σ_i pWm_i·M_i`                                   | Balance of payments              |

## Market clearing

| Code     | Equation                                  | Meaning                       |
| -------- | ----------------------------------------- | ----------------------------- |
| `eqpqd`  | `Q_i = Xp_i + Xg_i + Xv_i + Σ_j X_{i,j}`  | Composite-good market         |
| `eqpf`   | `Σ_i F_{h,i} = FF_h`                       | Factor market                 |

## Objective

`max Π_i Xp_i^{α_i}` — a fictitious Cobb-Douglas utility. With the household
demand equations `eqXp` already embodying utility maximisation, the objective
is economically redundant; it serves only to give the NLP solver a well-defined
problem once the system is made square.

---

## Closure and degrees of freedom

Counting the **scalar** (expanded) system:

- variables: 48; one is fixed as numeraire (`pf['LAB']`) → **47 free**;
- equality constraints: **48**.

Raw DOF = 47 − 48 = **−1**: the system is over-determined by one equation
because of Walras' law (one market-clearing condition is implied by the others
plus the agents' budget constraints). Dropping one market-clearing equation
with `model_drop_redundant('eqpf', 'LAB')` gives a square system (DOF = 0) that
IPOPT solves. The dropped market clears automatically at the solution; the test
suite asserts this as a Walras'-law consistency check.

The choice of which equation to drop is immaterial — any single market-clearing
condition works, and the computed equilibrium is identical.

## Calibration

All behavioural parameters are recovered from the SAM so that the base instance
reproduces the data exactly:

- shares `α_i, β_{h,i}, μ_i, λ_i` from expenditure/value-added/investment rows;
- Leontief coefficients `ax_{i,j}, ay_i`;
- CES/CET share and scale parameters `δ^m, δ^d, γ` and `ξ^e, ξ^d, θ` from the
  substitution/transformation elasticities `σ_i, ψ_i` (both 2 by default) and
  base quantities/prices;
- tax and saving rates `τ^d, τ^z_i, τ^m_i, ssp, ssg` as ratios from the SAM.

At the base equilibrium all prices equal 1, so calibrating with unit prices is
consistent. The standard SAM yields the base solution
`Z = (73, 72)`, `Xp = (20, 30)`, `M = (13, 11)`, `E = (8, 4)`.


## Numerical lower bounds

The model reproduces the reference implementation's explicit numerical lower
bounds to keep divisions and fractional powers away from zero. All positive
`stdcge` quantities, prices, the exchange rate, private saving, government
saving, and direct tax have lower bound `1e-5`. Production-tax and import-tariff
revenues (`Tz`, `Tm`) may be zero. The simple model uses `1e-3` for all positive
variables.
