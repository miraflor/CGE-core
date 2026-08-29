# Advanced and internals

Most users should stop before this page.

## Raw Pyomo

High-level states expose a raw model:

```python
base.raw
result.raw
```

Snapshot-based `value()` and `compare()` remain stable even if an advanced user later inspects or mutates a raw object.

## v0.6 compatibility

The lower-level lifecycle remains available:

```python
from cge_core import CGE, PyCGE, example_data
from cge_core.models import StdCGE

model = CGE(model=StdCGE(), data=example_data("stdcge"))
base = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

The direct `PyCGE` engine remains the escape hatch for framework development and older code.

## Solver override

Ordinary use is `.solve()`. For reproducibility experiments:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

Use `cge doctor` to inspect the detected backend.

## Why two engine layers?

v0.7 deliberately does not rewrite the validated lower-level engine in one risky diff. The new public engine adapter adds explicit metadata and centralized solver selection while preserving the v0.6 `PyCGE` surface. This allows gradual deprecation/refactoring without mixing software architecture changes with economic equation changes.
