# CGE-Core v0.6 ↔ GAMS workflow crosswalk

This is a practitioner-intuition and design-sanity aid, not a requirement that Python imitate GAMS. A public operation should have either a recognizable GAMS counterpart or a short explanation of why the Python object model improves on the serial GAMS discipline.

| CGE-Core v0.6 | GAMS idiom | Manual discipline automated |
|---|---|---|
| `CGE(model=StdCGE(), data=...)` | sets/data/parameters/equations declared before solve | Configures the static economy and its data source. |
| `model.solve_benchmark(numeraire=("pf","LAB"), redundant=("eqpf","LAB"))` | `pf.fx("LAB") = 1;` + Walras-law equation omission + first `solve` | Applies the Hosoe closure, solves the SAM-replicating benchmark, and protects it behind an `Equilibrium`. |
| `Equilibrium` | benchmark `.l` levels protected by convention/report parameters | Makes the benchmark structurally read-only at the public API. |
| `benchmark.scenario("tariff abolition")` | begin/reset an experiment block | Creates an isolated counterfactual without manual reset bookkeeping. |
| `scenario.set("taum", "BRD", 0)` | parameter assignment; for a Var, `.fx` | Applies a scenario shock. |
| `scenario.unfix("epsilon")` | release a Var previously fixed in the experiment | Releases only a Var fixed earlier by this Scenario; this is not a general GEMPACK-style closure swap. |
| `result = scenario.solve()` | second `solve` | Solves the counterfactual and returns an immutable snapshot. |
| `result.value("Z", "BRD")` | `Z.l("BRD")` | Reads a solved level without traversing the live model. |
| `result.compare(benchmark)` | hand-built report table | Computes `self-reference` differences and percentage changes consistently. |
| multiple live `Scenario` objects | no direct serial-script equivalent without manual state management | Python object ownership keeps counterfactuals simultaneously live and isolated. |

## Terminology layer rule

- **benchmark**: the SAM-replicating static equilibrium;
- **scenario / counterfactual / experiment**: a static policy solve derived from that benchmark;
- **baseline**: reserved for a reference path in dynamic/forecast contexts rather than the static benchmark solve.
