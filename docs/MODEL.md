# The Standard CGE Model (`stdcge`)

This document maps each equation in `cge_core/models/standard/model.py` to
Hosoe, Gasawa & Hashimoto (2010), Chapters 5–6, and to the GAMS Model Library
file `stdcge.gms` (SEQ=276).

The bundled example has goods
$i \in \{\mathrm{BRD},\mathrm{MLK}\}$ and factors
$h \in \{\mathrm{CAP},\mathrm{LAB}\}$.

## Production and factors

| Code | Equation | Meaning |
| --- | --- | --- |
| `eqpy` | $Y_i=b_i\prod_h F_{h,i}^{\beta_{h,i}}$ | Cobb-Douglas composite-factor production |
| `eqF` | $F_{h,i}=\dfrac{\beta_{h,i}p_i^yY_i}{p_h^f}$ | Factor demand |
| `eqX` | $X_{i,j}=a^x_{i,j}Z_j$ | Leontief intermediate demand |
| `eqY` | $Y_i=a_i^yZ_i$ | Leontief composite-factor demand |
| `eqpzs` | $p_j^z=a_j^yp_j^y+\sum_i a^x_{i,j}p_i^q$ | Unit cost / zero-profit price |

## Taxes

| Code | Equation | Meaning |
| --- | --- | --- |
| `eqTd` | $T^d=\tau^d\sum_h p_h^fFF_h$ | Direct-tax revenue |
| `eqTz` | $T_i^z=\tau_i^zp_i^zZ_i$ | Production-tax revenue |
| `eqTm` | $T_i^m=\tau_i^mp_i^mM_i$ | Import-tariff revenue |

## Final demand and saving

| Code | Equation | Meaning |
| --- | --- | --- |
| `eqXp` | $X_i^p=\dfrac{\alpha_i}{p_i^q}\left(\sum_h p_h^fFF_h-S^p-T^d\right)$ | Household demand |
| `eqXg` | $X_i^g=\dfrac{\mu_i}{p_i^q}\left(T^d+\sum_jT_j^z+\sum_jT_j^m-S^g\right)$ | Government demand |
| `eqXv` | $X_i^v=\dfrac{\lambda_i}{p_i^q}\left(S^p+S^g+\varepsilon S^f\right)$ | Investment demand |
| `eqSp` | $S^p=ss^p\sum_h p_h^fFF_h$ | Private saving |
| `eqSg` | $S^g=ss^g\left(T^d+\sum_jT_j^z+\sum_jT_j^m\right)$ | Government saving |

## Trade: Armington, CET, and the rest of the world

| Code | Equation | Meaning |
| --- | --- | --- |
| `eqpqs` | $Q_i=\gamma_i\left[\delta_i^mM_i^{\eta_i}+\delta_i^dD_i^{\eta_i}\right]^{1/\eta_i}$ | Armington composite |
| `eqM` | $M_i=\left[\dfrac{\gamma_i^{\eta_i}\delta_i^mp_i^q}{(1+\tau_i^m)p_i^m}\right]^{1/(1-\eta_i)}Q_i$ | Import demand |
| `eqD` | $D_i=\left[\dfrac{\gamma_i^{\eta_i}\delta_i^dp_i^q}{p_i^d}\right]^{1/(1-\eta_i)}Q_i$ | Domestic demand for the Armington composite |
| `eqpzd` | $Z_i=\theta_i\left[\xi_i^eE_i^{\phi_i}+\xi_i^dD_i^{\phi_i}\right]^{1/\phi_i}$ | CET transformation |
| `eqE` | $E_i=\left[\dfrac{\theta_i^{\phi_i}\xi_i^e(1+\tau_i^z)p_i^z}{p_i^e}\right]^{1/(1-\phi_i)}Z_i$ | Export supply |
| `eqDs` | $D_i=\left[\dfrac{\theta_i^{\phi_i}\xi_i^d(1+\tau_i^z)p_i^z}{p_i^d}\right]^{1/(1-\phi_i)}Z_i$ | Domestic supply |
| `eqpe` | $p_i^e=\varepsilon p_i^{We}$ | Export price |
| `eqpm` | $p_i^m=\varepsilon p_i^{Wm}$ | Import price |
| `eqepsilon` | $\sum_i p_i^{We}E_i+S^f=\sum_i p_i^{Wm}M_i$ | Balance of payments |

## Market clearing

| Code | Equation | Meaning |
| --- | --- | --- |
| `eqpqd` | $Q_i=X_i^p+X_i^g+X_i^v+\sum_jX_{i,j}$ | Composite-good market |
| `eqpf` | $\sum_iF_{h,i}=FF_h$ | Factor market |

## Objective

The model maximizes the Cobb-Douglas household-utility index

```{math}
UU
=
\prod_i \left(X_i^p\right)^{\alpha_i}.
```

The household-demand equations already embody utility maximisation, so the
constraint system pins down the equilibrium once the model is square. The
objective gives the NLP solver a well-defined optimization problem and its
solution value is the utility level used by the model's welfare reporting.

---

## Closure and degrees of freedom

Counting the **scalar** expanded system:

- variables: 48; one is fixed as the numeraire (`pf['LAB']`), leaving **47 free**;
- equality constraints: **48**.

Therefore,

```{math}
\mathrm{DOF}
=
47-48
=
-1.
```

The raw system is over-determined by one equation because Walras' law makes
one market-clearing condition dependent on the others plus the agents' budget
constraints.

Dropping one admissible market-clearing equation with

```python
cge.model_drop_redundant("eqpf", "LAB")
```

gives a square system with zero degrees of freedom. The dropped factor market
still clears at the solution and is checked by the test suite.

The standard model declares `eqpf` and `eqpqd` as admissible redundant
market-clearing families. One scalar market-clearing condition is dropped in
a solve; arbitrary behavioural equations are not valid closure choices.

## Calibration

All behavioural parameters are recovered from the SAM so that the base
instance reproduces the benchmark:

- expenditure and factor shares:
  $\alpha_i$, $\beta_{h,i}$, $\mu_i$, and $\lambda_i$;
- Leontief coefficients:
  $a^x_{i,j}$ and $a_i^y$;
- CES/CET parameters:
  $\delta_i^m$, $\delta_i^d$, $\gamma_i$,
  $\xi_i^e$, $\xi_i^d$, and $\theta_i$;
- substitution/transformation parameters derived from the fixed benchmark
  elasticities $\sigma_i=\psi_i=2$;
- tax and saving rates:
  $\tau^d$, $\tau_i^z$, $\tau_i^m$, $ss^p$, and $ss^g$.

At the base equilibrium all prices equal 1. The bundled standard SAM yields

```{math}
Z=(73,72),\qquad
X^p=(20,30),\qquad
M=(13,11),\qquad
E=(8,4).
```

## Numerical lower bounds

The model reproduces the reference implementation's explicit numerical lower
bounds to keep divisions and fractional powers away from zero.

All positive `stdcge` quantities, prices, the exchange rate, private saving,
government saving, and direct tax use a lower bound of $10^{-5}$.
Production-tax and import-tariff revenues (`Tz`, `Tm`) may be zero.

The simple model uses $10^{-3}$ for its positive variables.
