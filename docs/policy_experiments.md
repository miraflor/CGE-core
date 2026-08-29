# Run a policy experiment

CGE analysis is comparative equilibrium analysis:

1. solve the benchmark;
2. create an independent scenario;
3. change an exogenous policy/resource/world assumption;
4. solve the whole economy again;
5. compare the counterfactual with the benchmark.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("50% tariff cut")
reform.tariff("BRD", change=-0.50)
result = reform.solve()

result.compare(base)
```

## Level versus relative change

Set a new tariff **level**:

```python
reform.tariff("BRD", 0.05)       # exactly 5%
```

or change the existing rate **proportionally**:

```python
reform.tariff("BRD", change=-0.50)  # cut the existing rate in half
```

Other Standard-CGE semantic helpers include:

```python
reform.production_tax("MLK", 0.02)
reform.endowment("CAP", change=0.10)
```

For a model-specific component with no semantic helper:

```python
reform.set("taum", "BRD", 0.0)
```

A scenario owns independent mutable state. It does not rewrite the benchmark or a sibling scenario, and a solved `Result` is a numerical snapshot rather than a live pointer to later edits.

## Interpretation

A shock is an assumption, not the result. Abolishing a tariff does not mean “imports rise by X%” because you typed X somewhere. The model determines the new imports, domestic production, prices, factor allocation, tax revenue, consumption, saving, investment and trade balance jointly.
