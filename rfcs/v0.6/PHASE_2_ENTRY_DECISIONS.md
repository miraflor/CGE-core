# CGE-Core v0.6 — Final Phase 2 Entry Decisions

This file governs the Phase 2 implementation where earlier v0.6 planning documents conflict.

## Public lifecycle

```text
CGE
  └── solve_benchmark()
          ↓
      Equilibrium
          └── scenario()
                  ↓
              Scenario
                  └── solve()
                          ↓
                       Result
```

## Final decisions

1. **`CGE` is a stateless configuration blueprint.** It stores the model definition and data source, not one mutable solved model. Every `solve_benchmark()` call builds a fresh `PyCGE` backend owned by the returned `Equilibrium`.
2. **The public solve verb is `solve_benchmark()`.** `benchmark` is the canonical variable name for the SAM-replicating static equilibrium. The legacy engine may continue using `BASE` internally.
3. **No public `Closure` class in v0.6.** `numeraire=` and `redundant=` are keyword-only Hosoe-backend closure arguments, not a universal backend contract. Future closure requirements are recorded separately and an abstraction is extracted only when a second backend requires it.
4. **Each public `Scenario` owns isolated mutable state.** The first implementation deep-copies the whole calibrated `PyCGE` backend and then uses the unchanged legacy `model_sim`, `model_modify_sim`, and `model_solve` methods. A permanent test guards whole-engine copyability. Refactor `_modify` only if profiling or compatibility evidence makes cloning impractical.
5. **`Scenario.unfix()` is deliberately limited.** It only releases a `Var` previously fixed by `set()` in the same Scenario. Structurally exogenous `Param` objects may be shocked with `set()` but cannot be made endogenous without a model-definition change.
6. **`Result` is an immutable numerical snapshot.** Previously returned results never change after later Scenario mutation or re-solving.
7. **Stable read/comparison surface:** `value(component, *index)`, `objective`, and `compare(reference)`. `to_frame()` and general export/persistence methods are deferred.
8. **No new live-model persistence API.** Legacy dill persistence stays in `PyCGE`; the new object model does not pickle live Pyomo state.
9. **`PyCGE` remains importable and behavior-compatible.** It remains the direct legacy/advanced path and is not immediately inverted into a compatibility facade over new code.
10. **IFPRI and CAMCGE remain on their validated paths in v0.6.** No Phase 2 equation, closure, packaging, or data-layer migration is performed for either.

## Numerical parity policy

- Values copied/extracted from the exact same solved state may be asserted exactly equal.
- Results produced by separate nonlinear solver calls use named tight tolerances rather than a cross-platform bit-for-bit equality promise.
- Existing scientific benchmark tolerances must not be loosened to make an API refactor pass.

## Phase 2 exit bar

Phase 2 is not complete merely because `from cge_core import CGE` works. It ends only when the following lifecycle is solver-tested:

```text
solve benchmark
→ create multiple independent scenarios
→ set shocks
→ solve independently
→ read values
→ compare
→ modify one scenario
→ solve again
→ prove the earlier Result is unchanged
```

The untouched legacy test suite and the new differential facade tests must both pass.
