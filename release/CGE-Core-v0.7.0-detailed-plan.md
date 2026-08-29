# CGE-Core v0.7.0 — Detailed Implementation Plan

**Status:** Proposed implementation blueprint  
**Target release:** `v0.7.0`  
**Baseline:** `v0.6.0`, commit `7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2`  
**Primary theme:** Practitioner-first CGE system, first-class bundled models, extensible model authoring, and an experimental human-readable model specification  
**Scientific rule:** Preserve validated economic equations and benchmark results while changing the software architecture around them.

---

# 0. Purpose of this document

This document is intended to be sufficiently self-contained that development can continue in a separate conversation or work session without reconstructing the reasoning that led to the v0.7.0 direction.

It consolidates:

1. the independent technical audit of CGE-Core v0.6.0;
2. the practitioner-first redesign discussion;
3. the decision that CAMCGE must remain a first-class supported model;
4. the requirement that researchers must be able to create their own CGE models;
5. the decision that object-oriented programming must **not** be required of model authors;
6. the proposal for a human-readable Markdown-based CGE model specification;
7. the requirement that CGE-Core hide computational infrastructure from ordinary practitioners;
8. the requirement that existing validated equations not be casually rewritten during the usability refactor;
9. the need to preserve a lower-level Python/Pyomo escape hatch for advanced users and framework developers.

The desired end state is not merely “a cleaner Python package.” The desired end state is:

> **CGE-Core is an open, reproducible, human-oriented CGE modelling system in which ordinary practitioners can run established models with very little code, researchers can construct new models without learning software-engineering patterns, and the underlying numerical machinery remains inspectable and rigorous.**

---

# 1. Executive summary

v0.7.0 should move CGE-Core from a validated research package with a transitional façade into a coherent modelling system with three clearly separated levels.

## Level 1 — Practitioner use

A practitioner choosing a bundled model should specify economics, not infrastructure.

Target:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)

result = reform.solve()
result.summary()
```

A practitioner bringing her own SAM should ideally write:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("philippines_sam.csv")
base = economy.solve()
```

The practitioner should not need to know about:

- Git branches or tags;
- `subprocess`;
- `sys.path`;
- repository directories;
- `DataPortal`;
- Pyomo model-instance mechanics;
- IPOPT executable locations;
- AMPL modules;
- PATH manipulation;
- Colab detection;
- internal parameter names where a semantic policy helper is available;
- the redundant Walras equation for the canonical closure of a bundled model.

## Level 2 — Model authoring

A researcher who wants to create a new CGE model should need to understand:

- sets;
- data;
- parameters;
- calibration;
- variables;
- equations;
- closure;
- shockable objects;
- model-specific economic conventions.

She should **not** be required to understand:

- inheritance;
- abstract base classes;
- `self`;
- protocols;
- factories;
- decorators;
- internal engine state;
- framework-specific object hierarchies.

The initial Python authoring interface should therefore be functional/declarative rather than OOP-first.

Longer-term—and experimentally in v0.7.0—the preferred authoring surface should become a human-readable `.cge.md` model specification.

## Level 3 — Framework internals

CGE-Core itself may continue to use classes, dataclasses, adapters, Pyomo objects, solver resolvers, cloning, validation objects, and other software-engineering machinery.

That complexity belongs below the waterline.

---

# 2. Baseline: what v0.6.0 already establishes

The v0.7.0 refactor must begin from the premise that v0.6.0 is not a failed scientific implementation. The independent audit found the opposite.

## 2.1 Hosoe simple CGE

- Replicates.
- Independently verified.
- Reachable from an installed package.
- Exercised by CI.
- No substantive audit issue found.

## 2.2 Hosoe standard CGE

The audit independently verified that:

- the benchmark returns the SAM values;
- the tariff-abolition counterfactual matches Hosoe's published listing;
- the perturbation test is substantive;
- three independent solves were bitwise identical;
- two unrelated root-finding algorithms recover the IPOPT solution at machine precision;
- 35 of 35 successful random multi-start runs reached the same equilibrium;
- no run converged to a distinct equilibrium.

This is a valuable scientific baseline. v0.7.0 must not weaken it.

## 2.3 CAMCGE

CAMCGE is one of the strongest parts of the repository scientifically.

The audit independently verified:

- base `omega`;
- 98 reported variable levels;
- a near-zero current-account gap on the dropped equation;
- all three counterfactual experiments;
- selected published percentage changes;
- solver independence across root-finding algorithms.

The issue is not that CAMCGE is untrustworthy. The issue is that it is packaged incorrectly: it is currently outside `cge_core/` and therefore absent from the wheel.

**v0.7.0 decision:** CAMCGE is a first-class supported bundled model and must be importable after `pip install cge-core`.

## 2.4 IFPRI

The current status must be described precisely.

What exists:

- IFPRI model code;
- calibration machinery;
- closure/scenario machinery;
- reporting;
- synthetic independently authored IFPRI-format data used in tests.

What the audit could not externally verify:

- official-source benchmark construction;
- official-source base solve;
- official-source calibration tests;
- official-source SAM/input tests;
- most policy scenarios.

The official IFPRI replication claim therefore remains asymmetric because it depends on external licensed material.

**v0.7.0 must not pretend that moving the synthetic fixture into the package solves the official-source verification problem.**

It solves a different problem:

> installed users gain a runnable, redistributable IFPRI-format demonstration economy and CI can exercise more of the IFPRI code path.

Official IFPRI replication must remain clearly labelled according to what is externally reproducible and what requires licensed source material.

---

# 3. Product doctrine for v0.7.0

These principles should guide every implementation decision.

## 3.1 The user specifies economics; CGE-Core handles computation

If a line of ordinary user code exists only because Python, Pyomo, Colab, Git, IPOPT, PATH, or repository layout needs it, ask whether CGE-Core can absorb it.

Default answer: yes.

## 3.2 Easy use must not mean opaque economics

CGE-Core should hide software plumbing, not economic assumptions.

A user should be able to inspect:

- which closure is active;
- which variable is fixed;
- which equation is dropped;
- what was shocked;
- benchmark values;
- scenario values;
- solver status;
- residual information;
- calibration metadata.

“Simple” must not mean “black box.”

## 3.3 Bundled models may share an interface without sharing equations

Hosoe standard CGE, CAMCGE, and IFPRI have different structures and closure conventions.

The framework should unify the lifecycle:

```text
load/build → solve benchmark → create scenario → apply shock → solve → inspect result
```

It should **not** force all models into one universal economic equation template.

## 3.4 Closure is model-owned

The engine should not assume that every CGE model uses the Hosoe closure convention.

A bundled model should declare its canonical/default closure.

The ordinary practitioner writes:

```python
base = economy.solve()
```

The model knows its own default closure.

Advanced users may override closure deliberately.

## 3.5 Economic meaning must never be inferred from spelling

The current engine rule:

```python
if name == "sam" or name.endswith("0") or (base and name == "FF"):
```

must disappear from the model-extension contract.

A parameter is benchmark-only because the model declares it benchmark-only, not because its name happens to end in `0`.

## 3.6 Model authors should learn modelling, not OOP

The documented custom-model interface must not begin with:

```python
class MyCGE(CGEModel):
```

OOP may exist internally or as an advanced optional interface.

The normal authoring path should be functional/declarative, and eventually `.cge.md`.

## 3.7 Human-readable does not mean natural-language execution

For `.cge.md`:

- prose is documentation;
- formal fenced blocks are executable;
- prose never silently changes computation;
- no LLM should infer missing equations from prose;
- parsing and compilation must be deterministic.

## 3.8 Preserve validated economic code during architectural changes

Do not mix equation changes, calibration changes, API refactoring, packaging changes, and state-management changes inside one unreviewable diff.

When moving or splitting validated code, use mechanical transformations and regression tests.

## 3.9 Prefer transparent code over clever abstraction

The audit explicitly found that `StdModelDef.model()` is long but not spaghetti.

Do **not** respond by creating a generic CES factory hierarchy, metaprogramming layer, or deep inheritance tree merely to reduce line count.

Mechanical decomposition for reviewability is desirable. Abstraction for its own sake is not.

## 3.10 Backward compatibility matters

v0.7.0 is a minor release.

Existing v0.6 public workflows should continue to work where reasonably possible, especially:

```python
CGE(...)
solve_benchmark(...)
scenario.set(...)
```

New practitioner APIs should be additive.

If an old import path must move, retain a compatibility shim and issue a deprecation warning rather than abruptly breaking it.

---

# 4. Explicit v0.7.0 goals

v0.7.0 should accomplish the following.

## Goal A — Make installed CGE-Core genuinely usable

After installation, users should be able to run SimpleCGE, StandardCGE, CAMCGE, and a redistributable IFPRI-format example.

No advertised bundled family should vanish merely because the user installed a wheel rather than cloned the repository.

## Goal B — Establish one coherent public lifecycle

For bundled models:

```text
construct → solve → scenario → shock → solve → result
```

The model-specific economics remain separate internally.

## Goal C — Remove infrastructure from normal notebooks and examples

Public teaching/practitioner notebooks should not contain Git checkout logic, solver PATH plumbing, or repository bootstrapping.

## Goal D — Centralize numerical backend resolution

There should be one authoritative solver-resolution subsystem.

## Goal E — Fix scenario state architecture

Creating one scenario should create one independent scenario model, not deep-copy an entire engine and then deep-copy the base again.

## Goal F — Make closure metadata explicit and model-specific

Bundled models declare their default closure.

## Goal G — Formalize model metadata

At minimum:

- benchmark-only components;
- default closure;
- required data;
- optionally semantic shock metadata.

## Goal H — Make custom-model authoring possible without OOP

Provide a functional/declarative Python model-author interface.

## Goal I — Introduce an experimental `.cge.md` format

Ship the first deterministic, documented, deliberately limited version of a human-readable CGE specification.

The experimental format should prove the concept without forcing a rewrite of validated StandardCGE, CAMCGE, or IFPRI implementations.

## Goal J — Convert audit findings into executable safeguards

Where the audit found external evidence that is currently only documented, wire it into tests or validation artefacts.

---

# 5. Non-goals for v0.7.0

The following should **not** become release blockers.

## 5.1 Rewriting all bundled models in `.cge.md`

Do not rewrite validated Python/Pyomo implementations merely to prove the DSL.

The DSL should begin with a small reference model, preferably `splcge` or another deliberately small example.

## 5.2 Creating a universal CGE ontology

Do not attempt to standardize every possible institution type, closure, tax, production nest, trade structure, dynamic mechanism, or welfare measure.

v0.7.0 needs a model contract, not a theory of all CGE models.

## 5.3 Building a replacement for GAMS in general

The proposed language is a CGE-oriented modelling specification, not a universal algebraic modelling language.

## 5.4 Solver bundling at any cost

The UX goal is:

```python
economy.solve()
```

not necessarily “CGE-Core ships a portable IPOPT binary inside every wheel.”

If solver distribution cannot be made reliable, keep installation explicit but keep solver selection invisible during ordinary use.

## 5.5 Broad style cleanup

Do not spend v0.7.0 modernizing every annotation, line length, or single-letter economic symbol.

## 5.6 A full IFPRI re-verification without source access

The redistributable synthetic economy improves usability and code-path coverage, but cannot substitute for the official licensed benchmark.

---

# 6. Target user classes

v0.7.0 should be designed around four distinct users.

## 6.1 Practitioner using a bundled model

Needs clean model construction, SAM/data input, sensible default closure, semantic shocks, automatic solver selection, and readable results.

Does not need Pyomo internals, model-definition classes, repository layout, or solver executable management in every script.

## 6.2 Teacher or learner

Needs one-command install or one Colab install cell, small runnable examples, visible economic structure, and no setup boilerplate.

## 6.3 Research model author

Needs custom sets, calibration, equations, closure, model metadata, shockable components, and transparent Pyomo escape hatches.

Should not need OOP.

## 6.4 CGE-Core/framework developer

Needs lower-level engine access, adapters, solver controls, validation infrastructure, snapshots, profiling, and debugging hooks.

This is where complexity is allowed.

---

# 7. Target public API

## 7.1 Bundled model entry points

Proposed:

```python
from cge_core import (
    SimpleCGE,
    StandardCGE,
    CamCGE,
    IFPRICGE,
)
```

### SimpleCGE
Teaching, smoke tests, DSL reference implementation.

### StandardCGE
Canonical Hosoe standard model and normal practitioner use.

### CamCGE
First-class supported Cameroon model and demonstration that the shared interface survives a larger model.

### IFPRICGE
IFPRI family interface, redistributable synthetic example, and official-source path where licensed source is available.

## 7.2 Benchmark solve

```python
base = StandardCGE.example().solve()
```

or:

```python
economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

No ordinary solver argument. No ordinary closure argument when the canonical model closure is intended.

## 7.3 Scenario creation

```python
reform = base.scenario("Tariff abolition")
```

Scenario must be independent of `base` and all sibling scenarios.

## 7.4 Semantic shocks

Examples:

```python
reform.tariff("BRD", 0)
reform.endowment("CAP", change=0.10)
reform.production_tax("MAN", 0.05)
```

Retain generic advanced access:

```python
reform.set("taum", "BRD", 0)
```

Semantic helpers must be thin, model-specific mappings rather than a universal tax ontology.

## 7.5 Results

Minimum target:

```python
result.summary()
result.compare(base)
```

Potential views:

```python
result.output
result.prices
result.trade
result.households
result.government
result.welfare
result.raw
```

Only expose common views where meanings are honest across models.

## 7.6 Advanced access

Preserve an escape hatch to raw model/solver objects. Simplification must not remove research flexibility.

---

# 8. Proposed package architecture

```text
cge_core/
├── __init__.py
├── api.py
├── economy.py
├── equilibrium.py
├── solvers.py
├── data.py
├── model_spec.py
├── reporting.py
│
├── models/
│   ├── simple/
│   │   ├── model.py
│   │   └── data/
│   ├── standard/
│   │   ├── model.py
│   │   └── data/
│   ├── camcge/
│   │   ├── model.py
│   │   ├── experiments.py
│   │   └── data/
│   └── ifpri/
│       ├── model.py
│       ├── calibration.py
│       ├── closure.py
│       ├── scenarios.py
│       └── data/
│           └── synthetic/
│
├── authoring/
│   ├── module_adapter.py
│   └── metadata.py
│
├── spec/
│   ├── parser.py
│   ├── grammar.py
│   ├── ast.py
│   ├── compiler.py
│   ├── validation.py
│   └── errors.py
│
└── advanced/
    └── pycge.py
```

Repository-level material:

```text
examples/
├── tariff_reform.py
├── cameroon_experiment.py
├── own_sam.py
├── custom_python_model/
└── custom_markdown_model/

notebooks/
├── 01_first_cge.ipynb
├── 02_policy_experiments.ipynb
├── 03_your_own_sam.ipynb
├── 04_camcge.ipynb
├── 05_ifpri.ipynb
├── 06_build_a_model.ipynb
└── 90_internals.ipynb

validation/
├── hosoe/
├── camcge/
└── ifpri/

tests/
```

This is a target architecture, not a requirement to move every file in one commit.

---

# 9. CAMCGE plan

## 9.1 Status

Treat CAMCGE as:

> **supported bundled model + separately maintained validation evidence**

Implementation belongs inside the installed package. Published-target artefacts and replication reports belong under `validation/`.

## 9.2 Packaging

Move or wrap the current top-level `cam/` implementation under:

```text
cge_core/models/camcge/
```

If a direct move is risky, create package-level wrappers first, then mechanically relocate later.

## 9.3 Compatibility

The supported path becomes:

```python
from cge_core import CamCGE
```

Retain compatibility for old repository-level imports where practical.

## 9.4 Default closure

CAMCGE declares its own canonical closure explicitly. Do not force it through Hosoe-specific `numeraire=`/`redundant=` conventions.

## 9.5 Experiments

Provide a clean lifecycle example while preserving published experiments as validation tests.

## 9.6 Audit-specific corrections

- remove hard-coded `solver="cyipopt"` default;
- use central solver resolver;
- add explanatory pointer for the disclosed experiment-1 exclusions;
- retain known-residual disclosure;
- preserve current regression tolerances unless scientific evidence justifies change.

## 9.7 Acceptance criteria

A clean wheel install can run:

```python
from cge_core import CamCGE
base = CamCGE.example().solve()
```

and reproduce the frozen validated base result.

---

# 10. IFPRI plan

## 10.1 Relocate redistributable synthetic economy

Move the independently authored synthetic fixture from `tests/` into installed package data/code.

Preferred conceptual destination:

```text
cge_core/models/ifpri/data/synthetic/
```

## 10.2 Public example

```python
from cge_core import IFPRICGE

economy = IFPRICGE.synthetic()
base = economy.solve()
```

The name must make clear that it is synthetic, not the official benchmark.

## 10.3 Official source path

Retain an explicit path for users who possess the required source, e.g.:

```python
economy = IFPRICGE.from_official_source(...)
```

Do not silently substitute synthetic data.

## 10.4 CI

Use synthetic data to exercise package import, model construction, relevant calibration/closure paths, scenario machinery, reporting, and solver integration.

## 10.5 Scientific claim discipline

Clearly separate externally reproducible synthetic/code-path evidence from official-source replication requiring licensed material.

## 10.6 Focused review

Because the audit did not review IFPRI solve/closure-switching logic, include a dedicated review and tests before refactoring those internals aggressively.

---

# 11. Solver subsystem

## 11.1 Current problem

Solver discovery/selection is duplicated across the core engine, IFPRI, examples, CAMCGE, and notebooks.

## 11.2 Create one authoritative resolver

Proposed module:

```text
cge_core/solvers.py
```

Responsibilities:

1. detect supported backends;
2. respect explicit advanced override;
3. choose a sensible default;
4. provide consistent errors;
5. return reproducibility metadata;
6. avoid incompatible silent fallback;
7. expose diagnostics.

Potential internal functions:

```python
resolve_solver(preferred=None)
solve_model(model, solver=None, options=None)
solver_info()
```

## 11.3 Ordinary workflow

```python
result = economy.solve()
```

## 11.4 Advanced override

```python
result = economy.solve(solver="ipopt")
```

Optional solver options remain advanced.

## 11.5 Missing backend

Detect early, explain clearly, and provide supported installation routes. Do not make raw backend traceback the primary user message.

## 11.6 Solver-install feasibility spike

Test Windows, Linux, macOS, Colab/Linux, and supported Python versions.

Determine whether:

```bash
pip install "cge-core[solver]"
```

can be made reliable. If not, document the shortest truthful installation path.

The minimum product promise is:

> Once the numerical backend is available, ordinary scripts contain no backend plumbing.

## 11.7 Diagnostics

Consider:

```bash
cge doctor
```

or an equivalent Python helper for version, platform, detected solver, and executable information.

---

# 12. Scenario state architecture

## 12.1 Current issue

v0.6 scenario creation deep-copies the whole engine and then deep-copies the copied base model again.

## 12.2 Target

```text
Benchmark model
├── clone → Scenario A
├── clone → Scenario B
└── clone → Scenario C
```

Each scenario should own exactly one independent model clone.

## 12.3 Requirements

- Scenario A cannot mutate benchmark.
- Scenario A cannot mutate Scenario B.
- undo restores scenario state.
- benchmark/result snapshots remain immutable from user perspective.
- identity and value tests cover cloning.
- no redundant base copy exists merely for legacy signatures.

## 12.4 Migration

Introduce an adapter/new path first, preserve compatibility wrappers, prove numerical equivalence, then remove redundant state.

## 12.5 Performance validation

Use a model larger than StandardCGE to verify clone count and object structure. Avoid fragile wall-clock CI thresholds.

---

# 13. Explicit model metadata

Create an internal `ModelSpec`-like structure. Users normally do not instantiate it.

Possible fields:

```text
name
family
default_closure
benchmark_only
required_data
semantic_shocks
result_views
validation_metadata
```

## 13.1 Benchmark-only components

Replace name inference with explicit declarations.

## 13.2 Required data

Models declare what they require; the data layer satisfies the declaration from packaged data, SAMs, files, or mappings.

## 13.3 Default closure

A model declares a closure function or structured specification.

## 13.4 Semantic shocks

Optional model-specific mapping from concepts such as tariff/endowment to internal components.

Generic `.set()` remains available.

---

# 14. Closure design

## 14.1 Ordinary use

```python
base = StandardCGE.example().solve()
```

applies StandardCGE's declared canonical closure.

## 14.2 Inspection

Expose human-readable closure information, for example:

```text
Closure: Hosoe standard benchmark
Fixed:
  pf[LAB] = 1
Dropped:
  eqpf[LAB]
```

CAMCGE reports its own closure rather than imitating Hosoe.

## 14.3 Advanced override

Do not finalize the exact API until it has been tested against StandardCGE, CAMCGE, and IFPRI.

## 14.4 DSL

MVP may support:

```cge
fix pf[LAB] = 1
drop factor_market[LAB]
```

Do not encode every IFPRI macro-closure switch in grammar version 0.

---

# 15. Data and SAM interface

## 15.1 Principle

Current conversion to multiple internal CSV/DataPortal structures may remain temporarily, but it is not a practitioner responsibility.

## 15.2 Target

```python
economy = StandardCGE.from_sam("sam.csv")
```

Loader responsibilities:

1. read SAM;
2. validate balance;
3. determine or receive account roles;
4. construct required internal representation;
5. return actionable errors.

## 15.3 Explicit role metadata

Support:

```python
StandardCGE.from_sam(
    "sam.csv",
    factors=["LAB", "CAP"],
    household="HOH",
    government="GOV",
    investment="INV",
    rest_of_world="ROW",
)
```

Infer only when unambiguous.

## 15.4 Errors

Prefer domain-specific messages over raw `KeyError`/Pyomo exceptions.

## 15.5 Internal conversion

v0.7.0 may reuse `samtools`; later releases may remove intermediate CSV/DataPortal mechanics.

---

# 16. Custom model authoring: Python path

## 16.1 Primary documented style

Functional/declarative:

```python
def build_model(data):
    ...
    return model

def apply_default_closure(model):
    ...

benchmark_only = {...}
```

Optional metadata can be module-level declarations.

## 16.2 Do not require

```python
class MyModel(CGEModel):
    ...
```

## 16.3 Internal adapter

```text
user functions + declarations
          ↓
module adapter
          ↓
internal ModelSpec
          ↓
engine
```

## 16.4 Optional advanced class API

A class-based extension can exist for software developers, but it should not be the introductory model-authoring path.

## 16.5 Pyomo

Python authors may still use Pyomo directly. The non-Python authoring path is `.cge.md`.

---

# 17. Experimental human-readable `.cge.md` format

Suggested extension:

```text
my_model.cge.md
```

## 17.1 Core idea

A `.cge.md` file is simultaneously human-readable documentation, model specification, reproducibility artefact, GitHub-readable document, and teaching material.

Markdown prose documents the economics.

Fenced `cge` blocks define executable semantics.

## 17.2 Fundamental rule

> **Prose never controls computation.**

No LLM or heuristic should infer missing equations from surrounding prose.

## 17.3 Example

````markdown
# Small Open-Economy CGE

## Sets

```cge
goods = [BRD, MLK]
factors = [CAP, LAB]
```

## Data

```cge
SAM = "sam.csv"
```

## Parameters

```cge
X0[i in goods] = SAM[i, HOH]
F0[h in factors, i in goods] = SAM[h, i]
```

## Variables

```cge
X[i in goods] >= 0
F[h in factors, i in goods] >= 0
px[i in goods] > 0
pf[h in factors] > 0
```

## Factor market

```cge
factor_market[h]:
    sum(i in goods, F[h,i]) = FF[h]
```

## Closure

```cge
fix pf[LAB] = 1
drop factor_market[LAB]
```

## Policy variables

```cge
shockable:
    FF
```
````

## 17.4 MVP language features

Support only what the first reference CGE genuinely needs:

- sets;
- indexed declarations;
- parameters;
- variables and bounds;
- named equations;
- summation;
- product;
- fix;
- drop/deactivate;
- shockability declaration;
- external data reference.

## 17.5 Explicitly excluded from MVP

Do not implement merely for familiarity:

- GAMS `..`;
- `=e=`;
- `=l=`;
- `=g=`;
- `.fx`;
- `$` conditions;
- GAMS `/ ... /` syntax;
- `.gms` compatibility;
- natural-language equation interpretation;
- unrelated general optimization features.

## 17.6 Parser pipeline

```text
Markdown
  ↓
extract fenced cge blocks
  ↓
tokenizer/parser
  ↓
AST
  ↓
semantic validation
  ↓
internal ModelSpec
  ↓
Pyomo compiler
  ↓
ordinary CGE-Core lifecycle
```

## 17.7 Markdown handling

Do not build a full Markdown implementation. Reliably identify fenced `cge` and later `cge-scenario` blocks using a CommonMark-compatible approach.

## 17.8 Parser choice

Compare a small hand parser with a lightweight grammar library. Choose based on maintainability and error quality, not dependency ideology.

## 17.9 AST

Create nodes such as:

```text
SetDecl
DataDecl
ParameterDecl
VariableDecl
EquationDecl
SumExpr
ProductExpr
FixStmt
DropStmt
ShockableDecl
```

Do not compile raw strings directly to Pyomo.

## 17.10 Semantic validation

Detect before solving:

- duplicate declarations;
- unknown sets/symbols;
- invalid indices;
- undeclared index variables;
- invalid closure references;
- invalid shockability declarations;
- unsupported syntax.

## 17.11 Error quality

Aim for:

```text
my_model.cge.md:47:12

Unknown symbol `factorz`.

Did you mean `factors`?
```

rather than a Pyomo stack trace.

## 17.12 Compilation target

The DSL must compile into the same internal lifecycle as bundled Python models, not a second engine.

## 17.13 First reference model

Progression:

1. tiny toy equilibrium;
2. Hosoe simple CGE or equivalent;
3. numerical equivalence;
4. grammar expansion.

Do not begin with CAMCGE.

## 17.14 Release status

Label clearly:

> **Experimental model specification — syntax may evolve before 1.0.**

## 17.15 CLI

If sufficiently stable:

```bash
cge check my_model.cge.md
cge solve my_model.cge.md
```

`cge check` is particularly useful and may be prioritized before richer CLI execution.

---

# 18. `.cge.md` intellectual-property guardrails

This is a product/design precaution, not legal advice.

## 18.1 Independent design

Describe the format as an independently designed declarative CGE specification, not “GAMS syntax in Markdown.”

## 18.2 Mathematical concepts

Build from general algebraic/economic modelling concepts: sets, parameters, variables, equations, sums, products, bounds, closure, and scenarios.

## 18.3 Avoid unnecessary syntax compatibility

Do not intentionally clone distinctive GAMS syntax when an independent notation works.

## 18.4 No copied implementation

Do not copy source, binaries, internal implementation, or reverse-engineered code.

## 18.5 No copied manuals/examples

Write documentation independently and respect provenance/licensing of reference models and data.

## 18.6 Branding

Do not imply affiliation with or endorsement by GAMS.

## 18.7 Provenance

Maintain source citation, implementation provenance, licensing status, validation evidence, and data provenance for bundled/reference models.

Consider legal review before declaring the language stable if the project becomes sufficiently significant.

---

# 19. Internal audit fixes

## 19.1 Remove `endswith("0")`

Replace with explicit benchmark-only metadata.

Test that a legitimately shockable parameter ending in `0` is allowed when declared.

## 19.2 Restructure `_modify`

Split responsibilities:

```text
resolve component
validate target/index
validate bounds
capture state
apply
restore
```

Preserve rollback guarantees.

## 19.3 Split `StdModelDef.model()` mechanically

Possible sections:

```text
_declare_sets
_declare_benchmark_data
_declare_benchmark_magnitudes
_declare_calibrated_parameters
_declare_variables
_declare_equations
_declare_objective
```

Preserve order, equations, names, initialization, and meaningful comments.

## 19.4 IFPRI long functions

Refactor only after stronger tests.

## 19.5 Exception chaining

Correct the audit-identified exception paths with proper `raise ... from ...`.

## 19.6 Namespace cleanup

Prevent accidental `PackageNotFoundError` exposure.

## 19.7 Model placement

Move/wrap supported StandardCGE implementation out of `cge_core/examples/`.

## 19.8 Ruff

Fix high-value correctness issues, not broad cosmetic churn. Preserve source-faithful economic notation where reasonable.

---

# 20. Validation upgrades

## 20.1 Freeze v0.6 numerical baseline

Before major refactors capture:

### StandardCGE
- benchmark;
- tariff abolition;
- utility/welfare;
- selected calibration values if stable;
- solver status/residual.

### CAMCGE
- `omega`;
- published levels;
- selected experiment targets;
- Walras/current-account residual;
- disclosed exclusions.

### SimpleCGE
- existing behavioural results.

### IFPRI
- synthetic expectations;
- official-source expectations only in optional licensed lane.

## 20.2 Wire `listA1.csv` into tests

Use the shipped external reference instead of relying only on transcribed constants.

## 20.3 Record solver independence

Store the audit's root-finder evidence in validation documentation and optionally a reproducible validation script.

## 20.4 Record multi-start evidence

Document 40 starts, 35 successful, 35 agreeing, 5 infeasible, 0 distinct equilibria, and the interpretation.

## 20.5 Baseline artefact

If `validation/v0.6-baseline.json` remains, make a test consume it. Otherwise remove it.

## 20.6 Tolerances

Centralize by benchmark. Any tolerance change must be explicit and justified.

---

# 21. Test-suite redesign

## 21.1 Retire prose-policing tests

Remove migration-era tests that assert exact documentation wording.

Keep tests for version consistency, public symbols, installability, examples, notebooks, and behaviour.

## 21.2 Reverse notebook invariant

Ordinary public notebooks should not contain:

- `git clone`;
- `git fetch`;
- `git reset --hard`;
- `CGE_CORE_REF`;
- bootstrap `subprocess`;
- `sys.path` manipulation;
- `amplpy.modules`;
- PATH injection;
- repository-root `chdir` gymnastics.

A Colab notebook may contain one installation cell.

## 21.3 API tests

Exercise bundled model constructors and solves.

## 21.4 Scenario isolation

Test base immutability, sibling isolation, undo, and snapshot stability.

## 21.5 Closure tests

Every bundled model declares and solves with its default closure and exposes it.

## 21.6 Semantic shock tests

Each helper must equal the corresponding generic `.set()` operation.

## 21.7 Custom Python model test

Use a no-class third-party-style model.

## 21.8 `.cge.md` tests

Separate parser, AST, semantic, compiler, end-to-end, and prose-inertness tests.

---

# 22. Results API

## 22.1 Preserve immutable snapshots

Keep snapshot safety. Optimize redundant model cloning first.

## 22.2 Human-facing summary

`result.summary()` should include model, scenario, solver, status, headline indicators, warnings, and changes from benchmark where meaningful.

## 22.3 Comparison

`result.compare(base)` should return a structured comparison object/table.

## 22.4 Raw access

Retain `result.raw` or equivalent.

---

# 23. Documentation and notebooks

## 23.1 Documentation structure

```text
Start here
Install
Your first CGE
Run a policy scenario
Bring your own SAM
Bundled models
    SimpleCGE
    StandardCGE
    CAMCGE
    IFPRI
Build your own model
    .cge.md
    Python authoring
Advanced
    closures
    solver control
    raw Pyomo access
Validation
Developer documentation
```

## 23.2 Notebook sequence

### `01_first_cge.ipynb`
First successful solve, no Git/setup plumbing.

### `02_policy_experiments.ipynb`
Benchmark → scenario → semantic shock → compare.

### `03_your_own_sam.ipynb`
SAM and account mappings.

### `04_camcge.ipynb`
Larger supported model and published experiment.

### `05_ifpri.ipynb`
Synthetic example and licensed-source status.

### `06_build_a_model.ipynb`
`.cge.md` experimental path plus functional Python fallback if needed.

### `90_internals.ipynb`
Pyomo/engine/solver internals.

## 23.3 README

Lead with the shortest compelling practitioner workflow.

Do not make the README a migration history.

## 23.4 Historical material

Archive/de-emphasize old RFCs and migration scaffolding from the primary user path.

---

# 24. Packaging

## 24.1 Wheel contents

Must include core, supported bundled models, required example data, synthetic IFPRI data, and reference `.cge.md` examples if shipped.

Must exclude tests, licensed IFPRI source, and accidental repository clutter.

## 24.2 sdist/wheel parity

Test both. The v0.6 CAMCGE problem proves sdist success is not enough.

## 24.3 Clean environment

Build wheel, install in clean env, import all public model families, and run redistributable examples in solver CI.

## 24.4 Metadata

Package description must match what installed users can actually run.

---

# 25. Backward compatibility

## 25.1 Preserve v0.6 façade

Existing `CGE(...)` workflows continue where feasible.

## 25.2 Import shims

When moving model implementations, re-export old paths temporarily with deprecation warnings.

## 25.3 Deprecation policy

Do not remove a public path in the same release that deprecates it.

## 25.4 Additive public API

Make the simple path better without destroying advanced workflows.

---

# 26. Recommended implementation sequence

## Phase 0 — Freeze scientific baseline

Tasks:
1. confirm v0.6.0 baseline;
2. machine-readable validation fixtures;
3. wire Hosoe `listA1.csv`;
4. freeze CAMCGE targets;
5. freeze synthetic IFPRI behaviour;
6. wire/remove baseline JSON;
7. document solver-independence and multi-start.

**Exit:** later refactors cannot silently change validated outputs.

## Phase 1 — Audit cleanup

Tasks:
1. exception chaining;
2. namespace cleanup;
3. CAM exclusion comment;
4. retire prose tests;
5. preserve version tests;
6. temporary solver-default fix;
7. remove/wire unused artefacts.

**Exit:** outputs unchanged.

## Phase 2 — Central solver subsystem

Tasks:
1. inventory duplicates;
2. create resolver;
3. route core;
4. route IFPRI;
5. route CAMCGE;
6. remove duplicate example detector;
7. diagnostics;
8. consistent no-solver error;
9. explicit override tests.

**Exit:** no independent solver-selection policy remains outside the central module except thin wrappers.

## Phase 3 — Explicit model metadata

Tasks:
1. define internal metadata;
2. add Simple/Standard/CAM/IFPRI declarations;
3. replace `endswith("0")`;
4. add closure declarations;
5. add required-data declarations;
6. tests.

**Exit:** benchmark protection no longer depends on names.

## Phase 4 — Scenario clone redesign

Tasks:
1. isolation tests;
2. one-clone path;
3. route new façade;
4. compatibility wrappers;
5. structural profiling;
6. remove redundant copy after equivalence.

**Exit:** one scenario = one independent model clone.

## Phase 5 — First-class bundled packaging

Tasks:
1. canonical SimpleCGE location;
2. canonical StandardCGE location;
3. CAMCGE under installed package;
4. synthetic IFPRI under installed package;
5. wheel tests;
6. bundled solves.

**Exit:** wheel reaches every publicly advertised redistributable model.

## Phase 6 — Practitioner facades

Implement `SimpleCGE`, `StandardCGE`, `CamCGE`, `IFPRICGE`, `.solve()`, `.scenario()`, `.summary()`, and narrow semantic helpers.

**Exit:** first README example contains only economically meaningful modelling code after import.

## Phase 7 — `from_sam()`

Tasks:
1. schema;
2. balance validation;
3. role mapping;
4. internal conversion;
5. errors;
6. example;
7. tests.

**Exit:** one SAM plus economically necessary mapping information constructs StandardCGE.

## Phase 8 — Mechanical internal refactors

Tasks:
1. split StandardCGE model method;
2. refactor `_modify`;
3. move canonical implementations out of `examples`;
4. compatibility shims;
5. IFPRI refactor only where coverage permits.

**Exit:** maintainability improved with no benchmark change.

## Phase 9 — Functional custom-model authoring

Tasks:
1. minimal module contract;
2. module adapter;
3. no-class example;
4. closure;
5. benchmark metadata;
6. ordinary lifecycle;
7. docs.

**Exit:** custom Python model tutorial contains no inheritance.

## Phase 10 — Experimental `.cge.md`

### A. grammar prototype
Sets, declarations, variables/bounds, equations, sum/product, fix/drop, shockable.

### B. AST + semantic validation

### C. Pyomo compiler

### D. tiny reference equilibrium

### E. SimpleCGE equivalence
Compare Python implementation, `.cge.md` implementation, and independent reference.

### F. CLI
Add `cge check` and `cge solve` if stable.

**Exit:** at least one nontrivial small CGE can be parsed, validated, compiled, solved, and independently checked.

## Phase 11 — Documentation/notebook reset

Rewrite README, notebooks, installation docs, model-authoring docs, and archive migration-era material.

**Exit:** a new practitioner solves a model before encountering Git, PATH, or Pyomo internals.

## Phase 12 — Release hardening

Full matrix, wheel/sdist, examples, notebooks, namespace, deprecations, docs, changelog, version bump, release candidate, clean-environment smoke test.

---

# 27. Suggested PR decomposition

1. **PR 1 — Freeze external validation evidence**
2. **PR 2 — Audit cleanup and prose-test retirement**
3. **PR 3 — Central solver resolution**
4. **PR 4 — Model metadata and benchmark-only declarations**
5. **PR 5 — Scenario clone architecture**
6. **PR 6 — Canonical bundled model locations**
7. **PR 7 — CAMCGE first-class wheel packaging**
8. **PR 8 — Installed synthetic IFPRI economy**
9. **PR 9 — Practitioner facades**
10. **PR 10 — SAM loader**
11. **PR 11 — Mechanical StandardCGE decomposition and `_modify` refactor**
12. **PR 12 — Functional custom-model adapter**
13. **PR 13 — `.cge.md` parser/AST**
14. **PR 14 — `.cge.md` compiler/reference model**
15. **PR 15 — Notebook/docs redesign**
16. **PR 16 — Release candidate hardening**

Every PR should state:

- equations changed? yes/no;
- calibration changed? yes/no;
- public API changed? yes/no;
- packaging changed? yes/no;
- internal-only? yes/no;
- frozen validation tests run.

---

# 28. Acceptance tests as user stories

## Story 1 — First-time practitioner

```python
from cge_core import StandardCGE
base = StandardCGE.example().solve()
```

works without solver-name selection or closure specification.

## Story 2 — Tariff experiment

```python
reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)
result = reform.solve()
```

reproduces validated Hosoe results.

## Story 3 — Scenario independence

Scenario A does not alter benchmark or Scenario B.

## Story 4 — CAMCGE wheel install

```python
from cge_core import CamCGE
base = CamCGE.example().solve()
```

works after wheel installation.

## Story 5 — IFPRI installed example

```python
from cge_core import IFPRICGE
base = IFPRICGE.synthetic().solve()
```

works without licensed source and is clearly labelled synthetic.

## Story 6 — Own SAM

A practitioner supplies one SAM plus necessary account mappings without manually generating PyCGE data files.

## Story 7 — Model author without OOP

A researcher defines and runs a custom Python model using functions/declarations only.

## Story 8 — Human-readable model

```bash
cge check model.cge.md
```

returns deterministic syntax/semantic validation.

## Story 9 — Prose inertness

Changing only Markdown prose changes neither AST nor numerical result.

## Story 10 — Advanced user

Raw Pyomo access and explicit solver/closure override remain available.

---

# 29. Definition of done by subsystem

## Solver
- one resolver;
- bundled models use it;
- ordinary `.solve()` takes no solver name;
- explicit override works;
- missing backend message is actionable.

## Scenario
- one clone per scenario;
- isolation tests;
- rollback tests;
- stable snapshots.

## Bundled models
- all public imports work;
- packaged examples exist;
- model-owned closures;
- wheel reaches them.

## Custom Python authoring
- no-class example;
- explicit metadata;
- no naming heuristic;
- ordinary lifecycle.

## `.cge.md`
- deterministic fenced blocks;
- parser with source locations;
- AST;
- semantic validation;
- compiler;
- one working reference CGE;
- prose-inertness test;
- independent syntax.

---

# 30. Risks and mitigations

## Risk 1 — Scope explosion
**Mitigation:** `.cge.md` is experimental and may be non-blocking for the stable core if needed.

## Risk 2 — Scientific regression
**Mitigation:** freeze external benchmark evidence before structural work.

## Risk 3 — DSL becomes “new GAMS”
**Mitigation:** constrain grammar to actual CGE needs and reject compatibility-driven feature creep.

## Risk 4 — DSL hides economics
**Mitigation:** explicit equations; no AI-generated semantics; inspectable closure/calibration.

## Risk 5 — Over-generalized model contract
**Mitigation:** prove against SimpleCGE, StandardCGE, CAMCGE, and IFPRI before finalizing.

## Risk 6 — Synthetic IFPRI falsely presented as official validation
**Mitigation:** explicit labels in code, docs, and tests.

## Risk 7 — Solver promise exceeds reality
**Mitigation:** platform feasibility spike and truthful distinction between selection and installation.

## Risk 8 — Backward compatibility traps architecture
**Mitigation:** shims/deprecations with later removal.

## Risk 9 — Premature result ontology
**Mitigation:** only expose truly comparable common result categories.

---

# 31. v0.7.0 release checklist

## Scientific integrity

- [ ] StandardCGE benchmark unchanged.
- [ ] StandardCGE tariff experiment unchanged.
- [ ] Hosoe `listA1.csv` used in automated validation.
- [ ] CAMCGE base targets unchanged.
- [ ] CAMCGE experiments unchanged.
- [ ] CAMCGE dropped-equation residual remains within frozen tolerance.
- [ ] Solver-independence evidence documented.
- [ ] Multi-start evidence documented.
- [ ] No tolerance loosened merely to pass refactoring.
- [ ] IFPRI evidence boundary stated accurately.

## Packaging

- [ ] Wheel contains supported model packages.
- [ ] CAMCGE reachable from wheel.
- [ ] Synthetic IFPRI data reachable from wheel.
- [ ] Tests excluded.
- [ ] Licensed source excluded.
- [ ] Clean wheel smoke test passes.
- [ ] sdist smoke test passes.

## Public API

- [ ] `SimpleCGE` works.
- [ ] `StandardCGE` works.
- [ ] `CamCGE` works.
- [ ] `IFPRICGE` works.
- [ ] `.solve()` auto-resolves solver.
- [ ] `.scenario()` isolates state.
- [ ] `.summary()` exists.
- [ ] generic `.set()` remains.
- [ ] core semantic shock helper(s) work.
- [ ] old v0.6 façade remains functional or deprecates cleanly.

## Solver

- [ ] one authoritative resolver.
- [ ] explicit override.
- [ ] clear no-solver message.
- [ ] CAM no longer blindly defaults to cyipopt.
- [ ] IFPRI uses common resolver.
- [ ] notebook solver plumbing removed.

## Model contract

- [ ] benchmark-only metadata explicit.
- [ ] no `endswith("0")`.
- [ ] default closure explicit.
- [ ] required-data metadata explicit where needed.
- [ ] third-party naming test covers shockable `...0` if useful.

## Data

- [ ] `StandardCGE.from_sam()` works for supported schema.
- [ ] imbalance detected.
- [ ] ambiguous roles generate actionable errors.
- [ ] internal generated files hidden from normal workflow.

## Scenario architecture

- [ ] no whole-engine deepcopy per scenario.
- [ ] one scenario model clone.
- [ ] sibling isolation.
- [ ] benchmark immutability.
- [ ] undo rollback.

## Custom authoring

- [ ] functional Python authoring documented.
- [ ] no OOP required.
- [ ] custom closure works.
- [ ] benchmark-only declaration works.
- [ ] ordinary lifecycle works.

## `.cge.md` experimental MVP

- [ ] independent syntax documented.
- [ ] fenced `cge` blocks parsed.
- [ ] AST implemented.
- [ ] semantic validation implemented.
- [ ] line/column errors.
- [ ] small model solves.
- [ ] prose-inertness test.
- [ ] experimental stability warning.
- [ ] no intentional GAMS syntax compatibility.
- [ ] `cge check` if CLI retained.
- [ ] `cge solve` if CLI retained.

## Internal quality

- [ ] `_modify` simplified.
- [ ] exception chaining corrected.
- [ ] namespace cleaned.
- [ ] supported models no longer conceptually live under `examples`.
- [ ] StandardCGE method mechanically decomposed if included.
- [ ] migration/prose tests retired.

## Documentation

- [ ] README starts with practitioner workflow.
- [ ] install guide separates installation from modelling.
- [ ] first notebook has no Git setup.
- [ ] ordinary notebooks have no PATH/sys.path/subprocess solver plumbing.
- [ ] CAMCGE documented as first-class.
- [ ] IFPRI synthetic vs official status explicit.
- [ ] own-SAM tutorial.
- [ ] own-model tutorial.
- [ ] internals moved to advanced material.
- [ ] migration history de-emphasized.

---

# 32. Features that may be deferred

## Possible v0.7.x

- additional semantic shock helpers;
- richer result comparisons;
- CLI scenario execution;
- better SAM role inference;
- solver installation helpers;
- richer `.cge.md` diagnostics.

## Possible v0.8

- StandardCGE fully expressible in `.cge.md`;
- richer CES/CET syntax;
- scenario declarations inside Markdown;
- model templates;
- grammar/schema versioning;
- syntax highlighting;
- generated equation documentation;
- LaTeX equation rendering;
- model linting;
- reusable model fragments.

## Later

- CAMCGE `.cge.md` equivalence;
- IFPRI `.cge.md` representation if grammar proves adequate;
- dynamic CGE;
- model coupling;
- richer closure libraries;
- domain-specific result dashboards.

---

# 33. Questions to resolve during implementation spikes

1. **`.cge.md` stability:** recommendation: experimental in v0.7.0.
2. **Parser dependency:** compare hand parser and lightweight grammar library.
3. **Generic author API:** choose `CGE(model=module, ...)`, `CGE.from_module(...)`, or equivalent; no OOP required.
4. **Closure override API:** do not finalize until tested against StandardCGE, CAMCGE, IFPRI.
5. **SAM role declaration:** prefer explicitness to fragile inference.
6. **Solver distribution:** determine truthful cross-platform promise.
7. **Class spelling:** recommendation `CamCGE` in Python, “CAMCGE” in prose.

---

# 34. Architectural invariants after v0.7.0

1. **No infrastructure boilerplate in ordinary model use.**
2. **No economic meaning inferred from symbol spelling.**
3. **No OOP requirement for model authors.**
4. **No prose-driven model execution.**
5. **No advertised bundled model absent from installed distribution.**
6. **No scientific tolerance changes hidden inside refactors.**
7. **No universal closure assumption.**
8. **No forced equation abstraction merely to shorten files.**
9. **No loss of raw/advanced access in the name of simplicity.**
10. **No model rewrite without numerical equivalence evidence.**
11. **No synthetic-data test presented as official-source replication.**
12. **No duplicated solver-selection policy across model families.**

---

# 35. What success should feel like

## Practitioner

```python
economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()

policy = base.scenario("Policy")
policy.tariff("AGR", change=-0.50)

result = policy.solve()
result.summary()
```

The practitioner thinks about policy, not the software stack.

## Teacher

A student encounters the CGE before encountering Pyomo or solver plumbing.

## Model author

She opens:

```text
my_model.cge.md
```

and thinks:

```text
sets
data
parameters
variables
equations
closure
```

not:

```text
classes
inheritance
engine states
```

## Reviewer

The model, closure, validation evidence, solver metadata, and licensing boundary are inspectable.

## Developer

The architecture has explicit layers:

```text
economic specification
        ↓
model metadata / AST
        ↓
engine
        ↓
solver resolver
        ↓
result
```

---

# 36. One-sentence v0.7.0 release thesis

> **CGE-Core v0.7.0 turns a validated Python CGE package into a practitioner-first modelling system: bundled models become directly usable after installation, model-specific closures and metadata become explicit, solver and scenario plumbing move below the user interface, CAMCGE and IFPRI receive proper public packaging, custom models no longer require OOP, and an experimental human-readable `.cge.md` specification begins the path toward writing CGE models as readable economic documents rather than software frameworks.**

---

# 37. Recommended opening instruction for the separate implementation thread

> Implement CGE-Core v0.7.0 according to the attached plan. Treat v0.6.0 commit `7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2` and its independent audit as the scientific baseline. Work incrementally and preserve all validated Hosoe and CAMCGE numerical results. Do not rewrite economic equations unless a task explicitly requires it. Prioritize practitioner UX, first-class CAMCGE packaging, installed synthetic IFPRI usability, centralized solver handling, one-clone scenario state, explicit model-owned closure/metadata, non-OOP custom model authoring, and the experimental deterministic `.cge.md` format. Keep the existing v0.6 public API compatible where feasible. For every change, state whether it affects equations, calibration, public API, packaging, or only internals, and run the relevant frozen validation tests before proceeding.

---

# Appendix A — Audit findings directly motivating v0.7.0

1. Hosoe simple and standard CGE models reproduce their benchmark results.
2. CAMCGE reproduces its benchmark and experiments strongly.
3. CAMCGE is not reachable from the installed wheel because it lives outside `cge_core*`.
4. The official IFPRI benchmark is not externally verifiable without licensed source material.
5. A redistributable synthetic IFPRI-format economy exists under `tests/` and is absent from the installed package.
6. StandardCGE and CAMCGE solutions were independently recovered using root-finders unrelated to IPOPT.
7. StandardCGE successful random multi-start solves all converged to the same equilibrium.
8. `validation/gams/stdcge/listA1.csv` is shipped but not wired into tests.
9. `validation/v0.6-baseline.json` is unused.
10. `_modify` infers benchmark data using `endswith("0")`.
11. `StdModelDef.model()` is long but linear and should be mechanically split, not conceptually rewritten.
12. `_modify` has high complexity and duplicated responsibilities.
13. migration-era tests assert documentation prose and should be retired.
14. CAM replication defaults incorrectly to `cyipopt`.
15. four exception paths should preserve original causes.
16. supported StandardCGE code resides under an `examples` directory.
17. IFPRI solve/closure-switching was not independently audited.
18. the audit verified numerical replication, not an independent re-derivation of the economic specification.

---

# Appendix B — Decision log

## B.1 Practitioner notebooks
Reject Git/ref/PATH/solver plumbing in ordinary notebooks.

## B.2 CAMCGE
CAMCGE remains a real supported model family.

## B.3 Generic `CGE`
Do not remove it. Reposition it as the flexible general/lower-level entry point while adding easy bundled-model facades.

## B.4 Custom models
Custom model creation is first-class.

## B.5 OOP
Do not require OOP.

## B.6 Human-readable authoring
Develop a deterministic Markdown-based specification with formal executable blocks.

## B.7 Markdown semantics
Prose is inert documentation. Only formal fenced blocks execute.

## B.8 GAMS/IP posture
Do not make a GAMS clone. Use independently designed syntax based on general mathematical modelling concepts. Do not copy code, documentation, examples, branding, or distinctive syntax merely for compatibility.

## B.9 Validated Python models
Do not immediately rewrite StandardCGE, CAMCGE, or IFPRI in the new language.

## B.10 Long-term aspiration
If `.cge.md` implementations eventually reproduce validated Python implementations and published references, they may become canonical specifications in a later release.

---

# Appendix C — Product hierarchy

```text
                        CGE-Core
                           │
             ┌─────────────┼─────────────┐
             │             │             │
        Practitioner    Model author    Developer
             │             │             │
      bundled facades    .cge.md      Python/Pyomo
             │          or functions      │
             └─────────────┼─────────────┘
                           │
                    internal ModelSpec
                           │
                         engine
                           │
                    solver resolver
                           │
                         result
```

The central principle is that every layer sees only the complexity it actually needs.
