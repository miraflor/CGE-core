# Closure, Numeraire and Walras' Law

A CGE model needs a **closure**: a statement of which variables are endogenous, which are fixed, and which equation determines each endogenous variable.

## Numeraire

Only relative prices matter in the model, so one price must be fixed as the numeraire.

The standard CGE example uses:

```python
cge.model_instance("pf", "LAB")
```

which fixes the labour-factor price.

## Walras' law

One market-clearing equation is redundant. If all other markets clear and every agent satisfies its budget constraint, the remaining market clears automatically.

After the numeraire is fixed, the raw standard-model system has one too many equality constraints. CGE-Core therefore explicitly deactivates one market-clearing equation:

```python
cge.model_drop_redundant("eqpf", "LAB")
```

This makes the nonlinear system square for IPOPT.

The dropped market is not ignored economically: it should still clear at the solution. CGE-Core's regression tests check this consistency condition.

For the scalar degree-of-freedom count and implementation details, see {doc}`../MODEL`.
