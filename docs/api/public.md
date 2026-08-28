# Public CGE API

For the Hosoe simple and standard models, this is the canonical v0.6 workflow
surface.

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

model = CGE(model=StdCGE(), data=example_data("stdcge"))
benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

scenario = benchmark.scenario("tariff abolition")
scenario.set("taum", "BRD", 0.0)
result = scenario.solve()

comparison = result.compare(benchmark)
```

## `CGE`

`CGE` is a configured, stateless blueprint. It owns the model definition and
data location, but not a solved equilibrium. Each `solve_benchmark()` call
creates a fresh lower-level backend.

```{eval-rst}
.. autoclass:: cge_core.api.CGE
   :members:
```

The `numeraire=` and `redundant=` keyword arguments are the explicit closure
spelling for the engine-backed Hosoe family. They are **not** a promised
universal closure API for every current or future CGE backend.

## `Equilibrium`

`Equilibrium` is the protected solved benchmark returned by
`solve_benchmark()`. Public reads use an immutable numerical snapshot.

```{eval-rst}
.. autoclass:: cge_core.api.Equilibrium
   :members:
```

Creating a scenario makes an independent copy of the calibrated backend, so
multiple scenarios can coexist without overwriting each other.

## `Scenario`

`Scenario` is the mutable counterfactual object.

```{eval-rst}
.. autoclass:: cge_core.api.Scenario
   :members:
```

`set()` can change a mutable model parameter. When used on a variable it sets
and fixes that variable in the scenario. `unfix()` only releases a variable
that was previously fixed by `set()` in the **same** scenario; it does not turn
an exogenous `Param` into an endogenous variable and it is not a general
closure-swapping mechanism.

## `Result`

`Result` is an immutable numerical snapshot of one successfully solved state.

```{eval-rst}
.. autoclass:: cge_core.api.Result
   :members:
```

`Result.compare(reference)` accepts a compatible `Equilibrium` or another
`Result`. The direction is always `self - reference`. A zero reference value
produces `NaN` for percentage change rather than an infinite percentage.

## Model boundary

This façade currently targets the validated engine-backed Hosoe models. The
IFPRI subsystem keeps its dedicated closure/scenario API, and CAMCGE remains a
repository-level replication benchmark. See {doc}`ifpri` and
{doc}`../models/camcge`.

For direct access to the lower-level Hosoe engine state machine and Pyomo
objects, see {doc}`engine` and {doc}`../workflow`.
