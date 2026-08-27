> **SUPERSESSION NOTICE (v0.6):** This is an earlier planning document retained for decision history. Where it conflicts with `STAGGERED_EXECUTION_PLAN.md`, `PHASE_1_API_SPECIFICATION_ORIGINAL.md`, `COURSE_CORRECTION_RECONCILIATION.md`, or `PHASE_2_ENTRY_DECISIONS.md`, the later documents govern. In particular, the canonical v0.6 design uses a real `CGE` facade by composition, `solve_benchmark()` (not `calibrate()`/`solve_baseline()`), no runtime deprecation warning for `PyCGE`, and no public raw-model accessor.

# CGE-Core v0.6 Reengineering Plan

**Status:** Proposed
**Target release:** `0.6.0`
**Purpose:** Reengineer CGE-Core into a clearly independent, stable, extensible scientific Python framework before downstream packages such as DCGE-Core depend on it.

---

## 1. Why this release is needed

CGE-Core has grown beyond its original NIST PyCGE lineage. It now includes multiple CGE model families, benchmark validation, SAM tooling, solver handling, documentation, reproducible examples, and a broader research-software identity.

However, the current public workflow still exposes the inherited `PyCGE` class and a stateful API centered on:

```text
model_data()
→ model_instance()
→ model_drop_redundant()
→ model_calibrate()
→ model_sim()
→ model_modify_sim()
→ model_solve()
→ model_compare()
```

This creates three problems.

1. **Identity problem.**
   The name `PyCGE` makes CGE-Core appear to be merely a wrapper around the older NIST project, even though CGE-Core is now a substantially broader framework.

2. **API design problem.**
   A single mutable object currently carries many workflow states: uninitialized, instantiated, calibrated, simulation-created, modified, solved, and compared.

3. **Extension problem.**
   Future downstream packages such as DCGE-Core need a small, durable public contract for solving CGE equilibria repeatedly without depending on private engine internals.

Version `0.6.0` will address these issues before the API becomes harder to change.

---

# 2. Design goals

CGE-Core `0.6.0` should satisfy the following goals.

## 2.1 Establish a native CGE-Core identity

The canonical public interface should use CGE-Core terminology rather than the inherited `PyCGE` name.

Canonical usage should become conceptually:

```python
from cge_core import CGE
```

rather than:

```python
from cge_core import PyCGE
```

The historical NIST lineage will remain clearly documented in provenance and licensing, but it should no longer define the public identity of the framework.

---

## 2.2 Separate economic model definition from execution

CGE-Core should preserve one of its strongest existing design choices:

```text
economic model algebra
        ≠
simulation workflow
```

Model-definition classes should continue to declare the economics.

The core framework should handle:

- data loading;
- model instantiation;
- closure configuration;
- calibration;
- equilibrium solving;
- scenarios;
- result extraction;
- validation;
- comparison;
- reporting.

---

## 2.3 Replace workflow-state flags with clearer domain objects

The current engine stores state through attributes such as:

```python
base
sim
base_calibrated
sim_solved
base_results
sim_results
```

This works, but it makes one object behave as many different things.

The new architecture should move toward explicit objects representing actual concepts:

```text
CGE
│
├── Baseline / Equilibrium
│
├── Scenario
│
└── Result
```

Invalid workflow states should become harder to represent.

---

## 2.4 Define a small stable public API

Downstream users and packages should depend only on documented public interfaces.

They should not need to access:

```python
cge._something
cge.sim.some_pyomo_variable
cge.base.some_internal_component
cge_core.engine._private_function
```

The public API should be intentionally small.

---

## 2.5 Preserve CGE-Core's independence

CGE-Core must remain a static/general CGE framework.

It should **not** gain concepts merely because DCGE-Core may later exist.

CGE-Core should know nothing about:

- time periods;
- dynamic state transitions;
- capital accumulation across periods;
- recursive simulation;
- population growth paths;
- dynamic baselines;
- terminal conditions.

Those belong in DCGE-Core.

CGE-Core should only expose generally useful equilibrium capabilities that a dynamic package can compose.

---

## 2.6 Preserve tested economics

Version `0.6.0` is primarily an architectural/API release.

It should not casually alter the economic equations of the existing benchmark models.

The Hosoe, IFPRI, CAMCGE, and other validated benchmarks should continue to reproduce their existing results.

---

# 3. Non-goals

The following are explicitly **not** part of `0.6.0`.

- Implement Hosoe DYNCGE.
- Create DCGE-Core.
- Add recursive dynamics.
- Add intertemporal optimization.
- Replace Pyomo.
- Rewrite every model from scratch.
- Remove NIST attribution.
- Remove NIST licensing notices where required.
- Introduce an elaborate plugin framework.
- Build a large enterprise-style dependency-injection system.
- Break benchmark replication merely for stylistic consistency.
- Introduce unnecessary abstractions with no current use.

The release should remain scientifically transparent and relatively small.

---

# 4. Proposed public architecture

The target conceptual architecture is:

```text
Model Definition
      │
      ▼
     CGE
      │
      │ calibrate(...)
      ▼
  Equilibrium
      │
      │ scenario(...)
      ▼
   Scenario
      │
      │ solve()
      ▼
    Result
```

A user should be able to understand these objects without knowing Pyomo internals.

---

# 5. Core public objects

## 5.1 `CGE`

`CGE` is the main public façade of the framework.

Conceptually:

```python
from cge_core import CGE
from cge_core.models import StdCGE

model = CGE(
    StdCGE(),
    data="path/to/data",
)
```

Responsibilities:

- accept a model definition;
- load and validate data;
- construct the underlying model;
- configure model-wide execution resources;
- create a calibrated equilibrium;
- provide a clean boundary around lower-level Pyomo machinery.

`CGE` should not itself represent a solved reform scenario.

---

## 5.2 `Equilibrium`

An `Equilibrium` represents a valid calibrated/solved economic equilibrium.

Conceptually:

```python
baseline = model.calibrate(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

Responsibilities:

- hold the solved benchmark state;
- expose equilibrium values through a stable read API;
- act as the starting point for counterfactual scenarios;
- preserve closure information;
- preserve relevant calibration information;
- provide reproducible metadata about the solve.

An `Equilibrium` object should always be a valid solved equilibrium.

---

## 5.3 `Scenario`

A `Scenario` represents a counterfactual configuration derived from an equilibrium.

Conceptually:

```python
reform = baseline.scenario("tariff abolition")

reform.set("taum", "BRD", 0)
reform.set("taum", "MLK", 0)

result = reform.solve()
```

Responsibilities:

- isolate shocks from the baseline;
- safely modify admissible exogenous components;
- validate component names and indexes;
- preserve modification history;
- allow repeated modification and re-solving where economically valid;
- avoid mutation leaking into the baseline.

A scenario should not expose private Pyomo internals as its primary user interface.

---

## 5.4 `Result`

A `Result` represents a solved scenario.

Conceptually:

```python
result = reform.solve()

z_bread = result.value("Z", "BRD")
frame = result.to_frame()
comparison = result.compare(baseline)
```

Responsibilities:

- retrieve scalar or indexed equilibrium values;
- expose results as plain Python objects and pandas structures;
- compare against a baseline or another compatible equilibrium;
- carry solver metadata;
- provide reproducible export methods.

A `Result` should be suitable for use by downstream packages without direct Pyomo access.

---

# 6. Public result/value access

A stable value-access API is essential.

Users and downstream packages should not be forced to write:

```python
from pyomo.environ import value

value(cge.sim.Z["BRD"])
```

Instead:

```python
result.value("Z", "BRD")
```

or:

```python
baseline.value("Z", "BRD")
```

The accessor should:

- accept scalar and indexed components;
- return ordinary Python numeric values;
- raise clear CGE-Core exceptions for invalid components;
- avoid exposing Pyomo-specific component objects unless explicitly requested through an advanced API.

This is important for DCGE-Core because a dynamic package should be able to read investment, factor returns, output, or other equilibrium values through a documented CGE-Core interface.

---

# 7. Scenario modification API

The current `model_modify_sim()` capability is valuable and should be preserved conceptually.

The public API should move toward:

```python
scenario.set("taum", "BRD", 0)
```

rather than:

```python
cge.model_modify_sim("taum", "BRD", 0)
```

The new API should preserve:

- component validation;
- index validation;
- mutable-parameter checks;
- variable-bound checks;
- protection of benchmark-only calibration data;
- reversible or reconstructible scenario state;
- clear errors.

Repeated modification followed by repeated solving should remain supported.

Example:

```python
scenario.set("FF", "LAB", 100)
result_1 = scenario.solve()

scenario.set("FF", "LAB", 105)
result_2 = scenario.solve()
```

This is a general CGE capability, not a dynamic-specific feature.

---

# 8. Re-solvability as a formal contract

CGE-Core should formally guarantee:

> A scenario may be modified after a successful solve and solved again, provided the modified component is admissible and the model remains well posed.

This behavior already exists in the current engine and should become an explicit, tested public contract.

This is important for:

- sensitivity analysis;
- parameter sweeps;
- comparative statics;
- Monte Carlo experiments;
- iterative algorithms;
- external model coupling;
- future downstream packages such as DCGE-Core.

No time or dynamic concept needs to appear in CGE-Core to support this.

---

# 9. Extension protocol

CGE-Core should define a minimal public capability contract for downstream packages.

The precise names should be finalized during implementation, but conceptually the contract is:

```python
class EquilibriumLike(Protocol):
    def scenario(self, name: str | None = None): ...
    def value(self, component: str, index=None) -> float: ...

class ScenarioLike(Protocol):
    def set(self, component: str, index, value: float): ...
    def solve(self): ...
```

The purpose is not to build a generic plugin system.

The purpose is to establish what downstream code may safely rely upon.

DCGE-Core should eventually depend on this public capability rather than:

```python
cge_core.engine.CGE
```

or internal Pyomo objects.

---

# 10. Public versus private API

Version `0.6.0` should explicitly define public API rules.

## Public

Anything intentionally exported from:

```python
cge_core
```

and documented as public.

Likely examples:

```python
CGE
Equilibrium
Scenario
Result
CGEError
WorkflowError
ComponentError
DataValidationError
SolveError
example_data
samtools
```

Selected model-definition classes may also be exported through a stable model namespace.

---

## Private

Implementation details should use leading underscores where appropriate and should not be considered compatibility commitments.

Examples:

```python
_solve_instance()
_component_key()
_normalise_index()
_internal_clone()
```

Downstream projects must not depend on these.

---

# 11. `PyCGE` rename and migration

## 11.1 Canonical class rename

The implementation should move from:

```python
class PyCGE:
```

to:

```python
class CGE:
```

The documentation, examples, notebooks, and tests should use `CGE`.

The public architecture should no longer visually present NIST PyCGE as the center of CGE-Core.

---

## 11.2 Historical provenance

The rename must not obscure provenance.

`engine.py`, project documentation, and licensing should continue to explain that the original workflow code has historical lineage in the NIST PyCGE project.

The distinction should be explicit:

```text
source lineage: NIST PyCGE
current framework: CGE-Core
```

---

## 11.3 Compatibility policy for `PyCGE`

Because CGE-Core is still pre-1.0, two options are acceptable.

### Preferred option

Make `CGE` canonical in `0.6.0` and retain:

```python
PyCGE = CGE
```

temporarily with a deprecation warning.

Remove the alias in a later pre-1.0 release after a documented migration window.

### Alternative

Make a clean break in `0.6.0` and remove `PyCGE` immediately.

The final choice should consider whether any external users already depend on the old import.

Regardless of the compatibility choice, **the actual canonical implementation class should be named `CGE`.**

---

# 12. Model namespace cleanup

Model definitions should become easier to discover and should not remain conceptually buried under `examples`.

Instead of:

```python
from cge_core.examples.stdcge_model_def import StdModelDef
```

the long-term public import should move toward something like:

```python
from cge_core.models import StdCGE
```

or:

```python
from cge_core.models.hosoe import StdCGE
```

This does not require immediately moving every physical file if doing so would create unnecessary disruption.

A stable public import layer can be introduced first.

Possible public structure:

```text
cge_core/
    models/
        hosoe/
            simple.py
            standard.py
        ifpri/
        camcge/
```

The exact physical organization should follow the actual independence of the existing implementations.

---

# 13. Closure API

Closure configuration is currently spread across calls such as:

```python
model_instance("pf", "LAB")
model_drop_redundant("eqpf", "LAB")
```

For `0.6.0`, this should become clearer at the façade level.

A minimal interface could be:

```python
baseline = model.calibrate(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

A dedicated `Closure` object should only be introduced if closure configuration becomes sufficiently complex to justify it.

Avoid abstraction for its own sake.

---

# 14. Solver API

Solver handling should remain centralized in CGE-Core.

Users should not need to interact with `SolverFactory` for ordinary use.

Conceptually:

```python
model = CGE(..., solver="ipopt")
```

or:

```python
baseline = model.calibrate(solver="ipopt")
```

The framework should preserve:

- solver auto-detection where appropriate;
- clear solver failure exceptions;
- optimal-termination checks;
- reproducible solver metadata.

The solver layer should remain replaceable internally without changing the public scenario/result API.

---

# 15. Exception hierarchy

The existing exception hierarchy is useful and should be retained or refined:

```text
CGEError
├── WorkflowError
├── ComponentError
├── DataValidationError
└── SolveError
```

The new architecture should reduce the need for workflow errors by making invalid states less representable.

For example, a `Result` should never need to raise:

```text
"You must solve first."
```

because obtaining a `Result` already implies that solving succeeded.

---

# 16. Data and SAM tooling

Existing SAM tooling should remain independent of the execution engine.

The following capabilities should be preserved:

- balanced-SAM validation;
- account-label validation;
- dataset construction;
- model-specific structural checks;
- example datasets.

No DCGE-specific SAM format should be added in `0.6.0`.

If future dynamic packages need additional metadata such as capital-factor identity, those should be defined downstream unless they are generally meaningful for static CGE models.

---

# 17. Result tables and exports

`Result` and `Equilibrium` should expose tidy, reproducible data.

Likely methods:

```python
result.value(...)
result.to_frame()
result.compare(...)
result.export(...)
```

The existing pandas-based comparison behavior should be preserved conceptually.

Result structures should support:

- scalar variables;
- one-dimensional variables;
- multidimensional variables;
- clear component names;
- explicit indexes;
- no hidden reliance on DataFrame formatting.

This will make downstream scientific analysis easier.

---

# 18. Immutability and mutation policy

Full immutability is not required.

Scientific optimization models are naturally mutable internally.

However, mutation should be controlled.

Desired rules:

- baseline equilibria are not mutated by scenarios;
- scenarios own their modifications;
- solving a scenario does not alter the baseline;
- modifying a solved scenario invalidates its previous solution;
- a new solve produces a new `Result` or clearly replaces only scenario-local result state;
- benchmark calibration inputs are protected from unsafe in-place modification.

---

# 19. Preserve access to advanced Pyomo internals

CGE-Core should not prevent expert users from accessing the underlying Pyomo model.

However, this should be an explicitly advanced escape hatch rather than the normal API.

For example:

```python
baseline.raw_model
```

or another clearly documented accessor.

The existence of an advanced escape hatch does not make the underlying internals part of the stable extension API.

---

# 20. Testing strategy

Version `0.6.0` should add several new categories of tests.

## 20.1 Public API tests

Verify canonical imports:

```python
from cge_core import CGE
```

and all other declared public objects.

---

## 20.2 Extension-contract tests

Verify:

```text
calibrate
→ create scenario
→ modify
→ solve
→ read result
→ modify again
→ solve again
→ read result again
```

This protects the capability future downstream packages may need.

---

## 20.3 Isolation tests

Verify that modifying a scenario never changes:

- baseline parameters;
- baseline variables;
- baseline results;
- another scenario.

---

## 20.4 Value-access tests

Verify stable retrieval of:

- scalar components;
- indexed components;
- multidimensional components;
- invalid component errors;
- invalid index errors.

---

## 20.5 Benchmark regression tests

All existing validated benchmarks should continue to pass.

At minimum:

- Hosoe simple CGE;
- Hosoe standard CGE;
- IFPRI benchmark tests;
- CAMCGE replication checks.

No architecture refactor should be accepted if benchmark economics silently change.

---

## 20.6 API deprecation tests

If `PyCGE` remains temporarily available:

- importing it should work;
- it should emit the intended deprecation warning;
- documentation should not use it as the canonical interface.

---

# 21. Documentation changes

The documentation should be rewritten around the new domain model.

The main architecture diagram should become:

```text
Model Definition
      │
      ▼
     CGE
      │
      ▼
  Equilibrium
      │
      ▼
   Scenario
      │
      ▼
    Result
```

The README quick start should no longer use `PyCGE`.

Documentation should clearly distinguish:

- model algebra;
- calibration;
- closure;
- baseline equilibrium;
- counterfactual scenario;
- solved result;
- advanced Pyomo access.

---

# 22. Provenance language

CGE-Core should use precise language about its history.

Recommended framing:

> CGE-Core originated from the public-domain NIST PyCGE implementation by Fung and Burtwistle and has since evolved into an independently maintained CGE framework with expanded model coverage, validation infrastructure, SAM tooling, documentation, and reproducible policy-simulation workflows.

Avoid language that incorrectly implies either:

- CGE-Core is merely a wrapper around an externally imported PyCGE package; or
- CGE-Core was independently implemented from scratch with no source lineage.

Both would be inaccurate.

---

# 23. Licensing

Retain all required provenance and notices.

In particular:

- retain `LICENSE_NIST.txt`;
- retain appropriate source-file provenance;
- preserve third-party licensing requirements;
- keep CGE-Core's own project license clear.

The API redesign does not change the historical origin of inherited source code.

---

# 24. Versioning policy

CGE-Core is currently pre-1.0, which makes `0.6.0` the right time for architectural cleanup.

For the remainder of the `0.x` series:

- public API changes should still be intentional and documented;
- downstream packages should use narrow version bounds;
- deprecated public interfaces should have explicit removal targets.

Before `1.0`, CGE-Core should publish a clear compatibility policy.

After `1.0`, breaking changes should require a major version.

---

# 25. Dependency policy for future downstream packages

CGE-Core must not depend on DCGE-Core.

The dependency direction should be:

```text
DCGE-Core
    │
    ▼
CGE-Core public API
```

never:

```text
CGE-Core
    │
    ▼
DCGE-Core
```

CGE-Core's own tests should not require DCGE-Core.

DCGE-Core should test itself against supported CGE-Core releases.

---

# 26. What DCGE-Core should eventually be allowed to assume

After this reengineering, a future DCGE-Core should be able to rely on only a small set of capabilities:

1. construct or obtain a calibrated CGE equilibrium;
2. create an isolated scenario;
3. modify admissible exogenous values;
4. solve the scenario;
5. retrieve equilibrium values;
6. modify the scenario again;
7. solve again;
8. repeat as needed.

DCGE-Core should not need to know:

- how CGE-Core stores `base` or `sim`;
- whether CGE-Core uses deep copies;
- how solver flags are tracked;
- how Pyomo components are internally traversed;
- what private helper functions exist.

This is the key architectural objective of `0.6.0`.

---

# 27. Proposed package layout

A possible target layout is:

```text
cge_core/
│
├── __init__.py
│
├── api.py
│     ├── CGE
│     ├── Equilibrium
│     ├── Scenario
│     └── Result
│
├── engine/
│     ├── solve.py
│     ├── components.py
│     ├── closure.py
│     └── internal workflow machinery
│
├── models/
│     ├── hosoe/
│     ├── ifpri/
│     └── ...
│
├── datasets.py
├── samtools.py
├── exceptions.py
├── data/
└── ...
```

This is a direction, not a requirement to split files merely for aesthetic reasons.

The physical layout should remain as simple as possible while enforcing the public/private boundary.

---

# 28. Migration strategy

The reengineering should be incremental rather than a rewrite.

## Phase 1 — Freeze behavior

Before architectural changes:

- record current benchmark outputs;
- ensure the current full test suite is green;
- preserve reference results for regression testing.

---

## Phase 2 — Introduce the native API

Add:

```text
CGE
Equilibrium
Scenario
Result
```

initially backed by the existing tested implementation where practical.

Do not rewrite the numerical engine unnecessarily.

---

## Phase 3 — Move public examples

Update:

- README;
- notebooks;
- examples;
- documentation;
- tutorials;

to use the new API exclusively.

---

## Phase 4 — Stabilize extension behavior

Add explicit tests for:

- scenario isolation;
- repeated solving;
- value retrieval;
- downstream-safe public interfaces.

---

## Phase 5 — Refactor internals

Only after the public API is working should internal PyCGE-derived workflow machinery be simplified.

Because the public API is now stable, internals can change without affecting users.

---

## Phase 6 — Deprecate inherited vocabulary

Deprecate or remove `PyCGE` according to the chosen compatibility policy.

Remove old documentation references.

Keep historical attribution in provenance and licensing.

---

# 29. Proposed user experience

A representative workflow should eventually look approximately like:

```python
from cge_core import CGE
from cge_core.models import StdCGE
from cge_core import example_data

model = CGE(
    StdCGE(),
    data=example_data("stdcge"),
)

baseline = model.calibrate(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

tariff_reform = baseline.scenario("tariff abolition")
tariff_reform.set("taum", "BRD", 0)
tariff_reform.set("taum", "MLK", 0)

result = tariff_reform.solve()

print(result.value("Z", "BRD"))
print(result.compare(baseline))
```

The exact syntax may change during implementation.

The conceptual model should not.

---

# 30. API qualities we will optimize for

The final API should prioritize:

1. **clarity over cleverness;**
2. **domain language over implementation language;**
3. **composition over giant mutable workflow objects;**
4. **stable capabilities over access to internals;**
5. **scientific transparency over enterprise abstraction;**
6. **reproducibility over convenience shortcuts;**
7. **backward compatibility where inexpensive;**
8. **clean breaks where pre-1.0 cleanup clearly improves the framework.**

---

# 31. Acceptance criteria for CGE-Core 0.6.0

The release is ready when all of the following are true.

- [ ] `CGE` is the canonical public class.
- [ ] Documentation no longer presents `PyCGE` as the main CGE-Core object.
- [ ] Baseline equilibrium, scenario, and result concepts have clear public representations.
- [ ] Users can retrieve equilibrium values without direct Pyomo calls.
- [ ] Scenario modifications are isolated from the baseline.
- [ ] A solved scenario can be modified and solved again.
- [ ] Re-solving behavior is explicitly tested.
- [ ] Public and private APIs are documented.
- [ ] Existing benchmark validation remains green.
- [ ] SAM tooling remains functional.
- [ ] Solver behavior remains reproducible.
- [ ] NIST provenance remains explicit and correct.
- [ ] Licensing notices remain intact.
- [ ] README and notebooks use the new API.
- [ ] Downstream packages can rely on a narrow equilibrium/scenario contract.
- [ ] No dynamic-CGE-specific logic has been added to CGE-Core.

---

# 32. What comes after 0.6.0

Only after this release stabilizes should work begin on a separate:

```text
DCGE-Core
```

repository.

DCGE-Core can then depend on CGE-Core's public equilibrium interface rather than on inherited engine internals.

Its architecture can be:

```text
DCGE-Core
    │
    │ uses
    ▼
CGE-Core equilibrium API
    │
    ▼
solve period t
    │
    ▼
read equilibrium values
    │
    ▼
apply transition equations
    │
    ▼
set next-period exogenous state
    │
    ▼
solve period t+1
```

CGE-Core itself remains unaware that these successive solves represent time.

---

# 33. Guiding principle

The architectural boundary can be summarized as follows.

CGE-Core should implement:

\[
z \longmapsto x^*(z)
\]

where \(z\) is a valid configuration of exogenous conditions and \(x^*(z)\) is the corresponding solved general equilibrium.

A downstream dynamic package may then implement:

\[
x_t = \operatorname{CGE}(z_t, s_t)
\]

and

\[
s_{t+1} = G(s_t, x_t).
\]

The transition function \(G\) does not belong in CGE-Core.

That separation is the foundation for a clean, durable CGE-Core ecosystem.

---

# 34. Bottom line

CGE-Core `0.6.0` should not be a cosmetic rename of `PyCGE`.

It should be a controlled reengineering release that:

- gives CGE-Core its own public identity;
- keeps the tested economics intact;
- establishes explicit equilibrium, scenario, and result abstractions;
- defines a narrow stable extension contract;
- hides implementation details behind a scientific-Python-friendly façade;
- preserves full provenance;
- and creates a safe foundation for future packages such as DCGE-Core.

The implementation should be incremental, test-driven, and deliberately conservative with the economics.
