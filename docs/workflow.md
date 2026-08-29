# Modelling workflow

## Practitioner workflow

```text
model façade
    ↓
solve benchmark
    ↓
protected Equilibrium
    ↓
independent Scenario
    ↓
economic shock
    ↓
solve counterfactual
    ↓
Result
    ↓
compare with benchmark
```

Example:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

scenario = base.scenario("Tariff cut")
scenario.tariff("BRD", change=-0.50)

result = scenario.solve()
result.compare(base)
```

## Why solve the benchmark first?

Calibration reconstructs model parameters and verifies that the benchmark data are
consistent with the model's equilibrium structure. The benchmark is therefore the reference
state against which a counterfactual is interpreted.

## Why is a scenario a clone?

A policy experiment must not mutate the benchmark or another policy experiment. v0.7 creates
one independent concrete model clone per scenario. Multiple counterfactuals can therefore
coexist.

## Closure

Bundled model façades own their canonical closure. This removes routine numeraire and
redundant-equation bookkeeping from ordinary user code without pretending closure is
economically unimportant.

Advanced users can still work through the lower-level API when the closure itself is the
object of research.

## Results

`Result` is a numerical snapshot of a successful solve. Use `value()`, `summary()`, and
`compare()` for ordinary analysis. `.raw` is available when direct Pyomo access is genuinely
needed.
