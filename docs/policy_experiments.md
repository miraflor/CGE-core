# Run a policy experiment

CGE analysis is comparative equilibrium analysis: solve the benchmark, change an exogenous policy or resource, solve the counterfactual, then compare.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("50% tariff cut")
reform.tariff("BRD", change=-0.50)
result = reform.solve()

result.compare(base)
```

## Level versus relative change

Set the new tariff rate directly:

```python
reform.tariff("BRD", 0.05)
```

or change the existing rate proportionally:

```python
reform.tariff("BRD", change=-0.50)
```

Other StandardCGE helpers are deliberately thin:

```python
reform.production_tax("MLK", 0.02)
reform.endowment("CAP", change=0.10)
```

For an internal parameter with no semantic helper:

```python
reform.set("taum", "BRD", 0)
```

A scenario owns one independent clone. It cannot mutate the benchmark or a sibling scenario.
