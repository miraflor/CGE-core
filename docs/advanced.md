# Advanced and internals

Most policy users should not need this page.

## Raw Pyomo access

High-level states expose their underlying model for inspection:

```python
base.raw
result.raw
```

Use `value()`, `summary()` and `compare()` for stable downstream reads; use `raw` when you intentionally need model-level inspection.

## Retained lower-level API

```python
from cge_core import CGE, PyCGE, example_data
from cge_core.models import StdCGE
```

For SimpleCGE, StandardCGE, and CamCGE, the generic `CGE → Equilibrium → Scenario → Result` workflow sits above `CoreEngine`, which in turn subclasses the retained `PyCGE` engine. These layers remain escape hatches for debugging, validation, and engine development.

IFPRI has its own advanced API under `cge_core.models.ifpri`; it shares the Pyomo/solver boundary without being routed through `CoreEngine`.

New tutorials use the model façades instead.

## Solver override

Ordinary use is simply:

```python
base = StandardCGE.example().solve()
```

An advanced reproducibility run may request a backend explicitly:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

Use `cge doctor` to inspect what CGE-Core detects.

## Why the public layer exists

The public API encodes recurring software decisions—model construction, model-owned closure, counterfactual isolation, result inspection and solver selection—so practitioner code can expose the economic decisions instead of repeating framework plumbing. The implementation is allowed to differ by model family when those differences are economically meaningful.
