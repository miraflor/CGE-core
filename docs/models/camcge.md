# CAMCGE

CAMCGE is the published Cameroon model replication used as an independent historical
validation benchmark.

v0.8 keeps it as a first-class installed model:

```python
from cge_core import CamCGE

base = CamCGE.example().solve()

windfall = base.scenario("Oil windfall")
windfall.set("fsav", None, 500)
result = windfall.solve()
```

Its equations and closure remain CAMCGE-specific. The façade is a usability layer, not a
rewrite into the Hosoe model.

See `CAMCGE_REPLICATION_GUIDE.md` and `CAMCGE_VALIDATION_REPORT.md` in the repository root.
