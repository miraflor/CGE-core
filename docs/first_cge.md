# Your first CGE

A computable general equilibrium model is a simultaneous system. Production, household demand, intermediate input demand, trade, taxes, saving, factor markets, commodity markets, and accounting identities must be mutually consistent at one set of prices and quantities.

The bundled `StandardCGE` is the small open-economy model associated with Hosoe, Gasawa and Hashimoto.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
base.summary()
```

## What the benchmark means

The benchmark is the equilibrium to which the model is calibrated. It is not a forecast. The SAM supplies the observed base-year accounting flows; calibration recovers the parameters that make those flows satisfy the model at the benchmark.

Read quantities and prices directly:

```python
base.value("Z", "BRD")      # gross output
base.value("M", "BRD")      # imports
base.value("E", "BRD")      # exports
base.value("Xp", "BRD")     # household consumption
base.value("pq", "BRD")     # composite-good price
base.value("pf", "LAB")     # labor-factor price / numeraire
```

## Closure is part of the model

A CGE needs a numeraire price and, because of Walras' law, one redundant market-clearing condition is omitted. In v0.8.0 the bundled model declares its canonical closure, so the learner does not have to remember engine calls simply to get started.

```python
base.closure
```

That convenience does not make closure irrelevant. It makes it explicit model metadata that can be inspected and documented.

## The next step

A policy experiment starts from this protected benchmark, creates an independent scenario, changes an admissible exogenous assumption, solves the full system again, and compares the new equilibrium with the benchmark.
