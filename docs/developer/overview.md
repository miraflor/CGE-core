# Developer reference

CGE-Core's source tree is organized around the concepts a modeller actually
needs to understand.

```text
cge_core/
├── workflow.py          benchmark → scenario → result lifecycle
├── solver.py            hidden numerical-backend resolution
├── sam.py               social-accounting-matrix tools
├── models/              bundled economic model families
│   ├── simple/
│   ├── standard/
│   ├── camcge/
│   └── ifpri/
├── experimental/        optional authoring and .cge.md work
└── compat/              retained lower-level PyCGE implementation
```

## Where to make a change

- **Economic equations or calibration:** `cge_core/models/<family>/`.
- **Benchmark/scenario/result behavior:** `cge_core/workflow.py`.
- **Solver detection and automatic setup:** `cge_core/solver.py`.
- **SAM conversion and validation:** `cge_core/sam.py`.
- **Function-based or `.cge.md` authoring:** `cge_core/experimental/`.
- **Historical PyCGE compatibility:** `cge_core/compat/`.

Compatibility modules remain intentionally tiny so existing v0.6/v0.7 imports
do not break. They are not parallel implementations.

The model families share a home and a public lifecycle, not ceremonial file
symmetry. Simple CGE stays simple; IFPRI keeps the extra modules its economics
and validation genuinely require.

The ordinary interface remains:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
scenario = base.scenario("Tariff abolition")
scenario.tariff("BRD", 0)
result = scenario.solve()
result.compare(base)
```

This cleanup does not alter equations, calibration rules, closures, data, or
numerical validation targets.
