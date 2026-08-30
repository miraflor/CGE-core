# Public modelling API

## Bundled model entry points

```python
from cge_core import SimpleCGE, StandardCGE, CamCGE, IFPRICGE
```

The four façades share a practitioner vocabulary—solve a benchmark, create a policy
counterfactual, solve again, and inspect results—but they do not all use the same internal
workflow classes.

### SimpleCGE

```python
base = SimpleCGE.example().solve()
scenario = base.scenario("More labor")
scenario.endowment("LAB", change=0.10)
result = scenario.solve()
```

### StandardCGE

```python
base = StandardCGE.example().solve()
scenario = base.scenario("Tariff abolition")
scenario.tariff("BRD", 0)
result = scenario.solve()
```

`StandardCGE.from_sam(...)` constructs the model from one balanced SAM with explicit
economic account roles.

### CamCGE

```python
base = CamCGE.example().solve()
scenario = base.scenario("Oil windfall")
scenario.set("fsav", None, 500)
result = scenario.solve()
```

### IFPRICGE

```python
base = IFPRICGE.synthetic().solve()
result = base.scenario("TARCUT1").solve()
```

IFPRI deliberately uses its own `IFPRIEquilibrium`, `IFPRIScenario`, and `IFPRIResult`
classes because its calibration, macro closure, and named policy experiments are
model-specific.

## Generic Equilibrium

For SimpleCGE, StandardCGE, and CamCGE, a solved benchmark supports:

- `summary()`
- `value(component, *index)`
- `scenario(name)`
- `.raw` as an advanced escape hatch
- `.closure` for model-owned closure information

## Generic Scenario

The Hosoe/CAMCGE scenario object supports:

- `set(component, index, new_value)`
- `undo(component, index=None)`
- `tariff(good, value=None, change=None)` where declared by the model
- `production_tax(good, value=None, change=None)` where declared by the model
- `endowment(factor, value=None, change=None)` where declared by the model
- `solve()`

A generic scenario is an independent mutable clone derived from a protected benchmark.

## Generic Result

A generic solved result supports:

- `summary()`
- `value(component, *index)`
- `compare(reference)`
- `.raw` for advanced model inspection

Ordinary numerical reads come from the result snapshot, not from later mutation of a live
Pyomo object.

## IFPRI result surface

`IFPRIEquilibrium` and `IFPRIResult` provide the corresponding `summary()`, `value()`,
`.raw`, and comparison operations appropriate to the IFPRI implementation. IFPRI scenarios
are named model-specific experiments rather than the generic semantic-shock object.

See {doc}`ifpri` for the advanced IFPRI API.

## Lower-level generic lifecycle

The lower-level generic lifecycle remains available:

```python
from cge_core import CGE
```

`CGE → Equilibrium → Scenario → Result` is retained for downstream and advanced code.
`SimpleCGE`, `StandardCGE`, and `CamCGE` configure this lifecycle so ordinary users do not
have to supply closure and solver plumbing themselves.

`IFPRICGE` intentionally uses its separate IFPRI adapter rather than being forced through
this generic lifecycle.
