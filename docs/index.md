# CGE-Core 0.7.0

> **You specify economics; CGE-Core handles routine computational plumbing.**

CGE-Core 0.7.0 puts a practitioner-facing layer around validated model implementations while keeping the underlying equations, closures, and provenance inspectable.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
reform = base.scenario("Tariff reform")
reform.tariff("BRD", change=-0.50)
result = reform.solve()
result.compare(base)
```

## Start here

- **Interactive:** [CGE-Core Control Room](control-room/)
- **Notebook:** [01 — Your first CGE](notebooks/01_first_cge.ipynb)
- **Tutorial:** [Your first CGE](first_cge.md)
- **Policy experiments:** [Run a policy experiment](policy_experiments.md)
- **Own data:** [Bring your own SAM](own_sam.md)
- **Bundled models:** [Choose a bundled model](bundled_models.md)
- **IFPRI clean-room boundary:** [Public vs official-source evidence](ifpri_cleanroom.md)
- **Model authoring:** [Functional Python](authoring_python.md) and [experimental `.cge.md`](cge_md.md)
- **Scientific claims:** [Validation and provenance](validation.md)
- **Advanced:** [Internals and lower-level API](advanced.md)

The convenience layer does not make closure or model structure disappear; it moves routine software setup out of the policy notebook so users can focus on what is exogenous, what is endogenous, what closure is being used, and what the counterfactual means.
