# Tutorial: Remove an Import Tariff

This is the smallest complete policy experiment in CGE-Core.

## 1. Solve the benchmark

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

The benchmark is the SAM-replicating static reference equilibrium.

## 2. Create a scenario

```python
scenario = benchmark.scenario("remove bread tariff")
```

A scenario starts from an independent copy of the solved benchmark, so changes
to it do not mutate the benchmark.

## 3. Remove the bread tariff

```python
scenario.set("taum", "BRD", 0.0)
```

## 4. Solve

```python
result = scenario.solve()
```

## 5. Compare with the benchmark

```python
frame = result.compare(benchmark)
print(frame)
```

The tariff shock changes one parameter, but the counterfactual solution changes
every endogenous variable required to restore general equilibrium.

To remove both benchmark import tariffs, branch a fresh scenario from the same
benchmark:

```python
both = benchmark.scenario("remove both tariffs")
both.set("taum", "BRD", 0.0)
both.set("taum", "MLK", 0.0)
both_result = both.solve()

print(both_result.compare(benchmark))
```

The two scenarios are independent and can remain live at the same time.
