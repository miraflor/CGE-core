# Five-Minute Quick Start

This example solves the standard Hosoe model, removes one import tariff, and
compares the counterfactual with the solved benchmark equilibrium.

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

# 1. Configure a static CGE model blueprint.
model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

# 2. Solve the SAM-replicating benchmark equilibrium.
benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

# 3. Create an independent counterfactual from the benchmark.
scenario = benchmark.scenario("bread tariff abolition")
scenario.set("taum", "BRD", 0.0)

# 4. Solve and compare.
result = scenario.solve()
comparison = result.compare(benchmark)

print("Benchmark welfare:", benchmark.objective)
print("Scenario welfare:", result.objective)
print(comparison)
```

The workflow is:

```text
model + data
    ↓
solve benchmark
    ↓
protected Equilibrium
    ↓
independent Scenario
    ↓
policy shock
    ↓
immutable Result
    ↓
comparison
```

Differences returned by `result.compare(reference)` are always **result minus
reference**. Percentage changes are `(result - reference) / reference × 100`;
when the reference value is zero, the percentage change is `NaN`.

```{admonition} Coming from GAMS?
:class: tip

A rough workflow crosswalk is: choose the model and benchmark data → solve the
benchmark → change an exogenous parameter → solve the counterfactual → inspect
levels and changes. CGE-Core expresses those steps as `CGE`,
`solve_benchmark()`, `Scenario.set()`, `Scenario.solve()`, and `Result`.

This is a workflow analogy, not a claim that the Python object model is a
one-to-one translation of GAMS. See {doc}`../GAMS_CROSSWALK` for the fuller
crosswalk.
```

Next: {doc}`first-simulation`.
