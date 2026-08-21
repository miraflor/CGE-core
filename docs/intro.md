# CGE-Core

**A Python/Pyomo framework for computable general equilibrium modelling and reproducible policy simulation.**

CGE-Core separates the **economic model** from the **simulation workflow** and makes the whole counterfactual pipeline explicit:

**load data → calibrate → shock → solve → compare**

::::{grid} 1 2 2 3
:gutter: 2

:::{grid-item-card} Get started
:link: getting-started/quickstart
:link-type: doc

Run the standard model and a policy counterfactual in a few minutes.
:::

:::{grid-item-card} Understand the model
:link: theory/overview
:link-type: doc

Read the economic blocks, equations, closure and benchmark accounting.
:::

:::{grid-item-card} Inspect validation
:link: validation/overview
:link-type: doc

See how Hosoe/GAMS, IFPRI and CAMCGE are used as independent benchmarks.
:::
::::

## The workflow

```{mermaid}
flowchart LR
    A[Benchmark data] --> B[Calibrate]
    B --> C[Base equilibrium]
    C --> D[Apply policy shock]
    D --> E[Solve counterfactual]
    E --> F[Compare with base]
```

CGE-Core is built around the idea that a policy experiment is not a single
changed equation. It is a **new internally consistent equilibrium** after all
endogenous prices and quantities have adjusted.

## What is in the project?

| Component | Role |
| --- | --- |
| **Simple CGE** | Small closed-economy teaching model |
| **Standard CGE** | Open economy with trade, government and investment |
| **IFPRI Standard CGE** | Independently implemented benchmark and policy scenarios |
| **CAMCGE** | Published-model replication benchmark |
| **PyCGE engine** | Calibration, simulation, solving and comparison |
| **SAM tools** | Convert benchmark accounting into model-ready data |

::::{grid} 1 2 2 2
:gutter: 2

:::{grid-item-card} Architecture
:link: architecture
:link-type: doc

See how data, model definitions, the solver, benchmark equilibria and counterfactuals fit together.
:::

:::{grid-item-card} API reference
:link: api/index
:link-type: doc

Browse documentation generated directly from the Python docstrings.
:::
::::

```{note}
CGE-Core is an independent project. It is not affiliated with or endorsed by
the Policy Simulation Library. The `*-Core` name follows the same general
scientific-software naming convention.
```

For provenance, licensing, and citation metadata, see
[CITATION.cff](https://github.com/miraflor/CGE-core/blob/main/CITATION.cff)
in the repository.
