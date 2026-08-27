> **COURSE-CORRECTION NOTICE:** This file records the original Phase 1 specification before the final pre-Phase-2 review. `COURSE_CORRECTION_RECONCILIATION.md` and `PHASE_2_ENTRY_DECISIONS.md` govern where they conflict. The principal amendments are: `solve_baseline()` → `solve_benchmark()`; `CGE` is a stateless blueprint whose benchmark solves own fresh backends; `Scenario.unfix()` only releases Vars fixed earlier by the same Scenario; no public `Closure` class is added in v0.6.

# CGE-Core v0.6 Reengineering
## Phase 1 — Public API and Architecture Specification

**Project:** CGE-Core
**Target release:** v0.6
**Phase:** 1 — Specify the public API before implementation
**Specification date:** 27 August 2026
**Behavioral baseline:** `main` at `d4dfa7e881339c2101af17caf617dedeb23a7fd8`

---

# 1. Purpose

Phase 1 converts the findings of Phase 0 into a precise public contract.

This phase answers:

> **What should a user or downstream package be allowed to rely on in CGE-Core v0.6?**

It does **not** rewrite economic equations, migrate notebooks, rename the legacy engine internally, or force IFPRI and CAMCGE into the same implementation.

The central design principle is:

> **Unify the scientific workflow at the public API level while allowing validated model families to remain internally different.**

---

# 2. Phase 1 decisions at a glance

| Question | Decision |
|---|---|
| Canonical main class | `CGE` |
| Is `CGE` an alias for `PyCGE`? | **No** |
| Initial implementation style | Composition over existing `PyCGE` machinery |
| Canonical baseline operation | `solve_baseline()` |
| Use `calibrate()` as the main public solve method? | **No** |
| Baseline object | `Equilibrium` |
| Counterfactual object | `Scenario` |
| Solved counterfactual output | immutable `Result` |
| Multiple simultaneous scenarios | **Required** |
| Result live view of Pyomo state? | **No** |
| Result snapshot immutable? | **Yes** |
| Stable value accessor | `value(component, *index)` |
| Canonical comparison | `result.compare(reference)` |
| Comparison sign | `self - reference` |
| Comparison percentage | `(self-reference)/reference * 100` |
| Percent change when reference is zero | undefined / `NaN` |
| First-class `Closure` class in v0.6? | **No** |
| Baseline closure arguments | explicit `numeraire=` and `redundant=` |
| Scenario can make a variable endogenous? | `scenario.unfix(...)` |
| Scenario shock API | `scenario.set(...)` |
| Public model namespace | `cge_core.models` |
| Canonical Hosoe names | `SplCGE`, `StdCGE` |
| Physically move model-definition files now? | **No** |
| Force IFPRI through the new façade in v0.6? | **No** |
| Preserve `cge_core.ifpri`? | **Yes** |
| Promote CAMCGE into installed package? | **No** |
| Keep `PyCGE` importable in v0.6? | **Yes** |
| Runtime deprecation warning in v0.6? | **No** |
| Canonical docs use `PyCGE`? | **No, except legacy/advanced material** |
| New plugin/factory system? | **No** |
| Public backend protocol? | **Not yet** |
| Stable downstream contract | `solve_baseline → scenario → set/unfix → solve → value/compare → modify → solve again` |

---

# 3. Scope of the new `CGE` façade in v0.6

The new `CGE` façade will initially cover the **engine-backed model-definition architecture** currently used by the Hosoe simple and standard models.

That means v0.6 should make this excellent:

```text
Hosoe model definition
        ↓
CGE
        ↓
solve baseline equilibrium
        ↓
create independent scenario
        ↓
apply shock
        ↓
solve
        ↓
read result
```

The new façade should **not** pretend that IFPRI already uses the same internals.

Therefore:

```text
cge_core.CGE
```

and:

```text
cge_core.ifpri
```

will coexist in v0.6.

This is deliberate, not incomplete architecture.

The common abstraction is the **scientific capability model**, not a forced common implementation.

---

# 4. Canonical v0.6 user experience

The canonical Hosoe standard-model example should look approximately like this:

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

baseline = model.solve_baseline(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

scenario = baseline.scenario("tariff abolition")

scenario.set("taum", "BRD", 0)
scenario.set("taum", "MLK", 0)

result = scenario.solve()

print(baseline.value("Z", "BRD"))
print(result.value("Z", "BRD"))
print(result.compare(baseline))
```

The conceptual flow is:

```text
CGE
 │
 └── solve_baseline()
          │
          ▼
     Equilibrium
          │
          └── scenario()
                  │
                  ▼
               Scenario
                  │
              set / unfix
                  │
                solve()
                  │
                  ▼
                Result
```

This is the canonical public vocabulary for v0.6.

---

# 5. Why `solve_baseline()` replaces `calibrate()` at the public layer

The public façade will use:

```python
model.solve_baseline(...)
```

rather than:

```python
model.calibrate(...)
```

as the canonical operation.

## Reason

The word **calibration** has a specific scientific meaning.

In CGE modeling, calibration normally refers to recovering parameters from benchmark data.

The current Hosoe implementation performs much of this calibration while constructing the Pyomo model instance from the SAM. The later legacy method named:

```text
model_calibrate()
```

then solves the BASE system and verifies that the model reproduces the benchmark equilibrium.

The IFPRI implementation makes the distinction even more explicit:

```text
calibrate parameters
→ construct BASE model
→ apply BASE closure
→ solve BASE equilibrium
```

Therefore:

```text
solve_baseline()
```

is the least ambiguous high-level name.

It describes the output that the caller receives:

> a solved benchmark equilibrium.

---

# 6. `CGE`

## 6.1 Meaning

`CGE` represents a **configured static CGE problem**.

It combines:

- a model definition;
- a dataset location;
- the machinery necessary to construct a baseline.

It should **not** expose `base` or `sim`.

It should **not** itself become the mutable scenario.

It is closer to a blueprint than to a solved equilibrium.

---

## 6.2 Constructor

Canonical form:

```python
CGE(
    model,
    data,
)
```

Recommended signature:

```python
class CGE:
    def __init__(
        self,
        model,
        data,
    ):
        ...
```

Canonical documentation should prefer keywords:

```python
CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)
```

### `model`

A model-definition object satisfying the existing structural convention:

```python
model.model()
```

returns a fresh Pyomo abstract model.

No new inheritance hierarchy is required.

Custom model definitions should remain possible through structural compatibility.

### `data`

A filesystem path or path-like object to the model dataset.

v0.6 should **not** add magical string registries to `CGE(data=...)`.

Bundled data remain available explicitly through:

```python
example_data("stdcge")
```

This keeps the API transparent.

---

# 7. `CGE.solve_baseline()`

Recommended public signature:

```python
baseline = model.solve_baseline(
    *,
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
    solver=None,
    solver_manager=None,
)
```

The method performs the legacy conceptual sequence internally:

```text
load data
→ create model instance
→ fix numeraire
→ deactivate declared redundant equation
→ solve benchmark equilibrium
→ capture solved baseline
```

The caller should not need to invoke:

```text
model_data
model_instance
model_drop_redundant
model_calibrate
```

individually.

---

# 8. Baseline closure in v0.6

v0.6 will **not** introduce a public `Closure` class.

For the engine-backed Hosoe models, the required baseline closure information can be represented clearly by two explicit component references:

```python
numeraire=("pf", "LAB")
redundant=("eqpf", "LAB")
```

This is sufficiently transparent and avoids introducing an abstraction before it is needed.

The IFPRI macro closures are more complex, but IFPRI remains under its own API in v0.6.

If a future unified backend interface demonstrates that closures need first-class objects, a `Closure` abstraction can be introduced later from actual requirements rather than speculation.

---

# 9. `Equilibrium`

## 9.1 Meaning

`Equilibrium` represents a **solved baseline equilibrium**.

It is publicly immutable.

Ordinary users cannot mutate it.

This is deliberate.

The baseline is the reference state from which scenarios are constructed.

---

## 9.2 Core public operations

The stable v0.6 public surface should be small:

```python
baseline.value(...)
baseline.scenario(...)
baseline.objective
```

No public:

```text
base
sim
model_modify_base
raw fix/unfix workflow
```

is required.

---

# 10. `Equilibrium.value()`

Canonical forms:

```python
baseline.value("Sp")
baseline.value("Z", "BRD")
baseline.value("F", "LAB", "BRD")
```

Recommended signature:

```python
value(component: str, *index) -> float
```

Rules:

1. scalar component:
   ```python
   value("Sp")
   ```

2. one-dimensional component:
   ```python
   value("Z", "BRD")
   ```

3. multidimensional component:
   ```python
   value("F", "LAB", "BRD")
   ```

4. an incomplete index is an error;

5. an extra index is an error;

6. an unknown component is an error;

7. the return value is an ordinary Python numeric value, normally `float`.

No Pyomo `value(...)` call should be required in ordinary user code.

---

# 11. What `value()` can read

The solved snapshot should record:

- active variables;
- parameters useful for inspecting the solved model;
- the objective value separately.

Therefore:

```python
result.value(...)
```

can serve both:

```text
endogenous solution inspection
```

and:

```text
inspection of the exogenous settings associated with that result
```

The public API does not expose Pyomo component objects.

---

# 12. `Equilibrium.objective`

The solved baseline should expose:

```python
baseline.objective
```

as a numeric value.

The meaning of the objective is model-specific.

For the Hosoe standard model it is the household utility objective.

The API should not rename it generically to `welfare`, because not every CGE backend necessarily uses a welfare objective.

---

# 13. `Equilibrium.scenario()`

Canonical form:

```python
scenario = baseline.scenario("tariff abolition")
```

Recommended signature:

```python
scenario(name: str) -> Scenario
```

A scenario name is metadata.

It does not need to be globally unique.

It is useful for:

- reports;
- tables;
- debugging;
- notebooks;
- batch simulation.

---

# 14. Critical ownership rule

Every call to:

```python
baseline.scenario(...)
```

must create **independent mutable scenario state**.

Required:

```python
a = baseline.scenario("A")
b = baseline.scenario("B")
```

Then:

```text
changing A cannot change B
changing B cannot change A
changing either cannot change baseline
```

This is a hard correctness invariant.

A `Scenario` must never be only a wrapper around one shared:

```text
PyCGE.sim
```

slot.

---

# 15. Required ownership picture

```text
                    Equilibrium
                  solved baseline
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   Scenario A      Scenario B      Scenario C
   own state       own state       own state
        │               │               │
        ▼               ▼               ▼
     Result A        Result B        Result C
```

The actual backend may implement isolation using deep copies, reconstruction, or another validated method.

That implementation choice is private.

The independence guarantee is public.

---

# 16. `Scenario`

`Scenario` represents a **mutable counterfactual specification and solve state** derived from one baseline equilibrium.

It owns:

- scenario name;
- its own backend state;
- its own modifications;
- its own internal solve cache.

It does not own the baseline.

It cannot mutate the baseline.

---

# 17. `Scenario.set()`

Canonical use:

```python
scenario.set("taum", "BRD", 0)
```

For multidimensional components:

```python
scenario.set("component", ("i", "j"), value)
```

Recommended signature:

```python
set(
    component: str,
    index,
    value,
) -> None
```

For a scalar component:

```python
scenario.set("epsilon", None, 1.1)
```

## Semantics

For a mutable parameter:

```text
set its value
```

For a variable:

```text
set its value and fix it
```

Thus `set()` expresses the common CGE operation:

> make this quantity exogenous at this scenario value.

---

# 18. Protected benchmark components

The new façade must preserve the current engine's protection against changing benchmark calibration data in-place.

Examples include:

```text
SAM entries
*0 benchmark magnitudes
other model-specific protected calibration inputs
```

These must continue to raise a clear `ComponentError`.

Factor endowments that are valid scenario shocks in the existing engine must remain valid.

The façade must not weaken these safeguards.

---

# 19. `Scenario.unfix()`

v0.6 should expose one small advanced closure operation:

```python
scenario.unfix("Sf", None)
```

Recommended signature:

```python
unfix(
    component: str,
    index=None,
) -> None
```

This means:

> make this variable endogenous in the scenario while preserving its current numeric value as the solver starting value.

This is useful when a shock fixes a variable that was formerly endogenous and another variable must be released to preserve closure.

The numeraire remains protected and cannot be unfixed casually.

---

# 20. Why `unfix()` is preferable to exposing `fix=False`

The legacy API allows a call conceptually similar to:

```python
model_modify_sim(..., fix=False)
```

That mixes two distinct operations:

```text
change numeric value
```

and:

```text
change endogenous/exogenous status
```

The v0.6 domain API should make them clearer:

```python
scenario.set(...)
scenario.unfix(...)
```

The usual policy-shock path stays simple.

Closure changes remain explicit.

---

# 21. Scenario closure validation

A scenario may become non-square if a user fixes or unfixes variables inconsistently.

The façade should validate the model's degrees of freedom before solving whenever the backend supports this check.

If the system is not properly closed, `solve()` should fail **before** invoking the nonlinear solver with a clear workflow/closure error.

v0.6 does not need a new exception hierarchy merely for this.

A clear `WorkflowError` is sufficient initially.

---

# 22. `Scenario.solve()`

Canonical form:

```python
result = scenario.solve()
```

Recommended signature:

```python
solve(
    *,
    solver=None,
    solver_manager=None,
) -> Result
```

Rules:

1. solve only this scenario;
2. never mutate the baseline;
3. never mutate another scenario;
4. return a solved immutable `Result`;
5. if no scenario state has changed since the previous successful solve, implementation may reuse a cached solve;
6. callers must not rely on object identity of cached results.

---

# 23. Re-solving is a first-class contract

The following workflow must be explicitly supported:

```python
scenario = baseline.scenario("experiment")

scenario.set("taum", "BRD", 0.10)
r1 = scenario.solve()

scenario.set("taum", "BRD", 0.05)
r2 = scenario.solve()

scenario.set("taum", "BRD", 0.00)
r3 = scenario.solve()
```

This is not a special dynamic-CGE feature.

It is ordinary scientific-model orchestration.

It supports:

- sensitivity analysis;
- parameter sweeps;
- iterative algorithms;
- Monte Carlo workflows;
- model coupling;
- interactive use.

---

# 24. Result invalidation versus Result immutability

This distinction is fundamental.

Suppose:

```python
r1 = scenario.solve()
scenario.set("taum", "BRD", 0)
r2 = scenario.solve()
```

After the `set()` call:

```text
the scenario's cached current solution is stale
```

but:

```text
r1 remains valid forever as the snapshot returned by the first solve
```

Therefore:

```text
Scenario solve cache: mutable / invalidatable
Result object: immutable
```

This prevents a serious scientific-software failure mode where a previously saved result silently changes because the underlying Pyomo model was modified later.

---

# 25. `Result`

`Result` is a **read-only snapshot of a successful solved state**.

It is not a view into a live Pyomo model.

It should contain backend-neutral numerical data sufficient for:

- value access;
- comparison;
- reporting;
- provenance metadata.

Its public methods should not depend on direct Pyomo traversal.

---

# 26. Result snapshot contents

At minimum:

```text
scenario/baseline label
model identity
variable values
parameter values
objective value
solver metadata needed for reporting
```

Internal backend objects do not need to be part of the stable public result.

For the initial Hosoe adapter, the snapshot may be extracted from Pyomo after successful solving.

---

# 27. `Result.value()`

Same contract as `Equilibrium.value()`:

```python
result.value("Sp")
result.value("Z", "BRD")
result.value("F", "LAB", "BRD")
```

The implementation should use a normalized internal key such as:

```text
(component_name, index_tuple)
```

Examples:

```text
("Sp", ())
("Z", ("BRD",))
("F", ("LAB", "BRD"))
```

This gives one representation for scalar, 1-D, and multidimensional components.

---

# 28. Value-access errors

Use existing error classes.

## Unknown component

```text
ComponentError
```

## Invalid or incomplete index

```text
ComponentError
```

## Protected mutation

```text
ComponentError
```

## Invalid numerical value supplied to `set()`

```text
ValueError
```

## Out-of-order lifecycle operation

```text
WorkflowError
```

## Solver failure

```text
SolveError
```

No new error classes are required in Phase 1.

---

# 29. `Result.objective`

Canonical:

```python
result.objective
```

returns a numeric objective value.

The API makes no claim that the objective is always utility or welfare.

---

# 30. `Result.compare()`

Canonical:

```python
frame = result.compare(baseline)
```

It may also compare two scenario results:

```python
frame = policy_b.compare(policy_a)
```

The rule is always:

```text
self minus reference
```

Therefore:

```text
difference = self_value - reference_value
```

and:

```text
pct_change =
    (self_value - reference_value)
    / reference_value
    * 100
```

If the reference value is zero:

```text
pct_change = NaN
```

rather than an infinite or misleading percentage.

---

# 31. Comparison DataFrame contract

Recommended columns:

```text
component
index_1
index_2
...
reference_value
value
difference
pct_change
```

Example:

| component | index_1 | reference_value | value | difference | pct_change |
|---|---|---:|---:|---:|---:|
| Z | BRD | 73.0 | 74.2 | 1.2 | 1.6438 |

For a scalar component, index columns are blank.

The number of `index_N` columns is the maximum dimensionality represented in the compared variable set.

---

# 32. Comparison scope

`Result.compare()` compares **solution variables**.

It does not mix parameters and outcomes into the same default comparison table.

Parameters remain queryable through:

```python
result.value(...)
```

but the primary comparison table remains an equilibrium-outcome table.

This preserves the conceptual behavior of the legacy `model_compare()`.

---

# 33. Objective comparison

The returned DataFrame should retain objective comparison metadata:

```python
frame.attrs["objective"] = {
    "reference": ...,
    "value": ...,
    "difference": ...,
}
```

with:

```text
difference = self.objective - reference.objective
```

This preserves the useful existing behavior without pretending the objective is an ordinary indexed variable.

---

# 34. Result compatibility

`compare()` should accept:

```text
Result
Equilibrium
```

as a reference.

An `Equilibrium` is internally normalized to its solved baseline snapshot.

Comparing results from incompatible models or incompatible variable structures should raise a clear error rather than silently compare only whatever happens to overlap.

---

# 35. Why `Result` must not expose live Pyomo objects

If a stable downstream package depends on:

```text
result.model.Z["BRD"]
```

then the package is still coupled to Pyomo and the internal model representation.

Instead, downstream code should depend on:

```python
result.value("Z", "BRD")
```

This creates freedom later to:

- reorganize model internals;
- adapt IFPRI;
- support other backends;
- change model-construction details;
- optimize scenario storage.

The stable interface becomes scientific rather than implementation-specific.

---

# 36. Raw-engine access

v0.6 will not make raw backend objects part of the stable new API.

Advanced users who explicitly need the inherited engine can continue to use:

```python
PyCGE
```

during the migration period.

The `07_under_the_hood` notebook can continue to explain Pyomo and legacy internals.

This is preferable to adding a public:

```text
raw_model
backend_model
engine
```

escape hatch prematurely.

---

# 37. Public model namespace

Introduce:

```text
cge_core.models
```

Canonical imports:

```python
from cge_core.models import SplCGE, StdCGE
```

These represent the existing Hosoe simple and standard model definitions.

The source equation files do **not** need to move initially.

The new namespace can be an import façade over validated existing implementations.

---

# 38. Why `SplCGE` and `StdCGE`

The names preserve continuity with the established model identifiers:

```text
splcge
stdcge
```

while making them look like supported model definitions rather than incidental files under `examples`.

Canonical documentation should always describe them by their substantive names:

```text
Hosoe simple CGE
Hosoe standard open-economy CGE
```

---

# 39. Existing `StdModelDef` and `SplModelDef`

The current import paths should continue to work in v0.6:

```python
from cge_core.examples.stdcge_model_def import StdModelDef
from cge_core.examples.splcge_model_def import SplModelDef
```

They need not be used in canonical new-user documentation.

This is a compatibility transition, not a destructive rename.

---

# 40. No model inheritance hierarchy

Do not introduce:

```text
BaseModel
AbstractCGEModel
HosoeModelBase
ModelFactory
ModelRegistry
```

merely for architectural symmetry.

The current model definitions already satisfy a simple structural protocol:

```python
model.model()
```

with optional metadata.

That is enough for the first façade.

Composition remains preferable to hierarchy.

---

# 41. Initial internal adapter

The new public façade may use a private adapter conceptually like:

```text
CGE
 │
 ▼
_PyCGEBackend
 │
 ▼
PyCGE
 │
 ▼
existing ModelDef
```

The exact private class name is not part of the public contract.

The adapter exists to translate domain operations into the validated legacy workflow.

---

# 42. No public backend protocol yet

v0.6 should define the **behavioral capability** needed from a backend, but it should not expose a formal public plugin/protocol API yet.

Reason:

```text
only one backend will initially implement the new CGE façade
```

and:

```text
IFPRI is intentionally not being forced into it yet
```

A public plugin protocol before a second implementation would be speculative.

---

# 43. Internal backend capability contract

The internal architecture should nevertheless be designed around these capabilities:

```text
construct and solve baseline
create independent scenario state
set scenario component
unfix scenario variable
validate scenario closure
solve scenario
extract immutable result snapshot
```

A future IFPRI adapter can implement those capabilities differently.

For example, an IFPRI scenario may rebuild a model from:

```text
dataset
+ calibrated benchmark
+ shocked exogenous data
+ scenario closure
```

instead of cloning a `PyCGE.sim`.

That is acceptable.

---

# 44. IFPRI policy for v0.6

`cge_core.ifpri` remains a first-class supported public subsystem.

Its existing clean-room API remains available.

v0.6 should **not**:

- rewrite IFPRI into `PyCGE`;
- rename its current public functions gratuitously;
- force named IFPRI policy scenarios through `Scenario.set()`;
- claim the top-level `CGE` façade supports IFPRI if it does not.

Documentation should be explicit:

> The v0.6 `CGE` domain façade initially covers engine-backed Hosoe-style models. The validated IFPRI implementation retains its dedicated API.

This is more trustworthy than a superficial unification.

---

# 45. Future IFPRI adaptation

The Phase 1 design deliberately leaves room for a later adapter.

A future implementation could map:

```text
CGE.solve_baseline()
```

to:

```text
calibrate_ifpri_benchmark
build_ifpri_base_solve_model
solve_ifpri_base
```

and map:

```text
Equilibrium.scenario()
```

to:

```text
build_ifpri_scenario_model
```

or a generalized scenario builder.

But this is **not required for v0.6**.

---

# 46. CAMCGE policy for v0.6

CAMCGE remains:

```text
repository-level replication and regression benchmark
```

It should not be moved into:

```text
cge_core.models
```

solely to make the namespace look complete.

Its value in v0.6 is as a behavioral oracle protecting the inherited engine and economic semantics.

---

# 47. `PyCGE` compatibility policy

v0.6 retains:

```python
from cge_core import PyCGE
```

The class remains functional.

It should be described as:

> **Legacy/advanced workflow API**

rather than the canonical new API.

---

# 48. No runtime deprecation warning in v0.6

Do **not** emit a `DeprecationWarning` merely from importing or constructing `PyCGE` in v0.6.

Reasons:

- the migration is staggered;
- notebooks and external users may still rely on it;
- the under-the-hood teaching material still has legitimate use for it;
- the test configuration currently suppresses ordinary deprecation warnings;
- there is no need to create warning noise before the replacement surface is fully proven.

Canonical documentation is sufficient to shift new usage.

A runtime deprecation policy can be reconsidered after v0.6 adoption.

---

# 49. Removal policy

`PyCGE` should not be removed in a minor pre-1.0 cleanup without explicit review.

A conservative rule is:

> Do not remove `PyCGE` before 1.0 solely because the new façade exists.

The project can later decide whether:

- it remains an advanced engine API;
- it becomes private;
- it receives a formal deprecation cycle.

There is no need to settle that now.

---

# 50. Root exports in v0.6

Recommended canonical root surface:

```python
from cge_core import (
    CGE,
    Equilibrium,
    Scenario,
    Result,
    CGEError,
    WorkflowError,
    ComponentError,
    DataValidationError,
    SolveError,
    example_data,
    samtools,
)
```

Legacy compatibility additionally keeps:

```python
PyCGE
```

---

# 51. Public/private boundary

## Stable public surface

Downstream packages may rely on:

```text
CGE
CGE.solve_baseline

Equilibrium
Equilibrium.scenario
Equilibrium.value
Equilibrium.objective

Scenario
Scenario.set
Scenario.unfix
Scenario.solve

Result
Result.value
Result.objective
Result.compare

cge_core.models.SplCGE
cge_core.models.StdCGE

existing public errors
example_data
samtools
```

---

# 52. Explicitly unstable/internal surface

Downstream extensions should **not** rely on:

```text
PyCGE.base
PyCGE.sim
dict_base
dict_sim
base_calibrated
sim_solved
Pyomo clone details
private adapter classes
private result storage
direct component traversal
internal cache identity
```

`PyCGE` remains usable, but these internals are not the new extension contract.

---

# 53. Stable downstream orchestration contract

A future package should be able to depend only on:

```python
baseline = model.solve_baseline(...)

scenario = baseline.scenario("experiment")

scenario.set(...)
result_1 = scenario.solve()
x1 = result_1.value(...)

scenario.set(...)
result_2 = scenario.solve()
x2 = result_2.value(...)

comparison = result_2.compare(baseline)
```

This is the core v0.6 extension contract.

It is intentionally small.

---

# 54. What downstream packages are promised

They may assume:

1. a solved baseline remains unchanged;
2. scenarios are independent;
3. modifying one scenario does not modify another;
4. modifying a scenario makes its cached solve stale;
5. previously returned `Result` objects remain unchanged;
6. a scenario can be solved repeatedly;
7. component values can be retrieved without Pyomo traversal;
8. comparisons use a documented direction and formula;
9. invalid component/index operations fail loudly.

They may **not** assume how any of those guarantees are implemented.

---

# 55. No dynamic-CGE-specific API

The stable contract is intentionally sufficient for external orchestration but contains no:

```text
time index
capital accumulation
transition equation
intertemporal closure
terminal condition
dynamic solve loop
```

Those belong in a future downstream package if needed.

The base package remains a static-CGE engine.

---

# 56. Recommended initial file layout

The first implementation should remain small.

A reasonable additive structure is:

```text
cge_core/
    __init__.py
    api.py
    engine.py
    models/
        __init__.py
```

Where:

```text
api.py
```

contains initially:

```text
CGE
Equilibrium
Scenario
Result
private adapter helpers if small
```

and:

```text
models/__init__.py
```

exposes the supported model definitions.

Do not split into many modules before the code requires it.

---

# 57. Why one `api.py` first

Prematurely creating:

```text
equilibrium.py
scenario.py
result.py
backend.py
protocols.py
registry.py
closures.py
```

would increase architectural surface before the object model has been exercised.

The first implementation should be boring and readable.

Split modules later only when there is a real separation pressure.

---

# 58. Scenario implementation safety requirement

The Phase 2 implementation may choose any validated mechanism that guarantees isolation.

The safest initial approaches include:

```text
one independent legacy-engine state per Scenario
```

or:

```text
an independently cloned backend model owned by each Scenario
```

The implementation should favor correctness over clever memory optimization.

Do not share one mutable legacy `sim` among public Scenario objects.

---

# 59. Result implementation recommendation

Create the `Result` snapshot immediately after a successful solve.

Extract numerical values into ordinary Python data structures.

Conceptually:

```python
variables = {
    ("Z", ("BRD",)): 73.0,
    ...
}

parameters = {
    ("taum", ("BRD",)): 0.0,
    ...
}
```

The exact private representation may differ.

The important rule is:

> the snapshot no longer depends on later mutations of the live scenario model.

---

# 60. Baseline implementation recommendation

`Equilibrium` should likewise expose values from a solved snapshot rather than requiring public traversal of the live baseline Pyomo model.

It may privately retain backend state because it must create scenarios.

The snapshot and the backend state have different purposes:

```text
snapshot → read-only public result access
backend state → private scenario construction
```

---

# 61. No hidden baseline mutation

The new public `Equilibrium` should not expose a generic `set()`.

If the user wants a different benchmark assumption or closure, they should construct or solve another baseline.

Counterfactual changes belong to `Scenario`.

This preserves the conceptual distinction:

```text
benchmark equilibrium
versus
policy experiment
```

---

# 62. Error policy

The new façade reuses the existing typed error hierarchy.

The goal remains:

> bad workflow should fail loudly and descriptively rather than produce plausible wrong results.

Examples:

```python
scenario.set("not_a_component", None, 1)
# ComponentError
```

```python
scenario.set("Z", "NOT_A_GOOD", 10)
# ComponentError
```

```python
scenario.set("taum", "BRD", float("nan"))
# ValueError
```

```python
scenario.solve()
# WorkflowError before solver if closure is invalid
```

---

# 63. Numerical behavior policy

The façade must not alter:

```text
model equations
calibrated coefficients
bounds
default objective
closure mathematics
solver acceptance criteria
benchmark values
comparison sign convention
```

unless an independently reviewed correctness change is made.

v0.6 is an API reengineering release, not a model rewrite.

---

# 64. Phase 2 API tests required before outward migration

The following tests should be written with the new implementation.

## Imports

```text
test_root_exports_new_api
test_models_namespace_exports_hosoe_models
test_legacy_pycge_still_imports
```

## Baseline

```text
test_splcge_new_api_baseline_matches_legacy
test_stdcge_new_api_baseline_matches_legacy
test_baseline_value_scalar
test_baseline_value_one_dimensional
test_baseline_value_multidimensional
test_baseline_invalid_component
test_baseline_invalid_index
```

## Scenario isolation

```text
test_scenario_does_not_mutate_baseline
test_two_scenarios_are_independent
test_three_scenarios_can_coexist
```

## Scenario mutation

```text
test_set_mutable_parameter
test_set_variable_fixes_it
test_unfix_variable
test_numeraire_cannot_be_unfixed
test_protected_calibration_data_cannot_be_set
```

## Solving

```text
test_scenario_solve_matches_legacy_counterfactual
test_solve_modify_solve_again
test_modifying_one_scenario_does_not_invalidate_another
```

## Result immutability

```text
test_old_result_does_not_change_after_scenario_mutation
test_old_result_does_not_change_after_resolve
```

## Comparison

```text
test_compare_difference_is_self_minus_reference
test_compare_pct_change_matches_legacy_formula
test_compare_zero_reference_pct_is_nan
test_compare_objective_sign_matches_legacy
test_compare_incompatible_results_fails
```

## Compatibility

```text
test_legacy_pycge_workflow_still_passes
```

---

# 65. Critical acceptance test: two simultaneous scenarios

This should be treated as one of the defining tests of v0.6.

Example:

```python
baseline = model.solve_baseline(...)

a = baseline.scenario("A")
b = baseline.scenario("B")

a.set("taum", "BRD", 0)
b.set("taum", "BRD", 0.20)

ra = a.solve()
rb = b.solve()

assert ra.value("Z", "BRD") != rb.value("Z", "BRD")

# Re-read A after B has solved.
assert ra.value("Z", "BRD") == ra.value("Z", "BRD")

# Baseline still unchanged.
assert baseline.value("taum", "BRD") != 0
```

The exact numerical assertions should use known benchmark/counterfactual values where appropriate.

---

# 66. Critical acceptance test: Result snapshot

```python
scenario.set("taum", "BRD", 0.10)
r1 = scenario.solve()

old = r1.value("Z", "BRD")

scenario.set("taum", "BRD", 0.00)
r2 = scenario.solve()

assert r1.value("Z", "BRD") == old
assert r2.value("Z", "BRD") != old
```

This verifies that `Result` is a snapshot rather than a live view.

---

# 67. Critical acceptance test: comparison compatibility

The same canonical tariff experiment should be solved once through:

```text
legacy PyCGE
```

and once through:

```text
new CGE façade
```

Then compare:

```text
variable levels
differences
percentage changes
objective difference
```

within strict numerical tolerance.

The new API must be a different interface to the same economics.

---

# 68. Notebook migration target

Once Phase 2 is stable:

## Notebook 01

Should teach:

```text
CGE
solve_baseline
scenario
set
solve
value
compare
```

without exposing `PyCGE.base`.

## Notebook 02

Should use the same public API.

## Notebook 03

Should demonstrate multiple simultaneous `Scenario` objects.

This will be one of the strongest demonstrations that the reengineering actually improved the architecture.

## Notebook 04

Should combine the new API with `samtools`.

## Notebook 05

Should remain on the dedicated IFPRI API until an adapter is deliberately added.

## Notebook 06

Should remain a CAMCGE replication workflow.

## Notebook 07

May intentionally continue showing `PyCGE` and raw Pyomo internals as an advanced section.

---

# 69. Control Room migration target

The Control Room generated code should eventually emit:

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE
```

and:

```python
model = CGE(...)
baseline = model.solve_baseline(...)
scenario = baseline.scenario(...)
scenario.set(...)
result = scenario.solve()
```

It should no longer require:

```text
cge.base
cge.sim
model_modify_sim
raw Pyomo value()
```

for normal generated workflows.

---

# 70. README migration target

The README Quick Start should become the shortest canonical demonstration of the new API.

Legacy `PyCGE` should move to a clearly labeled compatibility or advanced section.

The project identity should become:

```text
CGE-Core public domain API
```

rather than:

```text
a renamed PyCGE workflow
```

while historical provenance remains fully documented.

---

# 71. Documentation architecture target

The architecture documentation should eventually show:

```text
User
 │
 ▼
CGE public API
 │
 ├── Equilibrium
 │      └── Scenario
 │             └── Result
 │
 ▼
private backend adapter
 │
 ▼
validated model implementation
```

with a separate branch for the existing IFPRI subsystem.

This is more accurate than depicting one monolithic engine.

---

# 72. Phase 1 non-goals

Do not do any of the following merely because Phase 1 exists:

- rewrite `engine.py`;
- rename `PyCGE` internally;
- move Hosoe equation files;
- rewrite IFPRI;
- move CAMCGE;
- introduce a model factory;
- introduce a plugin registry;
- create a public backend ABC;
- create a `Closure` hierarchy;
- add time/dynamic concepts;
- change equations;
- change solver tolerances;
- change benchmark data.

---

# 73. Phase 1 public contract in one page

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

# Configure the model.
model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

# Solve the immutable benchmark equilibrium.
baseline = model.solve_baseline(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

# Create independent scenario state.
policy = baseline.scenario("tariff abolition")

# Apply exogenous changes.
policy.set("taum", "BRD", 0)
policy.set("taum", "MLK", 0)

# Solve and receive an immutable snapshot.
result = policy.solve()

# Read model values without touching Pyomo.
z0 = baseline.value("Z", "BRD")
z1 = result.value("Z", "BRD")

# Compare result against a reference.
comparison = result.compare(baseline)

# Re-use the same scenario safely.
policy.set("taum", "BRD", 0.05)
result_2 = policy.solve()

# result is still the first solution.
assert result.value("Z", "BRD") == z1
```

This is the intended v0.6 experience.

---

# 74. Phase 1 acceptance criteria

Phase 1 is complete when the following decisions are treated as frozen for implementation:

- [x] `CGE` is a real façade, not `CGE = PyCGE`.
- [x] `solve_baseline()` is the canonical baseline operation.
- [x] `Equilibrium` is a solved immutable baseline.
- [x] `Scenario` owns independent mutable state.
- [x] multiple scenarios can coexist.
- [x] `Scenario.set()` applies the ordinary exogenous shock.
- [x] `Scenario.unfix()` handles the small advanced closure need.
- [x] scenario modification invalidates only that scenario's solve cache.
- [x] `Result` is an immutable numerical snapshot.
- [x] old `Result` objects never change after later scenario mutations.
- [x] `value(component, *index)` is the stable accessor.
- [x] `Result.compare(reference)` uses `self - reference`.
- [x] comparisons default to variables, not parameters.
- [x] objective comparison remains separate metadata.
- [x] baseline closure is explicit through `numeraire` and `redundant`.
- [x] no first-class `Closure` object is introduced yet.
- [x] `cge_core.models` becomes the canonical model namespace.
- [x] Hosoe source files need not move.
- [x] IFPRI remains under its dedicated API in v0.6.
- [x] CAMCGE remains a replication benchmark.
- [x] `PyCGE` remains compatible without a runtime warning in v0.6.
- [x] raw Pyomo state is not part of the new stable contract.
- [x] no plugin or backend framework is exposed prematurely.
- [x] no dynamic-CGE concepts are added to CGE-Core.

---

# 75. Implementation gate before Phase 2

Before writing the new façade on the reengineering branch, retain the two outstanding Phase 0 safeguards:

1. establish branch-safe notebook execution so Colab setup does not silently reset to `origin/main`;
2. establish at least one Control Room generated-code smoke/reference fixture.

Then Phase 2 can begin additively.

No validated economic model equations need to change.

---

# 76. Final Phase 1 architecture

The architecture to implement is:

```text
                     PUBLIC API
                 ┌───────────────┐
                 │      CGE      │
                 └───────┬───────┘
                         │
                  solve_baseline
                         │
                         ▼
                 ┌───────────────┐
                 │  Equilibrium  │
                 └───────┬───────┘
                         │
                      scenario
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │Scenario │ │Scenario │ │Scenario │
        │    A    │ │    B    │ │    C    │
        └────┬────┘ └────┬────┘ └────┬────┘
             │            │            │
           solve        solve        solve
             │            │            │
             ▼            ▼            ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │ Result  │ │ Result  │ │ Result  │
        │immutable│ │immutable│ │immutable│
        └─────────┘ └─────────┘ └─────────┘

                         │
                         │ private implementation
                         ▼
                 ┌───────────────┐
                 │ adapter layer │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │     PyCGE     │
                 │ legacy engine │
                 └───────┬───────┘
                         │
                         ▼
                 validated Hosoe
                 model definitions
```

Separately:

```text
cge_core.ifpri
    │
    └── validated dedicated IFPRI architecture
```

and:

```text
cam/
    │
    └── CAMCGE replication benchmark
```

The public architecture is unified where it is useful.

The validated scientific implementations remain separate where they genuinely differ.

---

# 77. Phase 1 verdict

Phase 1 should freeze **behavioral abstractions**, not internal structure.

The crucial contract is:

> **A `CGE` solves an immutable baseline `Equilibrium`; the equilibrium creates independent mutable `Scenario` objects; solving a scenario returns an immutable `Result`; results are read and compared through backend-neutral numerical accessors.**

This gives CGE-Core a genuine scientific-Python API without requiring a risky rewrite of its validated models.

It also establishes exactly the extension surface needed by future orchestration code:

```text
solve baseline
→ branch scenario
→ modify
→ solve
→ inspect
→ modify again
→ solve again
```

while keeping CGE-Core itself a static-CGE package.

**Phase 1 specification: complete.**
