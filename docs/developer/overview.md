# Developer reference

CGE-Core v0.8 is organized around **two bundled execution paths** that share a numerical
boundary but do not pretend to be one implementation.

```text
cge_core/
├── workflow.py          generic CGE → Equilibrium → Scenario → Result lifecycle
├── model_spec.py        model-owned closure/protection/semantic metadata
├── _engine.py           small ModelSpec-driven policy adapter over PyCGE
├── _pycge.py            retained lower-level PyCGE engine mechanics
├── _shared.py           shared comparison/index/rollback helpers
├── solver.py            centralized numerical-backend resolution
├── sam.py               social-accounting-matrix tools
├── models/
│   ├── _accounts.py     shared model-account validation helpers
│   ├── simple/          Hosoe Simple CGE
│   ├── standard/        Hosoe Standard CGE
│   ├── camcge/          CAMCGE implementation and packaged data
│   └── ifpri/           IFPRI-specific calibration, closure, scenarios and reporting
└── experimental/
    ├── authoring/       functional Python model adapter
    └── spec/            deterministic .cge.md parser/compiler
```

## Two bundled execution paths

### SimpleCGE / StandardCGE / CamCGE

These façades configure the generic scientific lifecycle:

```text
model definition + ModelSpec
            ↓
CGE → Equilibrium → Scenario → Result
            ↓
         CoreEngine
            ↓
           PyCGE
            ↓
           Pyomo
```

`CoreEngine` deliberately contains little mechanics of its own. It subclasses `PyCGE` and
uses `ModelSpec` to replace historical name-based protection rules with explicit model-owned
policy.

### IFPRICGE

IFPRI retains its own calibrated execution path:

```text
IFPRICGE
   ↓
IFPRI calibration / closure / named scenarios
   ↓
IFPRIEquilibrium → IFPRIScenario → IFPRIResult
   ↓
Pyomo
```

This is intentional. IFPRI shares practitioner semantics and solver policy with the other
families, but its richer institutional model and validation machinery do not need to be
forced through `CoreEngine` merely for file-level symmetry.

Both paths use `cge_core.solver` to resolve a supported nonlinear backend.

## Where to make a change

- **Hosoe/CAMCGE equations or calibration:** `cge_core/models/<family>/`.
- **Generic benchmark/scenario/result behavior:** `cge_core/workflow.py`.
- **Generic model policy and closure metadata:** `cge_core/model_spec.py`.
- **Model-protection policy adapter:** `cge_core/_engine.py`.
- **Lower-level PyCGE mechanics:** `cge_core/_pycge.py`.
- **IFPRI calibration, closure, scenarios, solve/reporting:** `cge_core/models/ifpri/`.
- **Solver detection and first-use setup:** `cge_core/solver.py`.
- **SAM conversion and validation:** `cge_core/sam.py`.
- **Function-based or `.cge.md` authoring:** `cge_core/experimental/`.

Historical redirect modules are intentionally absent in v0.8. Migration paths are
documented in {doc}`../migration-v0.8` rather than duplicated as executable modules.

The model families share a home and a practitioner vocabulary, not ceremonial file
symmetry. Simple CGE stays simple; IFPRI keeps the extra modules its economics and
validation genuinely require.

The ordinary interface remains:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
scenario = base.scenario("Tariff abolition")
scenario.tariff("BRD", 0)
result = scenario.solve()
result.compare(base)
```

The v0.8 architectural cleanup does not intentionally alter equations, calibration rules,
closures, data, or numerical validation targets.
