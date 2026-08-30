# Extension Contract

This page defines the **small public contract** that downstream scientific
packages may rely on when they use CGE-Core's engine-backed Hosoe models.

The purpose is stability, not extensibility for its own sake. CGE-Core does
not promise a plugin framework or a universal interface for every CGE model.
It promises a narrow equilibrium/scenario lifecycle that can be used without
reaching into the lower-level engine or raw Pyomo state.

## Scope

This extension contract applies to the public Hosoe Simple and Standard
workflow:

```python
from cge_core import CGE, Equilibrium, Scenario, Result, example_data
from cge_core.models import SplCGE, StdCGE
```

The IFPRI subsystem has its own dedicated API and closure machinery. CAMCGE
remains a repository-level replication benchmark. Neither is folded into this
contract.

## Contract at a glance

```text
CGE(model, data)
    |
    +-- solve_benchmark(...)
            |
            v
       Equilibrium
          |  \
          |   +-- value(...)
          |   +-- objective
          |
          +-- scenario(name)
                  |
                  v
              Scenario
                |
                +-- set(...)
                +-- solve(...)
                        |
                        v
                     Result
                       |
                       +-- value(...)
                       +-- objective
                       +-- compare(...)
```

A downstream package should be able to do this repeatedly:

```python
scenario.set("taum", "BRD", 0.0)
first = scenario.solve()

scenario.set("taum", "MLK", 0.0)
second = scenario.solve()
```

`first` remains an immutable snapshot of the first solved state even after the
same `Scenario` is modified and solved again.

## Stable capabilities

### 1. Configure a static CGE blueprint

```python
model = CGE(model=StdCGE(), data=example_data("stdcge"))
```

`CGE` is a stateless configuration object. A solved backend belongs to the
`Equilibrium` returned by `solve_benchmark()`, not to the blueprint itself.

### 2. Solve a benchmark equilibrium

```python
benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

For the Hosoe engine-backed models, `numeraire=` and `redundant=` are the
explicit structural closure spelling. This is a Hosoe-family contract, not a
universal closure abstraction.

### 3. Read the benchmark without raw Pyomo access

```python
wage = benchmark.value("pf", "LAB")
utility = benchmark.objective
```

`value()` is the stable read path for variables and parameters exposed by the
solved model snapshot.

### 4. Create an isolated counterfactual

```python
scenario = benchmark.scenario("tariff reform")
```

A `Scenario` owns independent mutable state. Creating or modifying a scenario
does not mutate the benchmark, and multiple scenarios may coexist.

### 5. Set admissible scenario values

```python
scenario.set("taum", "BRD", 0.0)
```

For a mutable `Param`, `set()` changes the scenario value. For a `Var`, it
sets and fixes that variable in the scenario. Whether a component is
economically appropriate to shock remains the responsibility of the model
definition and the researcher.

### 6. Solve, read, modify, and solve again

```python
result1 = scenario.solve()
x1 = result1.value("Z", "BRD")

scenario.set("taum", "MLK", 0.0)
result2 = scenario.solve()
x2 = result2.value("Z", "BRD")
```

Repeated `set()` -> `solve()` cycles are part of the contract. Previously
returned `Result` objects remain unchanged.

### 7. Compare solved states

```python
changes = result2.compare(benchmark)
```

`Result.compare(reference)` accepts a compatible `Equilibrium` or `Result`.
The direction is always:

```text
current result - reference
```

The comparison table includes component/index columns plus reference value,
current value, difference, and percentage change. Percentage change is `NaN`
when the reference value is zero. Objective comparison metadata is stored in
`DataFrame.attrs["objective"]`.

## Public boundary

Downstream packages should depend on the public surface, not the implementation
used to realize it.

| Supported dependency | Status |
|---|---|
| `cge_core.CGE` | extension contract |
| `cge_core.Equilibrium` | extension contract |
| `cge_core.Scenario` | extension contract |
| `cge_core.Result` | extension contract |
| `cge_core.example_data` | supported public helper |
| `cge_core.models.SplCGE` | supported public model import |
| `cge_core.models.StdCGE` | supported public model import |
| `cge_core._pycge.PyCGE` | advanced/lower-level API; not this contract |
| `Equilibrium._engine` | private implementation detail |
| `Result._snapshot` | private implementation detail |
| raw Pyomo objects reached through private state | private implementation detail |

The lower-level `PyCGE` API remains supported for advanced users, but
a downstream package that chooses to depend on its mutable `base`/`sim` state
machine is intentionally outside this extension-stability promise.

## Deliberate exclusions

The minimal contract does **not** include:

- a universal `Closure` object;
- arbitrary backend/plugin registration;
- direct access to the private engine;
- raw Pyomo traversal as a stable interface;
- persistence or serialization guarantees;
- `Scenario.unfix()` as a required downstream capability;
- IFPRI or CAMCGE being adapted to the Hosoe facade;
- dynamic transition equations or time-stepping logic.

`Scenario.unfix()` is public and documented for ordinary use, but the minimal
downstream contract does not require it. Making an exogenous parameter
endogenous is a model-definition or closure change, not a generic scenario
operation.

## Why the contract is narrow

A narrow contract lets another package orchestrate CGE-Core without knowing
how the current engine stores `base`, `sim`, Pyomo components, solver results,
or calibration state. That is enough for downstream static-equilibrium
composition, including future packages that may coordinate repeated
equilibrium solves.

Regression tests treat this lifecycle as a public behavioral
requirement. Internal cleanup may change how the capability is implemented,
but should not silently remove the documented behavior.
