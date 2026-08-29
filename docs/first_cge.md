# Your first CGE

A CGE model describes an economy as a simultaneous system: production, household demand, trade, taxes, factor markets, commodity markets, and accounting identities must all be mutually consistent.

CGE-Core's `StandardCGE` bundles the small open-economy model commonly associated with Hosoe, Gasawa and Hashimoto.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
base.summary()
```

You did **not** specify a numeraire or tell CGE-Core which redundant market equation to drop. Those choices are part of this bundled model's declared canonical closure.

You can still inspect the closure:

```python
base.closure
```

and inspect any solved quantity:

```python
base.value("Z", "BRD")      # gross output
base.value("pq", "BRD")     # composite-good price
base.value("pf", "LAB")     # labor-factor price / numeraire
```

Advanced users can reach the Pyomo model with `base.raw`.
