# Modelling workflow

## Practitioner workflow

All bundled families expose the same modelling idea:

```text
choose a model
    ↓
solve benchmark
    ↓
create policy scenario
    ↓
apply economic shock / named scenario
    ↓
solve counterfactual
    ↓
inspect and compare results
```

For the Hosoe Simple, Hosoe Standard, and CAMCGE families this is implemented by the generic
v0.8 workflow:

```text
model façade
    ↓
protected Equilibrium
    ↓
independent Scenario
    ↓
Result snapshot
```

Example:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

scenario = base.scenario("Tariff cut")
scenario.tariff("BRD", change=-0.50)

result = scenario.solve()
result.compare(base)
```

IFPRI keeps the same practitioner sequence through model-specific types and named scenarios:

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()
result = base.scenario("TARCUT1").solve()
```

Internally this path uses `IFPRIEquilibrium`, `IFPRIScenario`, and `IFPRIResult` plus the
IFPRI calibration and closure machinery. It is intentionally separate from the generic
`CGE` / `CoreEngine` path.

## Why solve the benchmark first?

Calibration reconstructs model parameters and verifies that the benchmark data are
consistent with the model's equilibrium structure. The benchmark is therefore the reference
state against which a counterfactual is interpreted.

## Why is a generic scenario a clone?

For SimpleCGE, StandardCGE, and CamCGE, a policy experiment must not mutate the benchmark or
another policy experiment. v0.8 therefore creates one independent concrete model clone per
generic scenario. Multiple counterfactuals can coexist.

IFPRI instead constructs its named scenario model through the IFPRI-specific scenario
builder using the benchmark dataset and calibration. The user-facing economic idea is the
same even though the internal mechanism differs.

## Closure

Closure is model-owned, not a universal framework default.

- SimpleCGE, StandardCGE, and CamCGE declare canonical closure metadata through their model
  configuration and `ModelSpec`.
- IFPRICGE retains IFPRI-specific macro closure and named scenario machinery.

This removes routine numeraire and redundant-equation bookkeeping from ordinary user code
without pretending closure is economically unimportant.

Advanced users can still work through lower-level or model-specific APIs when closure itself
is the object of research.

## Results

For the generic Simple/Standard/CAMCGE path, `Result` is an immutable numerical snapshot of
a successful solve. Use `value()`, `summary()`, and `compare()` for ordinary analysis.
`.raw` is available when direct Pyomo access is genuinely needed.

IFPRI provides corresponding `IFPRIResult` methods over its model-specific solved state.
