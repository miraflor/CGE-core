# Closure requirements ledger

**Status:** requirements only; not a v0.6 public abstraction.

The purpose of this ledger is to accumulate concrete closure cases before extracting a cross-backend `Closure` abstraction. v0.6 intentionally implements only the Hosoe engine-backed facade.

## Case 1 — Hosoe simple/standard CGE

- one price variable is fixed as numeraire, e.g. `pf[LAB] = 1`;
- one Walras-redundant market equation is dropped, e.g. `eqpf[LAB]`;
- the public v0.6 facade spells this as keyword-only `numeraire=` and `redundant=` arguments.

## Case 2 — CAMCGE

- savings-driven closure fixes `mps`;
- `mps` is not a price numeraire;
- the price system is anchored through exogenous `er` and world prices such as `pwm`;
- `caeq` is dropped under Walras' law.

This is direct evidence that the Hosoe `numeraire=` spelling must not become the universal extension contract.

## Case 3 — IFPRI BASE closure

The clean-room IFPRI backend uses its own closure machinery, including the CPI anchor, foreign savings, government/investment adjustment variables, factor-market treatment, and the WALRAS/WALRASSQR objective formulation. It is not forced into the v0.6 facade.

## Case 4 — IFPRI scenario closures

Known cases include TARCUT1, TARCUT2, FSAVINCR, PWMINCR, and DEVAL. DEVAL in particular changes the price anchor and exchange-rate/foreign-saving closure; TARCUT2 changes the government-saving/direct-tax-adjustment closure.

## Case 5 — exogenous/endogenous swaps

GAMS/GEMPACK practitioners commonly change closure by swapping which quantities are exogenous and endogenous. The current Hosoe Pyomo definitions encode some exogenous quantities as `Param`, so they cannot simply be `unfix()`ed. v0.6 documents this boundary rather than rewriting the model definitions.

## Extraction rule

Create a shared closure abstraction only when a second backend adapter is actually implemented and these concrete cases can drive the interface from evidence rather than anticipation.
