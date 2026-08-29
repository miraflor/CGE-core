# Tariff reform

Consider abolition of the import tariff on `BRD`.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("Abolish BRD tariff")
reform.tariff("BRD", 0)

result = reform.solve()
comparison = result.compare(base)
```

The direct policy change is only the tariff. The economic result is broader.

A lower tariff changes the tariff-inclusive import price. Through the Armington structure,
users of the composite good may substitute between imports and domestic supply. Producers,
factor markets, household income and demand, government revenue, investment demand, trade,
and the exchange rate then adjust together.

Useful quantities to inspect include:

```python
for component in ["M", "D", "Q", "Z", "pq", "pm", "epsilon"]:
    print(component, base.value(component, "BRD"), result.value(component, "BRD"))
```

For a proportional tariff cut instead of abolition:

```python
half_tariff = base.scenario("Half tariff")
half_tariff.tariff("BRD", change=-0.50)
half_result = half_tariff.solve()
```

The percentage is applied to the benchmark rate, not interpreted as percentage points.
