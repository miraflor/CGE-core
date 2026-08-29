# CGE-Core 0.7

CGE-Core is a computable general equilibrium modelling system built around a simple product rule:

> **You specify economics; CGE-Core handles computational plumbing.**

The first public path is intentionally short:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
policy = base.scenario("Tariff reform")
policy.tariff("BRD", change=-0.50)
result = policy.solve()
result.compare(base)
```

This convenience does not remove economic transparency. The model's closure, shocks, raw Pyomo representation, solver status, and validation provenance remain inspectable.

## Choose your path

- **New practitioner or learner:** read [Your first CGE](first_cge.md), then [Policy experiments](policy_experiments.md).
- **Using your own data:** read [Bring your own SAM](own_sam.md).
- **Choosing a bundled model:** read [Bundled models](bundled_models.md).
- **Building a model:** read [Build a model in Python](authoring_python.md) or [Experimental `.cge.md`](cge_md.md).
- **Framework/advanced work:** read [Advanced and internals](advanced.md).
- **Scientific claims:** read [Validation and provenance](validation.md).
