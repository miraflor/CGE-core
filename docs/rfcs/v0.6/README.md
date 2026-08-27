# CGE-Core v0.6 reengineering decision record

This directory preserves the v0.6 design history while making the governing order explicit.

## Governing order

Where documents conflict, read them in this order:

1. `PHASE_2_ENTRY_DECISIONS.md` — final implementation gate immediately before Phase 2.
2. `COURSE_CORRECTION_RECONCILIATION.md` — accepted/rejected course corrections.
3. `PHASE_1_API_SPECIFICATION_ORIGINAL.md` — original Phase 1 specification, as amended by the two files above.
4. `PHASE_0_ASSESSMENT.md` — repository/architecture assessment and frozen behavior baseline.
5. `STAGGERED_EXECUTION_PLAN.md` — canonical phase numbering and migration order.
6. `REENGINEERING_PLAN_HISTORICAL.md` — early plan retained for history; superseded where conflicting.

## Frozen behavioral baseline

`main` at:

```text
d4dfa7e881339c2101af17caf617dedeb23a7fd8
```

v0.6 is an API reengineering release. Economic equations, benchmark calibration, IFPRI internals, CAMCGE internals, and the data layer are not Phase 2 migration targets.
