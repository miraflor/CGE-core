# Your first policy simulation

A CGE counterfactual asks:

> If the exogenous policy or environment changed, what internally consistent equilibrium
> would satisfy the model afterward?

Start from a solved benchmark:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

Create an independent scenario and change an economic assumption:

```python
policy = base.scenario("Tariff cut")
policy.tariff("BRD", change=-0.50)
```

`change=-0.50` means “reduce the existing tariff rate by 50 percent.” It does not mean
“subtract 50 percentage points.”

Solve the new equilibrium:

```python
result = policy.solve()
```

Compare all endogenous variables with the benchmark:

```python
comparison = result.compare(base)
comparison
```

The resulting differences reflect **all model adjustments together**: domestic and import
prices, production, trade, factor allocation, income, demand, saving, and other endogenous
quantities respond jointly.

For a second independent experiment:

```python
factor_case = base.scenario("More capital")
factor_case.endowment("CAP", change=0.10)
factor_result = factor_case.solve()
```

The two scenarios do not share mutable counterfactual state.
