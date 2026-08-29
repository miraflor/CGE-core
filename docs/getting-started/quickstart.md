# Quickstart

Solve the bundled Standard CGE benchmark:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
base.summary()
```

Create a tariff-reform counterfactual:

```python
reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)

result = reform.solve()
result.compare(base)
```

That is the complete ordinary lifecycle.

The benchmark is protected. `scenario(...)` creates an independent counterfactual model.
The tariff helper changes the economic policy variable, and `solve()` finds the new
general-equilibrium solution.

To inspect one value:

```python
base.value("M", "BRD")
result.value("M", "BRD")
```

For lower-level Pyomo inspection, use `.raw` deliberately rather than making it part of
ordinary application code.
