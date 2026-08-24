# CGE-Core

**A Python/Pyomo framework for computable general equilibrium modelling and reproducible policy simulation.**

CGE-Core separates the **economic model** from the **simulation workflow** and
makes the counterfactual process explicit:

**load data → calibrate → shock → solve → compare**

## Start here

- <a href="control-room/" target="_blank" rel="noopener"><strong>Interactive Control Room ↗</strong></a>
  — explore models, closures, shocks, and generated scenario code.
- **{doc}`tutorials/colab-notebooks`** — learn CGE-Core interactively in Google
  Colab, from the simplest Hosoe economy to IFPRI and CAMCGE.
- **{doc}`getting-started/quickstart`** — run the standard model and a policy counterfactual.
- **{doc}`architecture`** — see how data, equations, solver, and workflow fit together.
- **{doc}`theory/overview`** — understand the economic structure and equations.
- **{doc}`validation/overview`** — see the Hosoe/GAMS, IFPRI, and CAMCGE benchmarks.
- **{doc}`api/index`** — browse the Python API reference.

## The workflow

1. Load benchmark data.
2. Calibrate the model so it reproduces the benchmark equilibrium.
3. Copy the calibrated base into a simulation.
4. Change an exogenous parameter or endowment.
5. Solve the counterfactual equilibrium.
6. Compare the counterfactual with the base.

```text
Benchmark data
      ↓
Calibration
      ↓
Base equilibrium
      ↓
Policy shock
      ↓
Counterfactual equilibrium
      ↓
Comparison
```

A policy experiment is therefore not a single changed equation. It is a **new
internally consistent equilibrium** after endogenous prices and quantities
adjust.

## What is in the project?

| Component | Role |
| --- | --- |
| **Simple CGE** | Small closed-economy teaching model |
| **Standard CGE** | Open economy with trade, government, and investment |
| **IFPRI Standard CGE** | Independently implemented benchmark and policy scenarios |
| **CAMCGE** | Published-model replication benchmark |
| **PyCGE engine** | Calibration, simulation, solving, and comparison |
| **SAM tools** | Convert benchmark accounting into model-ready data |
| **Colab course** | Progressive executable tutorials in the browser |

```{note}
CGE-Core is an independent project. It is not affiliated with or endorsed by
the Policy Simulation Library.
```

For provenance, licensing, and citation metadata, see
[CITATION.cff](https://github.com/miraflor/CGE-core/blob/main/CITATION.cff).
