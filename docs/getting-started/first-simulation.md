# Your First Policy Simulation

A static CGE policy experiment compares two internally consistent equilibria:

1. the **benchmark equilibrium**, calibrated to reproduce benchmark data; and
2. a **counterfactual equilibrium**, solved after changing an exogenous
   parameter or endowment.

CGE-Core calls the SAM-replicating static reference state the **benchmark**.
This avoids overloading *baseline*, which is often used for a time path in
dynamic models.

Consider the standard model's import tariff parameter, `taum`.

## Solve the benchmark

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

`CGE` is a stateless blueprint. Every call to `solve_benchmark()` constructs and
solves a fresh backend, so solved benchmarks do not compete for one mutable
simulation slot.

At this point CGE-Core has recovered the calibrated model state needed to
reproduce the benchmark equilibrium. Public reads use the protected numerical
snapshot:

```python
print(benchmark.value("Z", "BRD"))
print(benchmark.value("pf", "LAB"))
print(benchmark.objective)
```

## Create the counterfactual

```python
scenario = benchmark.scenario("bread tariff abolition")
scenario.set("taum", "BRD", 0.0)
result = scenario.solve()
```

The scenario owns an independent copy of the calibrated backend. The shock
sets the bread import tariff to zero in that scenario while leaving the
benchmark protected and available for other scenarios.

You can therefore branch more than one experiment from the same benchmark:

```python
tariff = benchmark.scenario("tariff abolition")
tariff.set("taum", "BRD", 0.0)

tax = benchmark.scenario("production-tax abolition")
tax.set("tauz", "BRD", 0.0)

result_tariff = tariff.solve()
result_tax = tax.solve()
```

## Compare immutable results

```python
comparison = result.compare(benchmark)

print(comparison)
print(comparison.attrs["objective"])
```

The returned `Result` is an immutable numerical snapshot: later scenario edits
or solves do not retroactively change an earlier result. You can also compare one compatible
`Result` with another.

## What changed economically?

Removing a tariff directly changes the domestic price wedge on imports. The
model then re-solves **all markets simultaneously**: import demand, domestic
production, factor demand, household demand, government revenue, saving,
investment and trade adjust until a new equilibrium is reached.

That general-equilibrium feedback is the central reason to use a CGE model
rather than applying the tariff change to one equation in isolation.

For the trade equations, see {doc}`../theory/trade`. For the public object
reference, see {doc}`../api/public`. For the underlying `PyCGE` engine workflow,
see {doc}`../workflow`.
