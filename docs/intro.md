# CGE-Core

**A Python/Pyomo framework for computable general equilibrium modelling and reproducible policy simulation.**

CGE-Core separates the **economic model** from the **simulation workflow** and
makes the counterfactual process explicit:

**benchmark data → solve benchmark → create scenario → shock → solve → compare**

## Start here

- <a href="control-room/" target="_blank" rel="noopener"><strong>Interactive Control Room ↗</strong></a>
  — explore models, closures, shocks, and runnable scenario code.
- **{doc}`tutorials/colab-notebooks`** — learn CGE-Core interactively in Google
  Colab, from the simplest Hosoe economy to IFPRI and CAMCGE.
- **{doc}`getting-started/quickstart`** — run the standard model and a policy counterfactual.
- **{doc}`architecture`** — see how the public API, model equations, solver, and validated engine fit together.
- **{doc}`theory/overview`** — understand the economic structure and equations.
- **{doc}`validation/overview`** — see the Hosoe/GAMS, IFPRI, and CAMCGE benchmarks.
- **{doc}`api/index`** — browse the Python API reference.

## The public workflow

For the Hosoe teaching models, ordinary v0.6 usage starts with `CGE`:

```text
CGE(model, data)
      ↓
solve_benchmark(...)
      ↓
Equilibrium
      ↓
scenario(name)
      ↓
Scenario.set(...)
      ↓
Scenario.solve()
      ↓
Result.compare(benchmark)
```

A `CGE` object is a stateless model blueprint. A solved `Equilibrium` protects
the benchmark state. Each `Scenario` is an independent counterfactual, and each
successful solve returns an immutable numerical `Result` snapshot.

A policy experiment is therefore not a single changed equation. It is a **new
internally consistent equilibrium** after endogenous prices and quantities
adjust.

## What is in the project?

| Component | Role |
| --- | --- |
| **Simple CGE** | Small closed-economy teaching model |
| **Standard CGE** | Open economy with trade, government, and investment |
| **Public CGE API** | `CGE`, `Equilibrium`, `Scenario`, and `Result` |
| **PyCGE engine** | Supported lower-level engine used by the Hosoe façade and advanced workflows |
| **IFPRI Standard CGE** | Independently implemented benchmark and policy scenarios |
| **CAMCGE** | Published-model replication benchmark |
| **SAM tools** | Convert benchmark accounting into model-ready data |
| **Colab course** | Progressive executable tutorials in the browser |

```{note}
CGE-Core is an independent project. It is not affiliated with or endorsed by
the Policy Simulation Library.
```

For provenance, licensing, and citation metadata, see
[CITATION.cff](https://github.com/miraflor/CGE-core/blob/main/CITATION.cff).
