> **GOVERNING DECISION RECORD:** This reconciliation governs v0.6 where it conflicts with earlier planning documents. Part 4 of the external review subsequently ratified the overall reconciliation and empirically validated whole-engine scenario cloning. `PHASE_2_ENTRY_DECISIONS.md` records the final implementation refinements.

# CGE-Core v0.6
## Course-Correction Reconciliation Memo — Disagreements Before Phase 2

**Project:** CGE-Core
**Target release:** v0.6
**Purpose:** Record the substantive disagreements between the current v0.6 plan and the external course-correction notes before Phase 2 implementation.

---

# 1. Purpose of this memo

Several independent reviews were produced before Phase 2.

They were useful because they challenged the v0.6 plan from different angles:

- repository correctness;
- closure semantics;
- migration safety;
- practitioner intuition;
- GAMS/GEMPACK conventions;
- public API naming;
- future extensibility.

The reviews do **not** all agree with one another, and some recommendations conflict with the current plan.

This memo records only the important disagreements.

The goal is to prevent later contributors from reading one review in isolation and assuming that every recommendation was accepted.

The governing principle is:

> **Adopt corrections that expose a real defect in the current specification, but do not expand v0.6 into a broader redesign merely because a future requirement can already be imagined.**

---

# 2. Governing v0.6 position after reconciliation

The v0.6 public architecture remains:

```text
CGE
 │
 └── solve_benchmark()
          ↓
      Equilibrium
          │
      scenario()
          ↓
       Scenario
          │
        solve()
          ↓
        Result
```

with:

```text
CGE
= configured model blueprint

Equilibrium
= solved, protected benchmark equilibrium

Scenario
= independent mutable counterfactual state

Result
= immutable solved numerical snapshot
```

The new façade initially covers the **Hosoe engine-backed models** only.

The following remain separate in v0.6:

```text
cge_core.ifpri
cam/
```

No attempt is made in v0.6 to create one universal internal architecture for Hosoe, IFPRI, and CAMCGE.

---

# 3. Disagreement 1 — Should v0.6 introduce a public `Closure` object?

## External recommendation

The first course-correction review argued that CAMCGE demonstrates a defect in the proposed:

```python
solve_baseline(
    numeraire=(...),
    redundant=(...),
)
```

interface.

CAMCGE fixes `mps`, which is not a price numeraire, while the price level is anchored elsewhere.

The initial reaction was therefore to introduce a minimal:

```python
Closure(...)
```

object before Phase 2.

## Revised position

**Do not introduce a public `Closure` object in v0.6.**

The later review, written after reading the full planning documents, correctly identifies the scope distinction:

```text
v0.6 façade scope = Hosoe engine-backed models
```

For those models:

```text
numeraire=
redundant=
```

are semantically correct.

CAMCGE and IFPRI are **not** being migrated through this façade in v0.6.

Therefore CAMCGE exposes a future abstraction requirement, but it does not force a v0.6 abstraction.

## Why the earlier `Closure` recommendation is rejected

Adding `Closure` now would require choosing a representation before the second backend exists.

A real general closure abstraction may eventually need to express:

- price numeraires;
- fixed closure variables;
- dropped equations;
- endogenous/exogenous swaps;
- IFPRI macro closures;
- fixed exchange-rate regimes;
- government-saving closures;
- Walras-objective formulations.

A small `Closure` object designed only from Hosoe + CAM risks becoming a premature abstraction that later has to be redesigned for IFPRI.

## Governing decision

For v0.6:

```python
benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

remains valid **only as the Hosoe-backend closure spelling**.

It is not part of the universal downstream extension contract.

Instead, create a requirements ledger such as:

```text
docs/rfcs/closure-requirements.md
```

recording:

1. Hosoe closure;
2. CAMCGE closure;
3. IFPRI BASE closure;
4. IFPRI scenario closures;
5. future GAMS/GEMPACK-style closure swaps.

The abstraction is extracted only when a second backend adapter creates a real common requirement.

---

# 4. Disagreement 2 — `solve_baseline()` versus `solve_benchmark()`

## Current Phase 1 decision

The original Phase 1 specification selected:

```python
solve_baseline()
```

because it avoided the misleading legacy verb:

```text
calibrate()
```

## External recommendation

The revised course-correction notes recommend:

```python
solve_benchmark()
```

on field-terminology grounds.

## Decision

**Adopt the rename to `solve_benchmark()`.**

The SAM-replicating equilibrium is naturally called the:

```text
benchmark equilibrium
```

while:

```text
baseline
```

already has a distinct meaning in dynamic and forecast CGE work:

```text
reference path
```

That distinction matters even within CGE, not only for hypothetical future DCGE work.

## Governing terminology

Static CGE:

```text
benchmark equilibrium
counterfactual / scenario equilibrium
```

Dynamic / forecast setting:

```text
baseline path
reform / policy path
```

Canonical v0.6 code therefore becomes:

```python
benchmark = model.solve_benchmark(...)
scenario = benchmark.scenario("tariff abolition")
result = scenario.solve()

comparison = result.compare(benchmark)
```

The legacy engine may continue using its internal word:

```text
BASE
```

No internal rename is required.

---

# 5. Disagreement 3 — What should `Scenario.unfix()` mean?

## Original Phase 1 specification

The specification used an example like:

```python
scenario.unfix("Sf", None)
```

to describe making a previously exogenous quantity endogenous.

## External correction

The review correctly identified that this is impossible in the current standard Hosoe backend.

`Sf` is a mutable:

```text
Param
```

not a:

```text
Var
```

A parameter has no Pyomo fixed/unfixed state.

Making `Sf` endogenous would require changing the model definition.

That is explicitly outside v0.6 scope.

## Decision

**Correct the `unfix()` contract.**

For v0.6:

```python
scenario.unfix(...)
```

means only:

> release a `Var` that this same scenario previously fixed through `set()`.

Example:

```python
scenario.set("epsilon", None, 1.10)
scenario.unfix("epsilon")
```

It does **not** mean:

```text
convert arbitrary exogenous Params into endogenous Vars
```

## Required error behavior

If the user tries:

```python
scenario.unfix("Sf")
```

the API should teach the limitation clearly:

```text
'Sf' is exogenous as a parameter in this model implementation.
set() can change its value, but making it endogenous requires
a model-definition change and is not a scenario operation.
```

This is a useful course correction because it prevents the façade from promising a capability the backend does not have.

---

# 6. Disagreement 4 — Should `PyCGE` immediately become a compatibility façade over the new core?

## External recommendation

One early review recommended:

```text
PyCGE
→ compatibility façade
→ new core
```

during Phase 2.

## Decision

**Reject this for early Phase 2.**

The migration needs an independent old path.

During reengineering, we want:

```text
legacy direct PyCGE path
versus
new CGE façade path
```

so that the two can be differentially compared.

If both immediately delegate to the same new implementation, the old path stops being an independent oracle.

## Governing structure during migration

Early v0.6:

```text
new CGE façade
      │
      ▼
private adapter
      │
      ▼
existing PyCGE machinery
```

while direct legacy usage remains:

```python
PyCGE(...)
```

and continues to run unchanged.

Only after parity is established should the project reconsider whether `PyCGE` eventually delegates downward or becomes private.

---

# 7. Disagreement 5 — How should scenario isolation be implemented?

## External preferred mechanism

One review recommends modifying the existing private `_modify()` helper so it accepts:

```text
instance
history
numeraire key
```

explicitly.

This would allow multiple Scenario objects to share the same validation logic without sharing the single legacy `sim` slot.

## Current position

The diagnosis is correct:

```text
Scenario objects must not share PyCGE.sim.
```

The rejection of duplicated validation logic is also correct.

However, **do not commit to refactoring `_modify()` before trying a less invasive mechanism.**

## Preferred implementation order

Try first:

```text
Equilibrium owns calibrated PyCGE backend
        │
        ├── deepcopy full backend → Scenario A backend
        ├── deepcopy full backend → Scenario B backend
        └── deepcopy full backend → Scenario C backend
```

Each Scenario can then use existing:

```text
model_sim()
model_modify_sim()
model_solve()
```

on its own private engine copy.

This preserves the legacy engine code unchanged.

## Fallback

If full-engine cloning proves:

- unreliable;
- too memory-intensive;
- incompatible with solver state;
- or otherwise impractical;

then parameterizing `_modify()` becomes the preferred fallback.

## Governing principle

Prefer:

```text
minimal engine disturbance
```

before:

```text
internal refactor for elegance
```

during the parity phase.

---

# 8. Disagreement 6 — Should `CGE` own mutable solved state?

## Underspecified original design

The original specification called `CGE` a blueprint but did not explicitly define repeated calls such as:

```python
b1 = model.solve_benchmark(...)
b2 = model.solve_benchmark(...)
```

## External recommendation

Each call should build a fresh backend owned by the returned `Equilibrium`.

## Decision

**Adopt this strongly.**

`CGE` should hold only:

```text
model definition
data source
configuration
```

It should not retain a single mutable solved backend that later calls overwrite.

## Governing ownership model

```text
CGE
 │
 ├── solve_benchmark() → Equilibrium A + private backend A
 │
 └── solve_benchmark() → Equilibrium B + private backend B
```

Thus:

- repeated benchmark solves are safe;
- different numeraires can coexist;
- different solver choices can coexist;
- an earlier equilibrium is never invalidated by a later benchmark solve.

---

# 9. Disagreement 7 — Should Phase 2 accept an importable shell?

## Weak interpretation

A minimal Phase 2 could theoretically pass if:

```python
from cge_core import CGE
```

works while the object methods remain mostly placeholders.

## External correction

This is too weak to be meaningful.

## Decision

**Adopt the stronger exit criterion.**

Phase 2 is not complete until the full canonical lifecycle works:

```text
solve benchmark
→ create multiple independent scenarios
→ set shocks
→ solve
→ read values
→ compare
→ modify one scenario
→ solve again
→ prove old Result unchanged
```

The exact numbering between "Phase 2" and "Phase 3" matters less than ensuring the implementation gate is behaviorally meaningful.

---

# 10. Disagreement 8 — Should benchmark values be duplicated into a new reference artifact?

## External recommendation

Commit a machine-readable benchmark-reference artifact containing frozen:

```text
levels
tolerances
family references
```

## Decision

**Adopt only partially.**

The motivation is good:

```text
make the freeze explicit and machine-readable
```

But duplicating all benchmark values creates another source of truth.

Existing values already live in:

- Hosoe tests;
- IFPRI validation tests;
- CAM published reference tables;
- existing tolerance assertions.

## Preferred solution

Commit a small validation manifest containing:

```text
frozen baseline commit
benchmark families
policy that refactor tolerances may not be loosened
references to canonical tests/reference modules
```

Do **not** duplicate every CAM published value or every Hosoe expected level.

---

# 11. Disagreement 9 — Should `Result.to_frame()` be added because it is easy?

## External recommendation

Add:

```python
result.to_frame()
```

because the internal snapshot is already tabular.

## Decision

**Defer it.**

Being easy to implement is not enough reason to freeze a public method.

`to_frame()` immediately creates unresolved API questions:

```text
variables only?
parameters too?
fixed status?
objective?
component type?
long versus wide?
index schema?
```

For v0.6:

```python
result.value(...)
result.compare(...)
```

are sufficient.

A private internal tabular representation may exist without becoming a stable API.

---

# 12. Disagreement 10 — Should the new API include persistence?

## Legacy behavior

`PyCGE` can persist live Pyomo state through dill.

## External recommendation

Do not port this into the new public object model.

## Decision

**Adopt.**

The new v0.6 API provides no public live-model persistence contract.

`Result` is plain numerical data.

Legacy dill functionality remains available through `PyCGE`.

A reproducibility manifest may be designed later.

---

# 13. Disagreement 11 — Should a GAMS crosswalk constrain the API?

## External recommendation

Create:

```text
docs/GAMS_CROSSWALK.md
```

and require every public operation to map to a GAMS idiom or explain why not.

## Decision

**Adopt as a design and pedagogy aid, not as an architectural constraint.**

The crosswalk is useful because CGE practitioners often already think in terms of:

```text
fix closure
solve benchmark
apply shock
solve counterfactual
store .l values
compare
```

The new object model maps well onto that mental model.

However:

> Python is allowed to improve the workflow.

Independent simultaneously live `Scenario` objects are valuable precisely because Python can provide stronger state ownership than manual serial GAMS scripts.

The design rule should therefore be:

```text
GAMS counterpart OR explicit explanation
```

not:

```text
Python API must imitate GAMS
```

---

# 14. Disagreement 12 — Should every teaching notebook show GAMS side-by-side?

## External recommendation

Notebooks 01–03 should contain side-by-side GAMS equivalents for the central experiments.

## Decision

**Useful but not mandatory in the main flow.**

For readers coming from GAMS, the crosswalk is excellent.

For beginners, mandatory side-by-side GAMS may add cognitive load.

Preferred presentation:

```text
"Coming from GAMS?" sidebar
```

or:

```text
collapsible reference panel
```

rather than making GAMS syntax part of the essential learning sequence.

Notebook 03 should definitely demonstrate multiple simultaneously live Scenario objects.

That is the clearest user-visible payoff of the new architecture.

---

# 15. Disagreement 13 — How strongly should GTAP/Burfisher licensing drive positioning?

## External framing

One review argues that Burfisher belongs only in reading material because GTAP data cannot be redistributed.

## Decision

**Keep the positioning, soften the licensing claim.**

Useful positioning:

```text
Hosoe
= pedagogical anchor

IFPRI
= practical / institutional anchor

Burfisher
= companion applied reading
```

But GTAP/Burfisher is not excluded merely because of licensing.

The stronger reason is that it represents a distinct:

- model architecture;
- solution paradigm;
- software ecosystem;
- data ecosystem;
- project scope.

GTAP licensing reinforces that separation but should not be stated as the sole reason.

---

# 16. Disagreement 14 — Should IFPRI be the next release headline?

## External suggestion

Because IFPRI is the practical anchor, a future IFPRI adapter is described as a natural v0.7 headline.

## Decision

**Do not commit to that roadmap yet.**

It is plausible.

It is not required for v0.6.

The closure-requirements ledger should prepare for future adaptation without creating a release promise.

---

# 17. Disagreement 15 — Should closure swapping be solved now?

## Practitioner expectation

GEMPACK and GAMS users are accustomed to changing closure by exchanging endogenous and exogenous quantities.

The current Pyomo model definitions encode some exogenous quantities structurally as:

```text
Param
```

which cannot simply be "unfixed."

## Decision

**Document the limitation; do not redesign Hosoe equations in v0.6.**

The inability to do a fully general closure swap is real.

But solving it requires changes deeper than the façade:

```text
model-definition structure
Var/Param representation
closure semantics
```

That is beyond v0.6 parity work.

Record it in:

```text
closure-requirements.md
```

and expose clear errors now.

---

# 18. Final accepted/rejected summary

| Issue | Final decision |
|---|---|
| Add public `Closure` in v0.6 | **Reject** |
| Rename `solve_baseline()` | **Accept → `solve_benchmark()`** |
| `unfix("Sf")` style behavior | **Reject** |
| `unfix()` releases scenario-fixed Vars only | **Accept** |
| Immediately make `PyCGE` delegate to new core | **Reject** |
| Keep direct legacy path for differential testing | **Accept** |
| Refactor `_modify()` immediately | **Defer; try full-engine scenario cloning first** |
| `CGE` as stateless blueprint | **Accept** |
| Each benchmark solve owns fresh backend | **Accept** |
| Weak Phase 2 shell acceptance | **Reject** |
| Full lifecycle required for Phase 2 exit | **Accept** |
| Duplicate all benchmark levels into new file | **Reject** |
| Small validation manifest | **Accept** |
| Add `Result.to_frame()` in v0.6 | **Defer** |
| Add persistence to new API | **Reject** |
| Keep legacy dill in `PyCGE` | **Accept** |
| GAMS crosswalk | **Accept as aid, not constraint** |
| GAMS panels mandatory in every notebook | **Reject as mandatory** |
| Closure requirements ledger | **Strongly accept** |
| General closure swap in v0.6 | **Reject** |
| IFPRI migration in v0.6 | **Reject** |
| CAMCGE migration into package | **Reject** |
| IFPRI adapter promised for v0.7 | **Do not commit yet** |

---

# 19. Final governing API after course correction

Canonical v0.6 use:

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

scenario = benchmark.scenario("tariff abolition")

scenario.set("taum", "BRD", 0)
scenario.set("taum", "MLK", 0)

result = scenario.solve()

print(result.value("Z", "BRD"))
print(result.compare(benchmark))
```

Repeated solve contract:

```python
scenario.set("taum", "BRD", 0.05)
result_2 = scenario.solve()

# Earlier result remains unchanged.
assert result.value("Z", "BRD") != result_2.value("Z", "BRD")
```

The long-term stable lifecycle is:

```text
solve_benchmark
→ scenario
→ set / limited unfix
→ solve
→ value / compare
→ modify
→ solve again
```

The following are deliberately **not** universal contracts:

```text
numeraire=
redundant=
Hosoe-specific closure spelling
Pyomo model structure
Param-versus-Var representation
legacy BASE/SIM slots
```

---

# 20. Final conclusion

The external course-correction notes improved the plan, but the right response is selective.

The key accepted corrections are:

- use **benchmark**, not baseline, for the SAM-replicating equilibrium;
- make `CGE` a true stateless blueprint;
- correct the `unfix()` contract;
- strengthen Phase 2 exit criteria;
- preserve independent legacy-vs-new differential testing;
- record closure requirements instead of prematurely building the abstraction;
- keep persistence out of the new API.

The key rejected expansions are:

- no public `Closure` abstraction yet;
- no IFPRI migration in v0.6;
- no CAMCGE package migration;
- no general closure-swap machinery;
- no premature `to_frame()` or persistence surface;
- no requirement that Python merely imitate GAMS.

The design principle after reconciliation is therefore:

> **Be general in vocabulary, narrow in implementation, strict in parity, and postpone abstractions until a second real backend forces them to exist.**
