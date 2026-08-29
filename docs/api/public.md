# Public modelling API

## Bundled model entry points

```python
from cge_core import SimpleCGE, StandardCGE, CamCGE, IFPRICGE
```

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

## Equilibrium

A solved benchmark supports:

- `summary()`
- `value(component, *index)`
- `scenario(name)`
- `.raw` as an advanced escape hatch
- `.closure` for model-owned closure information

## Scenario

The Hosoe/CAMCGE scenario object supports:

- `set(component, index, new_value)`
- `undo(component, index=None)`
- `tariff(good, value=None, change=None)` where declared by the model
- `production_tax(good, value=None, change=None)` where declared by the model
- `endowment(factor, value=None, change=None)` where declared by the model
- `solve()`

A scenario is an independent mutable counterfactual derived from a protected benchmark.

## Result

A solved result supports:

- `summary()`
- `value(component, *index)`
- `compare(reference)`
- `.raw` for advanced model inspection

Ordinary numerical reads come from the result snapshot, not from later mutation of a live
Pyomo object.

## v0.6 compatibility lifecycle

The lower-level public lifecycle remains available:

```python
from cge_core import CGE
```

`CGE → Equilibrium → Scenario → Result` is retained for downstream and advanced code.
The v0.7 façades configure this lifecycle for bundled models so ordinary users do not have
to supply closure and solver plumbing themselves.
