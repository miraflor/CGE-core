# CGE-Core v0.6 Reengineering
## Phase 0 — Baseline, Architecture, and Safeguard Assessment

**Project:** CGE-Core
**Target release:** v0.6
**Phase:** 0 — Freeze and understand current behavior
**Assessment date:** 27 August 2026
**Repository:** `miraflor/CGE-core`
**Baseline branch:** `main`
**Baseline commit:** `d4dfa7e881339c2101af17caf617dedeb23a7fd8`

---

# 1. Purpose of Phase 0

Phase 0 exists to make the v0.6 reengineering safe.

The purpose is **not** to redesign the API yet, rename classes, move files, reorganize packages, rewrite documentation, or alter model equations. The purpose is to understand what CGE-Core currently does, identify which behaviors are already protected, locate the outward-facing dependencies on the current API, and determine which parts of the repository must be frozen before reengineering begins.

The intended sequence is:

```text
understand current architecture
        ↓
identify public and de facto public interfaces
        ↓
identify benchmark and regression protections
        ↓
map notebooks, documentation, Control Room, packaging, and CI dependencies
        ↓
identify architectural risks
        ↓
freeze the current behavioral baseline
        ↓
only then design the v0.6 public API
```

This phase therefore answers a basic question:

> **What exactly must v0.6 preserve while changing how CGE-Core is presented and used?**

The answer is broader than “the model equations must still solve.” CGE-Core already contains several distinct model families, a stateful workflow engine, a separate IFPRI implementation, a CAMCGE replication benchmark, notebooks, documentation, a browser-based Control Room, packaging rules, and a fairly strong test suite. All of these constrain a safe reengineering.

---

# 2. Executive conclusion

The overall v0.6 reengineering direction is sound.

The repository is in a good position for a major public-API cleanup because:

- the economic models are already separated from the main Hosoe workflow engine;
- the numerical behavior is protected by meaningful tests;
- the current `main` branch is green in CI;
- the documentation build is green;
- Hosoe, IFPRI, and CAMCGE already have independent benchmark protection;
- scenario mutations and reporting behavior already have regression coverage;
- the package is still pre-1.0, so a controlled API transition is feasible.

However, Phase 0 found an important architectural fact:

> **CGE-Core is not one homogeneous engine with several interchangeable model definitions.**

There are currently at least three architectural families:

1. **Hosoe-style models** (`splcge`, `stdcge`) using the `PyCGE` workflow engine;
2. **IFPRI**, which is already a separate clean-room subsystem with its own calibration, model construction, scenarios, solving, reporting, and validation;
3. **CAMCGE**, which is intentionally maintained as a repository-level replication and regression benchmark and uses `PyCGE` internally.

This means the v0.6 public interface should be designed as a **capability layer over heterogeneous backends**, rather than as a cosmetic rename of `PyCGE`.

The main recommendation from Phase 0 is therefore:

> **Introduce a genuinely new public façade additively, preserve the validated internal machinery during migration, and avoid forcing all model families into one internal architecture during v0.6.**

---

# 3. Phase 0 status

## 3.1 Completed

The following Phase 0 tasks are complete:

- [x] Identify the current baseline commit.
- [x] Inspect the repository architecture.
- [x] Map the current `PyCGE` workflow.
- [x] Identify the current formal root API.
- [x] Identify de facto public imports used by examples and notebooks.
- [x] Inspect the IFPRI subsystem architecture.
- [x] Inspect the CAMCGE benchmark architecture.
- [x] Inspect the test structure and CI lanes.
- [x] Confirm that the current baseline is green.
- [x] Identify Hosoe benchmark protections.
- [x] Identify IFPRI benchmark protections.
- [x] Identify CAMCGE replication protections.
- [x] Inspect notebook dependencies.
- [x] Inspect documentation dependencies.
- [x] Inspect Control Room code-generation dependencies.
- [x] Inspect packaging and wheel assumptions.
- [x] Identify the main architectural risks for v0.6.
- [x] Determine which parts should not be refactored during the first API migration stages.

## 3.2 Remaining safeguards before Phase 1 implementation

Two safeguards should still be formalized before actual reengineering code begins:

- [ ] Establish a branch-safe notebook smoke-test procedure.
- [ ] Establish a Control Room generated-code smoke test or reference fixture.

In addition:

- [ ] Create the planned `reengineer-v0.6` branch before implementation begins.

These are small compared with the architectural assessment, but they matter because notebooks and generated code are user-facing surfaces that are currently not protected as strongly as the numerical engine.

---

# 4. Frozen repository baseline

The baseline inspected for Phase 0 is:

```text
branch: main
commit: d4dfa7e881339c2101af17caf617dedeb23a7fd8
```

At the time of inspection, `main` was the only repository branch.

This exact commit should be treated as the reference point for v0.6 behavioral compatibility.

The recommended policy is:

> Any unexpected numerical or behavioral difference between v0.6 work and commit `d4dfa7e...` should be treated as a regression until deliberately explained and justified.

This does **not** mean every internal implementation detail must remain unchanged. It means the validated scientific and user-visible behaviors should remain stable unless intentionally changed.

---

# 5. Current high-level architecture

CGE-Core currently contains several distinct architectural layers.

```text
                           CGE-Core
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
  Hosoe-style models        IFPRI                CAMCGE
  splcge / stdcge        clean-room          replication benchmark
        │                  subsystem                │
        │                     │                     │
   ModelDef classes      calibration.py         CamModelDef
        │                model.py                  │
        │                scenarios.py              │
        ▼                solve.py                  ▼
      PyCGE              reporting.py            PyCGE
 workflow engine         validation.py       replication scripts
        │
        ▼
     Pyomo
        │
        ▼
   NLP solver
```

The repository also contains cross-cutting surfaces:

```text
samtools
datasets / example_data
tests
notebooks
Jupyter Book documentation
Control Room
GitHub Actions
packaging metadata
```

The key Phase 0 finding is that the commonality among the model families is primarily **conceptual**, not yet architectural.

They all implement versions of:

```text
data
→ benchmark/calibration
→ closure
→ equilibrium solve
→ counterfactual/scenario
→ comparison/reporting
```

But they do not all reach that sequence through the same implementation.

---

# 6. Hosoe architecture: model equations versus workflow

The Hosoe models currently have a useful separation of responsibilities.

## 6.1 Model-definition classes contain the economics

Examples include:

```text
cge_core/examples/splcge_model_def.py
cge_core/examples/stdcge_model_def.py
```

These files define model-specific:

- sets;
- parameters;
- calibrated parameters;
- variables;
- constraints;
- objective functions;
- admissible closure information;
- economic equations.

The standard model definition is already substantial. It should not be physically reorganized merely to make the directory tree look cleaner.

## 6.2 `PyCGE` contains the workflow

The main engine lives in:

```text
cge_core/engine.py
```

Its conceptual role is approximately:

```text
load data
→ instantiate abstract model
→ fix numeraire / closure anchor
→ remove declared redundant market equation
→ calibrate / solve benchmark
→ clone benchmark
→ apply scenario changes
→ solve counterfactual
→ compare results
→ export
```

The engine therefore largely manages **workflow and state**, while model definitions contain the economics.

This is an important architectural boundary and should be preserved.

The recommended v0.6 approach is not to move economic equations into the new API layer. The new public API should orchestrate existing model definitions and solving machinery.

---

# 7. Current `PyCGE` state model

`PyCGE` is a stateful workflow object.

Important state includes concepts equivalent to:

```text
data
base
sim
base_results
sim_results
base_calibrated
sim_solved
dict_base
dict_sim
numeraire
```

The current user workflow is:

```python
cge = PyCGE(ModelDef())

cge.model_data(...)
cge.model_instance(...)
cge.model_drop_redundant(...)
cge.model_calibrate(...)

cge.model_sim()
cge.model_modify_sim(...)
cge.model_solve(...)

results = cge.model_compare()
```

This state machine has become much safer than the inherited implementation because it now contains workflow guards and typed exceptions.

However, it is still fundamentally organized around:

```text
one BASE
one current SIM
```

That becomes important for v0.6.

---

# 8. The most important scenario-state limitation

The current engine creates a simulation by deep-copying the baseline:

```text
BASE
  │
  └── deep copy → SIM
```

This is good because it protects the baseline from mutation.

However, the copied scenario is stored in the single engine slot:

```text
self.sim
```

Therefore:

```python
cge.model_sim()
```

creates or replaces the current simulation.

This is sufficient for the existing serial workflow:

```text
create scenario
→ solve
→ copy results
→ create another scenario
→ solve
→ copy results
```

But it is not sufficient for the proposed v0.6 domain model:

```python
baseline = ...
scenario_a = baseline.scenario("A")
scenario_b = baseline.scenario("B")
scenario_c = baseline.scenario("C")
```

Those objects should be able to exist simultaneously.

A superficial wrapper like this would therefore be incorrect:

```python
class Scenario:
    def __init__(self, cge):
        cge.model_sim()
        self._cge = cge
```

because every scenario would still point to the same mutable `cge.sim`.

## Required v0.6 invariant

The public scenario contract should guarantee:

```text
baseline
   ├── scenario A
   ├── scenario B
   └── scenario C
```

with:

- baseline unaffected by all scenarios;
- scenario A unaffected by scenario B;
- scenario B unaffected by scenario C;
- each scenario independently modifiable;
- each scenario independently solvable;
- each solved scenario independently invalidated only when that scenario changes.

This is one of the most important architectural requirements discovered in Phase 0.

---

# 9. Current formal root API

The installed package currently exposes `PyCGE` as the main root class.

Conceptually, the public root surface includes:

```python
PyCGE

CGEError
WorkflowError
ComponentError
DataValidationError
SolveError

example_data
samtools

__version__
```

There is currently no root-level:

```text
CGE
Equilibrium
Scenario
Result
```

This means v0.6 has a clean opportunity to establish a deliberate public object model.

The important requirement is that the new interface should become the **canonical public API**, while `PyCGE` becomes compatibility/internal machinery rather than the conceptual center of the framework.

---

# 10. De facto public API

The formal `__all__` is not the whole compatibility surface.

The README, notebooks, examples, and Control Room teach imports from:

```text
cge_core.examples
```

such as:

```python
from cge_core.examples.splcge_model_def import SplModelDef
from cge_core.examples.stdcge_model_def import StdModelDef
```

This means those paths are effectively part of the current user experience.

The folder name `examples` is awkward if these are real model definitions intended for downstream use.

However, Phase 0 strongly recommends:

> **Do not physically move the model files merely to improve names.**

A safer approach is to introduce a stable import façade:

```python
from cge_core.models import StdCGE
```

or, if the chosen abstraction remains closer to definitions:

```python
from cge_core.models import StdModelDef
```

while initially importing/re-exporting the current implementation internally.

This establishes a better contract without risking a large physical file move during the public-API migration.

---

# 11. IFPRI is architecturally separate

This is the most important finding beyond the `PyCGE` scenario-state issue.

The IFPRI subsystem lives under:

```text
cge_core/ifpri/
```

with modules including:

```text
calibration.py
data.py
inputs.py
model.py
reporting.py
scenarios.py
schema.py
solve.py
validation.py
```

This is not simply another `ModelDef` passed to `PyCGE`.

The subsystem has its own concepts for:

- dataset schema;
- benchmark calibration;
- benchmark model construction;
- macro closures;
- scenario construction;
- scenario enumeration;
- nonlinear solving;
- residual reporting;
- model comparison;
- validation.

It already exports a large explicit public API, including `IfpriScenario`.

Therefore the statement:

> “CGE-Core has one engine and several models”

would be architecturally inaccurate.

A more accurate statement is:

> **CGE-Core contains multiple CGE implementations sharing a project, validation philosophy, and intended user-facing capability model.**

That distinction matters for Phase 1.

---

# 12. Calibration semantics are not uniform

The proposed API previously used a design such as:

```python
baseline = model.calibrate(...)
```

Phase 0 found a semantic problem with making that universal.

For the Hosoe/PyCGE workflow, the operation called:

```text
model_calibrate()
```

effectively brings the benchmark model to its solved calibrated equilibrium.

In the IFPRI implementation, however, the architecture deliberately distinguishes:

```text
algebraic calibration
        ↓
build BASE equilibrium model
        ↓
solve BASE equilibrium
```

This distinction is scientifically meaningful.

Therefore a universal method called:

```python
model.calibrate()
```

may conflate:

1. parameter calibration; and
2. baseline equilibrium solution.

## Phase 1 decision required

Before the public API is frozen, Phase 1 should decide whether the canonical operation should instead resemble:

```python
baseline = model.solve_baseline(...)
```

or:

```python
baseline = model.equilibrium(...)
```

or whether `calibrate()` should be explicitly defined as a high-level operation whose internal meaning differs by backend.

No implementation should commit to this name until the semantic contract is settled.

---

# 13. CAMCGE is deliberately a benchmark

CAMCGE currently lives under:

```text
cam/
```

rather than:

```text
cge_core/
```

This is deliberate.

Its primary role is:

- replication;
- validation;
- regression testing;
- comparison with the published 1987 Cameroon model;
- reproduction of the published policy experiments.

It uses `PyCGE` internally but is not currently presented as a generic installed model family.

Phase 0 therefore recommends:

> **Do not move CAMCGE into `cge_core.models` merely to make the architecture appear uniform.**

Doing so would change:

- package contents;
- wheel policy;
- conceptual model status;
- import paths;
- potentially provenance expectations.

CAMCGE can remain a repository-level benchmark during v0.6.

The new public model namespace should not require every validated benchmark to become an installed first-class model.

---

# 14. Current test architecture

The test suite is one of the strongest safeguards for v0.6.

The repository includes tests for:

- engine workflow;
- simple Hosoe CGE;
- standard Hosoe CGE;
- SAM tools;
- datasets;
- hardening and regression behavior;
- IFPRI calibration;
- IFPRI data and schema;
- IFPRI policy scenarios;
- IFPRI real-solver behavior;
- IFPRI reporting;
- CAMCGE data;
- CAMCGE published-solution replication;
- CAMCGE published policy experiments.

The test architecture therefore protects both:

```text
scientific correctness
```

and:

```text
software behavior
```

This is exactly what is needed for a safe API reengineering.

---

# 15. Hosoe simple-model protections

The simple CGE tests protect properties including:

- successful model instantiation;
- expected number of constraints;
- expected degree-of-freedom structure before redundant-equation removal;
- square system after the redundant equation is removed;
- fixed numeraire;
- reproduction of benchmark SAM quantities;
- normalized benchmark prices;
- solver recovery from perturbed initial values;
- Walras-law behavior;
- goods-market clearing;
- factor-income consistency;
- balanced bundled SAM;
- lower-bound assumptions.

The benchmark quantities include the expected simple-model values for:

```text
X[BRD]
X[MLK]
Z[BRD]
Z[MLK]
```

and normalized prices.

This means the v0.6 API can be changed aggressively around the model without touching these equations or their scientific outputs.

---

# 16. Hosoe standard-model protections

The standard-model tests protect:

- model construction;
- closure dimensionality;
- numeraire behavior;
- benchmark SAM reproduction;
- solver recovery after perturbation;
- Walras-law behavior;
- a canonical tariff-abolition experiment;
- welfare direction under tariff abolition;
- preservation of baseline values after counterfactual solving;
- variable lower bounds.

Expected benchmark values include quantities such as:

```text
Z
Xp
M
E
```

for the bundled standard economy.

The tests also deliberately drive the model through the documented public workflow rather than bypassing the engine.

This is important: the test suite already protects not only equations but parts of the workflow contract.

---

# 17. Engine regression protections

The engine tests protect several previously silent bugs and workflow failures.

Examples include:

- simulation exports accidentally writing baseline values;
- incorrect comparison percentage semantics;
- inconsistent objective-difference sign conventions;
- workflow methods failing with internal exceptions rather than useful errors;
- invalid component handling;
- invalid index handling;
- invalid data-directory handling;
- unsafe closure modification;
- repeated shock undo behavior;
- simulation solved-state invalidation after modification;
- dill round trips;
- comparison DataFrame structure.

These tests are especially valuable because the worst failure mode in scientific software is often not a crash.

It is:

> **plausible but wrong output.**

The existing engine tests were explicitly designed to prevent that class of regression.

---

# 18. One missing contract test: solve → modify → solve again

The current tests verify that after a solved simulation is modified:

```text
sim_solved = False
```

This is good.

However, the v0.6 extension contract intends to guarantee the entire repeated lifecycle:

```text
create scenario
→ set value
→ solve
→ read value
→ set another value
→ solve again
→ read updated value
```

Phase 0 did not identify a dedicated end-to-end test protecting the full repeated solve cycle as a public contract.

This should be added early in v0.6.

It is important for:

- sensitivity analysis;
- scenario sweeps;
- Monte Carlo work;
- iterative algorithms;
- model coupling;
- future dynamic extensions;
- interactive applications.

The repeated-solve contract should not be described as a special dynamic-CGE feature. It is valuable for ordinary static CGE workflows.

---

# 19. IFPRI benchmark protections

The IFPRI test suite is substantial.

The public synthetic IFPRI fixture protects:

- balanced SAM construction;
- successful algebraic calibration;
- benchmark quantities;
- benchmark taxes;
- benchmark foreign saving;
- benchmark government saving;
- benchmark-equation residuals;
- zero degrees of freedom under the BASE closure;
- zero degrees of freedom for policy closures;
- nonzero policy shock construction;
- real NLP solver behavior;
- acceptable residual tolerances;
- Walras residual tolerances.

The IFPRI system therefore already has its own rigorous contract independent of the Hosoe engine.

This reinforces the recommendation not to rewrite IFPRI merely to fit a new façade.

The new public API should adapt to the validated IFPRI machinery, not replace it during the first reengineering stage.

---

# 20. CAMCGE benchmark protections

CAMCGE tests verify the published model replication.

They protect:

- the published base solution;
- 98 published variable levels;
- a strict maximum discrepancy tolerance;
- the deliberately dropped current-account condition;
- three published policy experiments.

This is unusually valuable because it gives CGE-Core an external historical benchmark rather than only internal self-consistency tests.

For v0.6, CAMCGE should therefore be treated as a **regression oracle**.

Any reengineering that causes CAMCGE to diverge from the published reference should be presumed unsafe unless there is a very strong, explicit reason.

---

# 21. Current continuous integration

The current CI is strong and should become the formal v0.6 baseline.

The test workflow includes:

## Structural test matrix

Python versions:

```text
3.9
3.10
3.11
3.12
3.13
3.14
```

The public suite is run without requiring the external official IFPRI source package.

## Real solver lane

A dedicated solver job installs IPOPT and verifies that Pyomo can see it.

The lane then runs:

- public IFPRI solver tests;
- the full public test suite.

The workflow explicitly checks that the full public suite has at least a minimum expected number of tests and zero skips, failures, or errors in the solver lane.

## Lint lane

Ruff checks a narrow correctness-oriented rule set.

## Packaging lane

The workflow builds both:

```text
sdist
wheel
```

and verifies package contents.

This is an excellent foundation for v0.6 because API work can be judged against:

```text
tests
solver
lint
packaging
docs
```

rather than only local manual execution.

---

# 22. Current documentation pipeline

Documentation is built using Jupyter Book.

The GitHub Actions documentation workflow:

```text
checks out repository
→ installs package and docs dependencies
→ runs docs/check_docs.py
→ builds Jupyter Book
→ publishes GitHub Pages
```

The current documentation build is green.

This means documentation changes should remain part of CI during the migration.

However, documentation is not neutral with respect to the old architecture.

It currently explicitly presents:

```text
PyCGE
```

as the Hosoe workflow engine.

Therefore documentation migration is a real architectural surface, not merely copyediting.

---

# 23. Documentation hardcoded dependency: `pycge-architecture.mmd`

The documentation checker includes assumptions about the current architecture diagram.

In particular, it explicitly references a Mermaid source equivalent to:

```text
diagrams/pycge-architecture.mmd
```

Therefore renaming or replacing the PyCGE architecture diagram without updating:

```text
docs/check_docs.py
```

will break documentation CI.

This is an example of why v0.6 should not perform broad search-and-replace renaming without inspecting build tooling.

The migration must include both:

```text
documentation content
```

and:

```text
documentation validation code
```

---

# 24. Notebook inventory

The repository currently contains eight teaching notebooks:

```text
00_start_here.ipynb
01_your_first_cge.ipynb
02_open_economy_cge.ipynb
03_policy_experiments.ipynb
04_bring_your_own_sam.ipynb
05_ifpri_standard_cge.ipynb
06_camcge_replication.ipynb
07_under_the_hood.ipynb
```

These notebooks are not incidental examples. Together they form a progressive teaching path.

Therefore notebook migration must preserve both:

```text
execution correctness
```

and:

```text
pedagogical sequence
```

The API should not be redesigned in a way that makes the teaching materials more complicated merely for architectural purity.

---

# 25. Notebook dependency map

## Notebook 00 — Start Here

Mostly orientation.

Uses:

```text
cge_core
example_data
bundled SAMs
```

Minimal direct dependency on `PyCGE`.

Migration risk: low.

---

## Notebook 01 — Your First CGE

Strong dependency on:

```text
PyCGE
SplModelDef
cge.base
cge.sim
pyomo.environ.value
model_data
model_instance
model_drop_redundant
model_calibrate
model_sim
model_modify_sim
model_solve
model_compare
```

Migration risk: high.

This notebook is an important candidate for the cleanest possible v0.6 introductory API.

---

## Notebook 02 — Open-Economy CGE

Strong dependency on:

```text
PyCGE
StdModelDef
manual closure sequence
base
sim
Pyomo value access
model_compare
```

Migration risk: high.

This notebook will be a good test of whether the v0.6 API genuinely improves usability.

---

## Notebook 03 — Policy Experiments

This notebook is particularly architecturally revealing.

It calibrates one baseline, then repeatedly performs:

```text
model_sim()
→ apply shocks
→ solve
→ copy results
```

for several scenarios.

This works because scenarios are processed serially.

Under the proposed v0.6 domain model, this notebook could instead naturally demonstrate:

```python
tariff = baseline.scenario(...)
tax = baseline.scenario(...)
capital = baseline.scenario(...)
```

and preserve all scenarios simultaneously.

This notebook is therefore an excellent acceptance test for the new `Scenario` object model.

---

## Notebook 04 — Bring Your Own SAM

Depends on:

```text
samtools
PyCGE
StdModelDef
custom account labels
manual closure
```

Migration risk: medium to high.

The SAM tooling itself should remain independent.

---

## Notebook 05 — IFPRI Standard CGE

This notebook does **not** use `PyCGE`.

It uses the independent IFPRI API.

This is one of the clearest pieces of evidence that the project already contains heterogeneous computational backends.

Migration risk: high if the new façade is incorrectly assumed to be universal from the beginning.

Recommended v0.6 treatment:

> Preserve the working IFPRI notebook and API until an explicit adapter is designed.

---

## Notebook 06 — CAMCGE Replication

Uses repository-level CAM replication functions.

It deliberately presents CAMCGE as a replication benchmark.

Migration risk: medium.

It should not be rewritten merely to make CAMCGE appear like a generic installed model.

---

## Notebook 07 — Under the Hood

Intentionally exposes:

```text
PyCGE
Pyomo components
raw model objects
numeraire
degrees of freedom
constraint expressions
calibrated parameters
base
sim
```

This notebook requires special treatment.

Unlike the introductory notebooks, its purpose is precisely to show internals.

Therefore the eventual disappearance of `PyCGE` from ordinary user documentation does **not** necessarily imply that all references to the legacy engine should be erased from this notebook.

Instead, v0.6 may present the distinction:

```text
public domain API
        versus
advanced/raw engine internals
```

That would actually improve the pedagogical value of the notebook.

---

# 26. Critical notebook safeguard issue

The Colab notebooks include setup code that clones or updates the repository and resets the working tree to:

```text
origin/main
```

This creates a serious development trap.

Suppose v0.6 is being developed on:

```text
reengineer-v0.6
```

and Notebook 01 is executed as a smoke test.

The notebook may reset its own working copy to:

```text
origin/main
```

and successfully test the old API instead of the branch under development.

This can produce a false green result.

## Required safeguard

Before notebook migration begins, establish a procedure where notebooks can be executed against:

- the current checkout;
- a specified branch;
- or a specified commit.

The notebook CI/smoke workflow must never silently replace the code under test with `main`.

---

# 27. Control Room architecture

The CGE-Core Control Room is located under:

```text
docs/microsites/control-room/
```

It is deployed as part of the documentation site.

Its core JavaScript application is substantial.

The Control Room is not merely a static explanatory webpage.

It contains model metadata, policy controls, closure information, explanatory content, and Python code generation.

Therefore its relationship to the public API is significant.

---

# 28. Control Room generated code currently depends on `PyCGE`

The generated Hosoe code currently contains logic equivalent to:

```python
from cge_core import PyCGE, example_data

cge = PyCGE(...)
cge.model_data(...)
cge.model_instance(...)
cge.model_drop_redundant(...)
```

and applies shocks through:

```python
cge.model_modify_sim(...)
```

It also reads baseline values directly through:

```text
cge.base
```

and Pyomo `value(...)`.

The Control Room therefore depends on:

- the old class name;
- the old state machine;
- direct engine state;
- current closure workflow;
- current result assumptions.

This is more than a documentation rename.

The generated-code engine itself must migrate.

---

# 29. Control Room version dependency

The Control Room JavaScript also includes a target version equivalent to:

```text
0.5.0
```

This must be updated as part of v0.6.

The version string should ideally be handled in a way that minimizes future duplication or stale hardcoded values.

---

# 30. Required Control Room safeguard

Before Phase 1 implementation, v0.6 should define at least one generated-code fixture.

For example:

```text
model: Hosoe standard CGE
shock: abolish BRD tariff
closure: current default
```

The test should verify that generated code:

1. is syntactically valid;
2. imports only supported public APIs;
3. constructs the intended baseline;
4. constructs the intended scenario;
5. applies the intended shock;
6. solves successfully when solver testing is available.

This would protect a major user-facing surface that currently has less automated coverage than the engine itself.

---

# 31. README dependency

The README currently teaches the legacy workflow directly.

Its conceptual sequence is:

```text
ModelDef
→ PyCGE
→ model_data
→ model_instance
→ model_drop_redundant
→ model_calibrate
→ model_sim
→ model_modify_sim
→ model_solve
→ model_compare
```

It also contains custom-SAM examples using the same engine.

Therefore the README will eventually become one of the main migration surfaces.

The canonical v0.6 README should eventually show only the new user-facing API.

Legacy `PyCGE` usage may remain in a migration or advanced section, but should no longer be the first interface a new user sees.

---

# 32. Package configuration

The project metadata currently declares:

```text
version = 0.5.0
```

Package discovery includes:

```text
cge_core*
```

This excludes repository-level `cam/` from the wheel.

That is consistent with CAMCGE's current role as a replication benchmark.

Phase 0 recommends retaining this distinction during v0.6 unless there is an independent reason to change it.

Do not make packaging broader merely to satisfy a prettier object hierarchy.

---

# 33. Packaging smoke test dependency

The packaging workflow currently smoke-tests imports involving:

```python
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef
```

Therefore the packaging workflow itself must be migrated deliberately.

It should eventually smoke-test the canonical v0.6 API.

During transition, it may test both:

```text
new public API
legacy compatibility API
```

until deprecation policy is settled.

---

# 34. Version fallback inconsistency

The package root currently has a fallback version value that is older than the project metadata.

The package metadata is already:

```text
0.5.0
```

while the fallback in `cge_core.__init__` still reflects an older development version.

This is not a scientific bug, but it is a small packaging inconsistency worth cleaning during v0.6 hardening.

It should not distract from the main API work, but it belongs in the release cleanup checklist.

---

# 35. Deprecation-warning issue

The pytest configuration globally suppresses:

```text
DeprecationWarning
```

If `PyCGE` is retained as a deprecated compatibility surface, relying on ordinary warning output will not provide reliable migration coverage.

Therefore explicit tests should use constructs such as:

```python
with pytest.warns(DeprecationWarning):
    ...
```

if warning-based deprecation is chosen.

Alternatively, the project can intentionally keep `PyCGE` as a supported compatibility name throughout v0.6 without noisy warnings and postpone formal deprecation.

That policy decision belongs in Phase 1.

---

# 36. Main architectural risk: confusing façade with rename

A dangerous implementation would be:

```python
CGE = PyCGE
```

This would change branding but not architecture.

It would fail to provide:

- meaningful `Equilibrium` objects;
- independent scenarios;
- stable value access;
- a clean extension contract;
- backend independence;
- explicit public/private boundaries.

It would also leave inherited state-machine vocabulary exposed.

Therefore:

> **`CGE` must eventually be a real implementation, not a permanent alias.**

However, this does **not** mean the internals must immediately be rewritten.

The recommended migration is composition.

---

# 37. Recommended additive façade

A safer first implementation is conceptually:

```python
class CGE:
    def __init__(self, model, ...):
        self._engine = PyCGE(...)
```

The new façade can then translate domain operations into the existing validated engine.

Conceptually:

```text
public CGE API
     │
     ▼
adapter / façade
     │
     ▼
legacy PyCGE engine
     │
     ▼
existing ModelDef
     │
     ▼
Pyomo
```

This allows v0.6 to improve the public contract while keeping the tested engine stable underneath.

Only after the new interface is working and all outward surfaces have migrated should internal cleanup begin.

---

# 38. Why composition is preferable to early renaming

Renaming:

```python
class PyCGE:
```

to:

```python
class CGE:
```

inside `engine.py` before introducing the new object model would create unnecessary coupling between two separate tasks:

1. changing identity/naming;
2. changing architecture.

If something broke, it would become harder to determine whether the cause was:

- public API translation;
- engine refactor;
- import migration;
- scenario semantics;
- internal rename.

Composition keeps these concerns separate.

That is consistent with the principle:

> **change one architectural dimension at a time.**

---

# 39. Backend-capability architecture

The long-term public API should represent what a CGE implementation can do, not how it happens internally.

A narrow backend-independent capability might be:

```text
create or load model
        ↓
obtain solved benchmark equilibrium
        ↓
create isolated scenario
        ↓
modify admissible exogenous values
        ↓
solve
        ↓
read values
        ↓
compare
        ↓
modify again
        ↓
solve again
```

The Hosoe backend can initially implement this through `PyCGE`.

An IFPRI backend can implement the same public concepts using its own:

```text
calibration
model construction
closure
scenario builder
solver
reporter
```

without pretending internally to be `PyCGE`.

This is the architectural direction Phase 0 recommends for Phase 1.

---

# 40. Proposed public domain objects remain useful

The proposed object vocabulary is still strong:

```text
CGE
Equilibrium
Scenario
Result
```

because these names describe domain concepts better than:

```text
PyCGE
base
sim
model_modify_sim
```

A possible conceptual ownership model is:

```text
CGE
 │
 └── builds/solves → Equilibrium
                       │
                       ├── scenario("A") → Scenario
                       ├── scenario("B") → Scenario
                       └── scenario("C") → Scenario

Scenario.solve()
       │
       ▼
     Result
```

However, Phase 1 must decide the exact lifecycle and whether a solved baseline itself should be a `Result`, an `Equilibrium`, or both.

Phase 0 intentionally does not freeze that syntax.

---

# 41. Public value access requirement

The current engine and notebooks frequently require:

```python
value(cge.base.Z["BRD"])
```

or:

```python
value(cge.sim.Z["BRD"])
```

This exposes raw Pyomo internals to ordinary users and downstream packages.

A stable public accessor should allow something like:

```python
result.value("Z", "BRD")
```

The accessor should support:

- scalar components;
- one-dimensional indexed components;
- multidimensional components;
- clear invalid-component errors;
- clear invalid-index errors;
- ordinary Python numeric outputs.

Raw Pyomo access can remain available as an advanced escape hatch, but it should not be required for normal downstream integration.

This becomes especially important if future backends are not organized identically to `PyCGE`.

---

# 42. Public/private boundary requirement

The new extension contract should ensure that future downstream packages do not need to depend on:

```text
base
sim
internal solved flags
undo dictionaries
private helper methods
direct Pyomo traversal
implementation-specific clone behavior
```

This is a core reason to establish:

```text
Equilibrium
Scenario
Result
```

as explicit domain objects.

The public interface should describe scientific operations.

The backend should remain free to change implementation details later.

---

# 43. Scenario isolation requirements

The following invariants should become explicit tests:

## Baseline protection

```text
scenario changes never mutate baseline
```

## Cross-scenario isolation

```text
scenario A never mutates scenario B
```

## Local result invalidation

```text
modify solved scenario A
→ only A becomes stale
```

## Re-solving

```text
scenario A solve
→ modify A
→ solve A again
```

## Independent simultaneous existence

```text
A, B, C can all remain live objects
```

## Calibration protection

Benchmark-derived calibrated parameters that should remain structurally fixed must not be accidentally changed by ordinary scenario editing.

These should be considered core scientific-software invariants, not implementation details.

---

# 44. Do not add DCGE-specific machinery during v0.6

One motivation for the extension contract is to make future downstream work possible, including dynamic extensions.

However, the base package should not contain:

```text
time loops
capital accumulation rules
intertemporal transition equations
DCGE-only hooks
future-period state machinery
```

merely to anticipate future extensions.

The right preparation is a stable static-equilibrium capability contract.

That contract is already useful for:

- sensitivity analysis;
- iterative simulation;
- scenario sweeps;
- Monte Carlo;
- coupling;
- external orchestration.

Future packages can compose those capabilities without making CGE-Core itself dynamic.

---

# 45. Numerical equations should remain untouched during early v0.6 phases

Phase 0 found no architectural reason to change the validated economic equations.

Therefore the initial reengineering should avoid modifying:

```text
splcge model equations
stdcge model equations
IFPRI economic equations
CAMCGE replication equations
```

unless an independently identified correctness problem emerges.

The public API can be substantially improved without changing these models.

This is one of the strongest safety advantages of the current repository design.

---

# 46. Main risk register

## Risk 1 — Scenario objects secretly share one `sim`

**Severity:** Critical

If the new `Scenario` class simply forwards to `PyCGE.sim`, multiple scenario objects may overwrite one another.

**Mitigation:** Each public `Scenario` must own independent scenario state.

---

## Risk 2 — Universal façade assumes every backend is PyCGE

**Severity:** Critical

IFPRI is already architecturally independent.

**Mitigation:** Design the façade around capabilities, not one engine implementation.

---

## Risk 3 — `calibrate()` conflates two scientific operations

**Severity:** High

IFPRI distinguishes parameter calibration from baseline solving.

**Mitigation:** Settle lifecycle terminology before freezing the Phase 1 API.

---

## Risk 4 — Notebooks silently test `main`

**Severity:** High

Colab setup currently resets to `origin/main`.

**Mitigation:** Create branch/current-checkout notebook execution mode before migration.

---

## Risk 5 — Control Room emits obsolete code

**Severity:** High

The Control Room generates executable `PyCGE` workflows.

**Mitigation:** Add generated-code fixture/smoke coverage.

---

## Risk 6 — Search-and-replace documentation breaks CI

**Severity:** Medium

The docs checker contains architecture-specific assumptions.

**Mitigation:** Migrate documentation source and docs validation together.

---

## Risk 7 — CAMCGE is unnecessarily moved into the wheel

**Severity:** Medium

Aesthetic unification could change packaging semantics.

**Mitigation:** Preserve CAMCGE's benchmark role unless separately justified.

---

## Risk 8 — New API changes result semantics

**Severity:** High

`model_compare()` semantics are already protected.

**Mitigation:** New `Result.compare(...)` should preserve established sign and percentage behavior unless intentionally versioned.

---

## Risk 9 — Deprecation policy is invisible in tests

**Severity:** Low to medium

Warnings are globally filtered.

**Mitigation:** Explicitly test deprecation behavior if used.

---

## Risk 10 — Internal cleanup begins too early

**Severity:** High

Refactoring `engine.py` at the same time as introducing the façade increases regression risk.

**Mitigation:** Keep internals stable until the new public interface and outward migrations are complete.

---

# 47. Recommended changes to the original v0.6 execution plan

The original high-level sequence remains correct:

```text
freeze behavior
→ introduce new API in parallel
→ migrate outward surfaces
→ clean internals last
```

Phase 0 recommends several refinements.

---

## Recommendation A — Keep `PyCGE` internally during the first migration stages

Do not immediately rename the engine class.

Instead:

```text
new public API
    ↓
adapter
    ↓
PyCGE
```

This minimizes risk.

---

## Recommendation B — Make `CGE` real, not an alias

Temporary compatibility may involve aliases elsewhere, but the canonical public implementation should eventually be its own façade.

Avoid:

```python
CGE = PyCGE
```

as the permanent architecture.

---

## Recommendation C — Make scenarios independent objects

This is not cosmetic.

It is the main behavior that the new API must improve over the current single-`sim` engine.

---

## Recommendation D — Resolve calibration terminology before implementation

Do not commit to:

```python
model.calibrate()
```

until its meaning is defined across Hosoe and IFPRI.

---

## Recommendation E — Introduce `cge_core.models` as an import layer first

Do not begin with broad physical file moves.

Example:

```python
from cge_core.models import StdCGE
```

can initially delegate to existing implementation modules.

---

## Recommendation F — Preserve IFPRI architecture

Do not rewrite IFPRI into `PyCGE`.

If a unified user interface is desired, add an adapter later.

---

## Recommendation G — Preserve CAMCGE as benchmark infrastructure

Do not automatically promote it into the installed public model namespace.

---

## Recommendation H — Add notebook smoke protection before notebook migration

A notebook should test the branch or checkout being developed.

---

## Recommendation I — Add generated-code testing for the Control Room

The browser code generator is part of the public API surface.

---

## Recommendation J — Delay engine cleanup

Only after:

```text
new API works
tests protect it
README migrated
notebooks migrated
docs migrated
Control Room migrated
packaging migrated
```

should large internal cleanup begin.

---

# 48. Revised phase sequence

Based on the repository as actually implemented, the recommended sequence is now:

```text
PHASE 0A
Baseline and architecture assessment
        ↓
COMPLETE
```

```text
PHASE 0B
Safeguard outward executable surfaces
- notebook branch-safe smoke procedure
- Control Room generated-code fixture
- create reengineer-v0.6 branch
        ↓
```

```text
PHASE 1
Specify public API precisely
- CGE façade responsibility
- model registry/import surface
- baseline lifecycle
- calibrate vs solve_baseline terminology
- Equilibrium semantics
- Scenario ownership
- Result semantics
- value(...)
- compare(...)
- repeated solve behavior
- backend capability contract
- PyCGE compatibility policy
        ↓
```

```text
PHASE 2
Implement additive public façade
- do not rewrite equations
- do not reorganize engine
- adapt Hosoe backend first
- add new API tests
        ↓
```

```text
PHASE 3
Validate scenario isolation and extension contract
- multi-scenario coexistence
- repeated modification and re-solving
- value access
- compare semantics
- baseline protection
        ↓
```

```text
PHASE 4
Migrate outward surfaces
- README
- examples
- notebooks
- documentation
- Control Room
- packaging smoke tests
        ↓
```

```text
PHASE 5
Formalize extension contract
- document stable supported surface
- public/private boundary
- downstream contract tests
        ↓
```

```text
PHASE 6
Internal cleanup
- retire inherited public vocabulary where appropriate
- simplify engine internals
- reorganize modules only where justified
- preserve provenance
```

---

# 49. What should be frozen before Phase 1

The following should be treated as the behavioral baseline.

## Scientific behavior

- Hosoe simple benchmark values.
- Hosoe standard benchmark values.
- Closure dimensionality.
- Walras-law behavior.
- solver convergence behavior protected by current tests.
- canonical tariff experiment behavior.
- IFPRI calibration targets.
- IFPRI closure behavior.
- IFPRI real-solver residual tolerances.
- CAMCGE 1987 replication tolerances.
- CAMCGE published experiments.

## Workflow behavior

- typed workflow errors;
- component/index validation;
- baseline isolation;
- valid shock modification;
- shock undo behavior;
- solved-state invalidation;
- comparison sign convention;
- percentage-change convention;
- export correctness.

## Package behavior

- supported Python range;
- wheel data inclusion;
- no unintended test leakage into wheel;
- current CAMCGE source-distribution behavior unless intentionally changed.

## Documentation behavior

- Jupyter Book builds;
- current source checker passes;
- GitHub Pages deployment remains healthy.

---

# 50. What is allowed to change in v0.6

The following are intentionally open to improvement:

- canonical class names;
- top-level import paths;
- user-facing method names;
- object ownership model;
- scenario lifecycle;
- result access;
- model namespace;
- documentation vocabulary;
- notebook code style;
- generated Control Room code;
- public/private boundaries;
- compatibility/deprecation policy.

These are exactly the areas v0.6 is meant to improve.

---

# 51. What should not change accidentally

The following must not drift merely because the API is cleaner:

```text
equations
calibrated parameters
benchmark equilibria
closure logic
solver results
comparison semantics
validation tolerances
published-replication results
```

A prettier API is not a valid reason for a different equilibrium.

---

# 52. Recommended Phase 1 design questions

Before writing implementation code, Phase 1 should explicitly answer the following.

## Object model

1. What exactly does `CGE` represent?
2. Is `CGE` configured with a model definition, model family, or backend?
3. What exactly is an `Equilibrium`?
4. Is the solved baseline an `Equilibrium`, a `Result`, or both?
5. What state does `Scenario` own?
6. Can multiple scenarios coexist indefinitely?
7. Does `Scenario.solve()` return a new immutable `Result` or mutate the `Scenario`?
8. What becomes stale after `Scenario.set(...)`?

## Baseline lifecycle

9. Is the canonical operation `calibrate()`, `solve_baseline()`, or something else?
10. How does this map cleanly to IFPRI?
11. Where is closure specified?
12. Should numeraire and redundant-equation details remain visible to ordinary users?

## Values and reporting

13. What does `value(...)` return for scalars?
14. What does it return for indexed components without a complete index?
15. How are multidimensional indices represented?
16. What does `compare(...)` return?
17. Should the current long-form DataFrame remain the canonical comparison representation?

## Backend contract

18. What minimum methods/capabilities must a backend provide?
19. Is a backend protocol required now, or can it remain an internal convention?
20. Which parts are stable for downstream packages?

## Compatibility

21. Does `PyCGE` remain importable in v0.6?
22. Is it deprecated immediately or simply documented as legacy/advanced?
23. How long should old examples remain executable?
24. Which old import paths are explicitly protected?

These questions should be answered in writing before implementation.

---

# 53. Recommended Phase 1 acceptance criteria

Phase 1 should not be considered complete until there is a short architecture/API specification that makes the following unambiguous:

- [ ] canonical root imports;
- [ ] model import surface;
- [ ] baseline creation lifecycle;
- [ ] closure specification;
- [ ] scenario ownership;
- [ ] scenario isolation;
- [ ] repeated solve semantics;
- [ ] result immutability/mutability policy;
- [ ] `value(...)` behavior;
- [ ] `compare(...)` behavior;
- [ ] raw Pyomo escape hatch;
- [ ] backend independence;
- [ ] IFPRI relationship to the façade;
- [ ] CAMCGE status;
- [ ] `PyCGE` compatibility policy;
- [ ] public/private contract.

No code should force unresolved choices before these are settled.

---

# 54. Final Phase 0 verdict

CGE-Core is ready for v0.6 reengineering.

The repository does **not** need a rewrite.

It needs a carefully designed public layer around already validated scientific machinery.

The safest architecture is:

```text
clean domain API
        ↓
small adapter layer
        ↓
existing validated backend implementations
```

rather than:

```text
rename everything
move files
rewrite engine
rewrite models
then hope tests still pass
```

The current tests and benchmarks give the project unusually strong protection for a pre-1.0 scientific package.

The main design challenge is no longer numerical correctness.

It is **state ownership and abstraction**:

- turning one mutable `base`/`sim` workflow into explicit equilibrium/scenario objects;
- preserving independent scenario state;
- exposing stable value access;
- defining a narrow downstream contract;
- supporting heterogeneous model backends without pretending they are internally identical.

The most important Phase 0 architectural rule for everything that follows is therefore:

> **Reengineer the interface first. Preserve the equations and validated backends underneath until the new contract is proven.**

---

# 55. Phase 0 decision summary

| Question | Phase 0 conclusion |
|---|---|
| Rewrite economic equations? | **No.** |
| Split `engine.py` immediately? | **No.** |
| Rename `PyCGE` internally first? | **No.** |
| Make `CGE = PyCGE` permanently? | **No.** |
| Introduce a new public façade? | **Yes.** |
| Use composition initially? | **Yes.** |
| Allow multiple independent scenarios? | **Required.** |
| Treat IFPRI as another `PyCGE` model? | **No.** |
| Preserve IFPRI subsystem? | **Yes.** |
| Force CAMCGE into installed model namespace? | **No.** |
| Add stable `value(...)` access? | **Yes.** |
| Formalize repeated re-solving? | **Yes.** |
| Migrate README/notebooks/docs/Control Room? | **Yes, after the API is stable.** |
| Add notebook branch-safe smoke test? | **Yes, before migration.** |
| Add Control Room generated-code smoke test? | **Yes.** |
| Perform internal cleanup last? | **Yes.** |

---

# 56. Immediate next step

Before beginning Phase 1 implementation:

1. create `reengineer-v0.6`;
2. establish branch-safe notebook execution;
3. establish one Control Room generated-code reference/smoke test;
4. freeze commit `d4dfa7e...` as the behavioral baseline;
5. write the Phase 1 API specification before touching the engine internals.

Only after those safeguards are in place should implementation begin.
