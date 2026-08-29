# IFPRI Standard CGE

The IFPRI implementation remains a separate model family with richer institutions and
explicit macro-closure logic.

For public tutorials and CI, use the independently authored synthetic dataset:

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()
result = base.scenario("TARCUT1").solve()
result.compare(base)
```

The bundled public path deliberately exposes the validated named scenarios rather than
pretending that IFPRI closure changes are interchangeable with the Hosoe `Scenario.set()`
interface.

Official-source replication is a separate evidence lane. See {doc}`../ifpri_cleanroom`
and {doc}`../IFPRI`.
