# CGE-Core v0.6 Staggered Multi-Phase Execution Plan

**Status:** Proposed
**Target release:** `0.6.0`
**Strategy:** staged, low-risk reengineering before DCGE-Core

---

# 1. Decision

Yes — a **staggered multi-phase approach is better**.

For CGE-Core, this is not just safer; it is the **best** option.

Why:

- CGE-Core already has working models, tests, notebooks, examples, docs, and a Control Room.
- The intended changes are architectural and user-facing, not just internal refactors.
- A one-shot rewrite would create unnecessary breakage risk.
- We want to preserve benchmark-valid economics while improving identity and API design.
- We want to create a stable base for DCGE-Core **without** accidentally destabilizing CGE-Core.

So the correct strategy is:

\[
\text{freeze working behavior}
\rightarrow
\text{introduce new API in parallel}
\rightarrow
\text{migrate surfaces gradually}
\rightarrow
\text{retire inherited vocabulary last}
\]

This is much better than a big-bang rewrite.

---

# 2. Main principles

This execution plan follows six principles.

## 2.1 Preserve working economics

The refactor must not silently change the economic behavior of:

- Hosoe simple CGE
- Hosoe standard CGE
- IFPRI subsystem
- CAMCGE replication
- existing benchmark outputs

Architecture may change. Validated economics should not.

---

## 2.2 Separate “interface change” from “engine rewrite”

We should not rewrite the numerical core merely because the public API changes.

First:

- build a **new public interface**

Then:

- migrate users and docs to it

Only later:

- simplify or refactor internals

---

## 2.3 Keep CGE-Core runnable at all times

At each phase, the repo should remain in a usable state.

That means:

- tests still run
- examples still run
- notebooks still run
- docs still build
- Control Room is not abandoned

---

## 2.4 Migrate from outside inward

Change public-facing surfaces first in a controlled way:

1. public API
2. docs/examples
3. notebooks
4. generated code templates
5. internal cleanup

This is better than starting with large internal changes.

---

## 2.5 Minimize irreversible steps early

Early phases should be easy to undo.

So initially we should prefer:

- additive interfaces
- aliases
- wrappers
- compatibility shims
- extra tests

over destructive renames or deletions.

---

## 2.6 Make the future DCGE dependency explicit but indirect

CGE-Core should not contain dynamic logic.

Instead, the refactor should ensure that a future DCGE-Core can rely on a narrow stable contract:

- create calibrated equilibrium
- create scenario
- set admissible exogenous values
- solve
- read values
- repeat

That is all.

---

# 3. High-level release structure

The work should be executed in the following phases:

1. **Phase 0 — Safeguard and freeze**
2. **Phase 1 — Define the new public API**
3. **Phase 2 — Introduce the new API without breaking the old**
4. **Phase 3 — Add result/value/scenario abstraction**
5. **Phase 4 — Migrate examples, docs, notebooks, and Control Room**
6. **Phase 5 — Formalize extension contract and downstream stability**
7. **Phase 6 — Internal cleanup and retirement of inherited vocabulary**
8. **Phase 7 — Release hardening and v0.6.0 cut**

---

# 4. Branching strategy

Use a dedicated reengineering branch.

```text
main
└── reengineer-v0.6
```

Recommended supporting branches when needed:

```text
reengineer-v0.6
├── api-cge
├── scenario-result-layer
├── docs-migration
├── notebooks-migration
├── control-room-migration
└── cleanup-deprecations
```

## Why this is best

- `main` stays stable
- work can be checkpointed
- each phase can be reviewed on its own
- rollback is easier
- documentation and tooling migration can proceed separately from core changes

---

# 5. Phase 0 — Safeguard and freeze

## Objective

Create a safe baseline before changing architecture.

## Tasks

- [ ] Confirm current full test suite is green.
- [ ] Record current benchmark outputs for:
  - [ ] Hosoe simple
  - [ ] Hosoe standard
  - [ ] IFPRI
  - [ ] CAMCGE
- [ ] Confirm docs build successfully.
- [ ] Confirm notebooks execute or at least import successfully.
- [ ] Confirm Control Room currently points to valid API behavior.
- [ ] Create a regression snapshot document or test reference notes.
- [ ] Commit the architectural plan documents into the repo.

## Deliverables

- stable baseline branch
- benchmark reference values
- green CI before reengineering begins

## Acceptance criteria

- [ ] Current repo works before any redesign is merged.
- [ ] No ambiguity exists about what “unchanged economics” means.

---

# 6. Phase 1 — Define the new public API

## Objective

Design the CGE-Core-native public interface before implementing it.

## Core decision

The public vocabulary should become:

- `CGE`
- `Equilibrium`
- `Scenario`
- `Result`

The inherited `PyCGE` name should stop being the canonical face of the package.

## Tasks

- [ ] Finalize public names.
- [ ] Finalize the minimal workflow shape.
- [ ] Decide where public classes live.
- [ ] Decide what remains public and what becomes private.
- [ ] Decide how model definitions will be imported publicly.
- [ ] Decide compatibility strategy for `PyCGE`.

## Proposed target workflow

```python
from cge_core import CGE
from cge_core.models import StdCGE
from cge_core import example_data

model = CGE(StdCGE(), data=example_data("stdcge"))
baseline = model.calibrate(numeraire=("pf", "LAB"), redundant=("eqpf", "LAB"))

scenario = baseline.scenario("tariff abolition")
scenario.set("taum", "BRD", 0)
scenario.set("taum", "MLK", 0)

result = scenario.solve()
frame = result.compare(baseline)
```

## Key design rule

Do **not** overdesign.

We do not need:

- plugin frameworks
- factories everywhere
- large abstraction pyramids
- a full-blown dependency injection system

Keep it small and scientific.

## Deliverables

- public API specification
- import map
- class responsibilities
- deprecation decision

## Acceptance criteria

- [ ] We can describe CGE-Core without mentioning `PyCGE` as the main interface.
- [ ] The API is small enough to document clearly.

---

# 7. Phase 2 — Introduce the new API without breaking the old

## Objective

Add the new public interface while preserving current functionality.

This is the critical safety phase.

## Tasks

- [ ] Introduce canonical `CGE` public class.
- [ ] Internally map `CGE` onto the current tested engine behavior.
- [ ] Add public `Equilibrium`, `Scenario`, and `Result` layers.
- [ ] Keep old workflow operational underneath.
- [ ] If needed, retain `PyCGE` temporarily as compatibility alias or wrapper.
- [ ] Export the new public objects from `cge_core.__init__`.
- [ ] Add initial tests for canonical imports.

## Important implementation principle

At this stage, we are **wrapping/adapting**, not rewriting the engine.

That means:

- we use the existing tested machinery where possible
- we expose a better interface on top
- we postpone deeper internal surgery

## Deliverables

- usable `CGE` import
- initial façade layer
- no immediate breakage of old behavior

## Acceptance criteria

- [ ] `from cge_core import CGE` works.
- [ ] Existing core benchmark logic still works.
- [ ] CI remains green.

---

# 8. Phase 3 — Add stable scenario/result/value abstraction

## Objective

Make the equilibrium lifecycle explicit and downstream-safe.

## Tasks

- [ ] Implement `baseline = model.calibrate(...)`.
- [ ] Implement `baseline.scenario(name=...)`.
- [ ] Implement `scenario.set(...)`.
- [ ] Implement `result = scenario.solve()`.
- [ ] Implement `value(...)` accessors.
- [ ] Implement `compare(...)`.
- [ ] Implement `to_frame()` or equivalent export methods.
- [ ] Add clear exceptions for invalid component/index access.
- [ ] Ensure scenario modifications do not mutate the baseline.

## Why this phase matters

This is the real foundation for DCGE-Core later.

A future dynamic package should not need to touch:

- `base`
- `sim`
- raw Pyomo variable access
- engine internals
- private helper functions

It should only need:

\[
\text{equilibrium}
\rightarrow
\text{scenario}
\rightarrow
\text{set}
\rightarrow
\text{solve}
\rightarrow
\text{value}
\]

## Deliverables

- stable scenario lifecycle
- stable read API
- baseline isolation

## Acceptance criteria

- [ ] Users can retrieve values without direct Pyomo calls.
- [ ] A scenario can be solved, modified again, and solved again.
- [ ] Baseline and scenario are isolated.

---

# 9. Phase 4 — Migrate outward-facing surfaces

## Objective

Move all user-facing materials to the new API.

This phase should itself be staggered.

---

## Phase 4A — README and examples

### Tasks

- [ ] Rewrite quick-start examples using `CGE`.
- [ ] Rewrite code snippets using `Equilibrium`, `Scenario`, `Result`.
- [ ] Replace `PyCGE` references in canonical docs.
- [ ] Update example scripts.

### Acceptance criteria

- [ ] A first-time user sees only the new interface.

---

## Phase 4B — Notebooks

### Tasks

- [ ] Update notebook imports.
- [ ] Update notebook narrative text.
- [ ] Update code cells to the new workflow.
- [ ] Re-run notebooks to check execution.

### Special caution

Notebook migration should be done carefully because they are teaching materials. We should not change both pedagogy and API style at once unless necessary.

### Acceptance criteria

- [ ] Notebooks run with the new API.
- [ ] Learning flow remains clear.

---

## Phase 4C — Documentation site

### Tasks

- [ ] Update architecture diagrams.
- [ ] Update API reference.
- [ ] Add a migration guide from `PyCGE` to `CGE`.
- [ ] Clarify provenance without centering inherited naming.
- [ ] Update Control Room related docs if they show code.

### Acceptance criteria

- [ ] The docs narrate CGE-Core as its own framework.

---

## Phase 4D — Control Room

### Tasks

- [ ] Identify where the Control Room displays or generates code.
- [ ] Replace generated code snippets using the old API.
- [ ] Ensure copied code uses `CGE`.
- [ ] Verify that any internal documentation or labels are aligned with the new vocabulary.

### Important note

The Control Room might not break immediately just because CGE-Core changed. The main risk is if it generates example code or explanations using the old API. So this is partly a content migration, not only a software migration.

### Acceptance criteria

- [ ] Control Room-generated code matches the new API.
- [ ] No visible user-facing code still presents `PyCGE` as canonical.

---

# 10. Phase 5 — Formalize extension contract

## Objective

Stabilize the exact subset of CGE-Core that future downstream packages may rely upon.

## Tasks

- [ ] Document supported public extension points.
- [ ] Add an “Extension API” section to the docs.
- [ ] Add tests covering the extension lifecycle:
  - [ ] calibrate
  - [ ] scenario
  - [ ] set
  - [ ] solve
  - [ ] value
  - [ ] set again
  - [ ] solve again
- [ ] Define public vs private namespaces clearly.
- [ ] Ensure advanced raw-model access is clearly labeled as non-contractual.

## Why this matters

This protects against the exact future problem you identified:

> someone cleans up CGE-Core, sees no reason for a capability, removes it, and leaves DCGE-Core hanging.

The solution is not to add random comments.

The solution is:

- document the capability
- test the capability
- make it part of the public contract

## Deliverables

- extension contract documentation
- contract tests
- clear public/private boundary

## Acceptance criteria

- [ ] A downstream package can safely depend on the intended equilibrium/scenario contract.
- [ ] The needed behavior is protected by tests.

---

# 11. Phase 6 — Internal cleanup and retirement of inherited vocabulary

## Objective

Once the new public interface is working and all outward surfaces are migrated, simplify internals as appropriate.

## Tasks

- [ ] Remove or de-emphasize `PyCGE` in code comments, docs, and examples.
- [ ] If compatibility alias remains, mark it clearly deprecated.
- [ ] Rename implementation objects where worthwhile.
- [ ] Reorganize package structure if needed.
- [ ] Move model definitions into a cleaner public namespace.
- [ ] Reduce leakage of old workflow-state language if possible.
- [ ] Keep provenance language precise and visible.

## Important rule

Only do cleanup **after** the new interface is stable and migrated.

This is a late-phase task, not an early-phase task.

## Deliverables

- cleaner internals
- reduced inherited naming
- clearer package identity

## Acceptance criteria

- [ ] CGE-Core no longer publicly “looks like PyCGE with extras.”
- [ ] Historical provenance is preserved without dominating the interface.

---

# 12. Phase 7 — Release hardening and v0.6.0 cut

## Objective

Prepare the release cleanly.

## Tasks

- [ ] Full test run.
- [ ] Full docs build.
- [ ] Notebook check.
- [ ] Control Room final verification.
- [ ] Update changelog.
- [ ] Add migration notes.
- [ ] Confirm benchmark regressions remain acceptable.
- [ ] Decide final `PyCGE` deprecation/removal wording.
- [ ] Tag and release `0.6.0`.

## Deliverables

- release notes
- migration guide
- stable `0.6.0`

## Acceptance criteria

- [ ] Public API is coherent.
- [ ] Outward-facing materials are aligned.
- [ ] Benchmarks still validate.
- [ ] Users can transition cleanly.

---

# 13. Compatibility strategy

## Recommended strategy

Use a **temporary compatibility window**.

That means:

- `CGE` becomes canonical now
- `PyCGE` may remain briefly as compatibility alias
- docs stop using `PyCGE`
- examples stop using `PyCGE`
- notebooks stop using `PyCGE`
- eventual removal happens after migration is complete

## Why this is better

It lets us:

- migrate safely
- avoid breaking everything at once
- keep `main` stable during transition
- update the Control Room and notebooks without panic

If after migration there are effectively no meaningful users of `PyCGE`, we can remove it later.

---

# 14. Testing plan by phase

## Core regression tests

Always keep:

- [ ] benchmark replication tests
- [ ] solve success tests
- [ ] scenario isolation tests
- [ ] comparison tests

## New API tests

Add:

- [ ] `CGE` import test
- [ ] `Equilibrium` creation test
- [ ] `Scenario` isolation test
- [ ] `Result` value access test
- [ ] repeated solve after re-modification test
- [ ] invalid component/index exception test

## Documentation-adjacent tests

Where practical:

- [ ] example scripts execute
- [ ] notebook smoke tests
- [ ] generated code snippets stay valid

---

# 15. Risk register

## Risk 1 — outward-facing materials lag behind core code

**Impact:** confusion
**Mitigation:** Phase 4 explicitly migrates README, docs, notebooks, and Control Room

---

## Risk 2 — breakage of benchmark behavior during refactor

**Impact:** severe
**Mitigation:** freeze outputs in Phase 0 and require regression checks throughout

---

## Risk 3 — overengineering

**Impact:** complexity, maintenance burden
**Mitigation:** keep only four main public concepts: `CGE`, `Equilibrium`, `Scenario`, `Result`

---

## Risk 4 — compatibility drag from keeping `PyCGE` too long

**Impact:** identity problem persists
**Mitigation:** use `PyCGE` only as temporary compatibility layer, not canonical interface

---

## Risk 5 — Control Room code generation mismatch

**Impact:** user confusion
**Mitigation:** dedicated Phase 4D and explicit verification

---

## Risk 6 — DCGE-Core later depends on internals anyway

**Impact:** architectural fragility
**Mitigation:** formal extension contract in Phase 5 and discourage internal access

---

# 16. Rollback strategy

If a phase causes instability:

- keep `main` untouched
- revert only the affected branch/phase
- do not discard benchmark freeze artifacts
- do not proceed to later phases until the earlier one stabilizes

This is another reason the staggered approach is better.

---

# 17. Concrete implementation order

If we want the most pragmatic order, I recommend:

1. Commit the RFC/plan docs
2. Create `reengineer-v0.6` branch
3. Freeze benchmarks and confirm CI
4. Introduce `CGE` public interface
5. Add `Equilibrium`, `Scenario`, `Result`
6. Add `value()` accessors
7. Add scenario isolation and repeated-solve tests
8. Migrate README and examples
9. Migrate notebooks
10. Migrate docs
11. Migrate Control Room code generation/content
12. Clean up inherited naming
13. Release `0.6.0`

That is the best order because it minimizes breakage while steadily moving toward the final architecture.

---

# 18. Definition of success

This refactor succeeds if, after `0.6.0`:

- users see CGE-Core as its own framework
- the canonical interface is `CGE`, not `PyCGE`
- the repo still reproduces validated benchmark results
- notebooks and docs still work
- the Control Room still works and speaks the new API
- a future DCGE-Core can depend on a narrow stable contract
- CGE-Core itself remains static/general and not dynamically contaminated

---

# 19. Bottom line

Yes — **a staggered multi-phase execution is not just better; it is the right strategy**.

This should be treated as a **controlled architectural migration**, not a rewrite.

The best path is:

\[
\text{protect what works}
\rightarrow
\text{introduce a new native API}
\rightarrow
\text{migrate all outward surfaces}
\rightarrow
\text{formalize the extension contract}
\rightarrow
\text{clean up internals last}
\]

That gives CGE-Core a stronger identity, a safer future, and a much better foundation for DCGE-Core later.

---

# 20. Immediate next step

The immediate next step should be:

- [ ] add this execution plan to the repo
- [ ] create `reengineer-v0.6`
- [ ] start Phase 0 only

Do **not** start with renaming everything at once.
