# Standard CGE

The Standard CGE adds intermediate inputs, government, saving and investment, imports,
exports, Armington aggregation, and CET transformation.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

Model-specific helpers make common policy experiments explicit:

```python
scenario = base.scenario("Policy package")
scenario.tariff("BRD", change=-0.50)
scenario.production_tax("MLK", 0.05)
scenario.endowment("CAP", change=0.10)
result = scenario.solve()
```

For advanced components without a semantic helper, `Scenario.set()` remains available.

A balanced SAM can be supplied with `StandardCGE.from_sam(...)`; see
{doc}`../tutorials/loading-sam`.
