# Developer reference

CGE-Core's source tree is organized around the concepts a modeller actually
needs to understand.

```text
cge_core/
├── workflow.py          benchmark → scenario → result lifecycle
├── _engine.py           model-declared engine policy
├── _pycge.py            inherited lower-level PyCGE engine
├── solver.py            numerical-backend resolution
├── sam.py               social-accounting-matrix tools
├── models/              bundled economic model families
│   ├── simple/
│   ├── standard/
│   ├── camcge/
│   └── ifpri/
└── experimental/        optional authoring and .cge.md work
```

## Where to make a change

- **Economic equations or calibration:** `cge_core/models/<family>/`.
- **Benchmark/scenario/result behavior:** `cge_core/workflow.py`.
- **Solver detection and automatic setup:** `cge_core/solver.py`.
- **SAM conversion and validation:** `cge_core/sam.py`.
- **Function-based or `.cge.md` authoring:** `cge_core/experimental/`.
- **Lower-level PyCGE engine:** `cge_core/_pycge.py`.

Historical redirect modules are intentionally absent in v0.8. Migration paths are
documented in `migration-v0.8.md` rather than duplicated as executable modules.

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
