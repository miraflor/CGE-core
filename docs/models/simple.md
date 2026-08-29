# Simple CGE

The Simple CGE is the smallest bundled Hosoe teaching economy: goods, primary factors,
firms, and a representative household, without government or foreign trade.

```python
from cge_core import SimpleCGE

base = SimpleCGE.example().solve()

case = base.scenario("More labor")
case.endowment("LAB", change=0.10)
result = case.solve()

result.compare(base)
```

Use it to learn price adjustment, factor allocation, production, consumption, and welfare
without the additional trade and fiscal blocks of the Standard CGE.
