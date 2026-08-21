# CGE-Core

**A Python/Pyomo framework for computable general equilibrium modelling and reproducible policy simulation.**

CGE-Core separates the **economic model** from the **simulation workflow**:

**load data → calibrate → shock → solve → compare**

It includes textbook CGE implementations and independent validation benchmarks built around Hosoe, the IFPRI Standard CGE model, and CAMCGE.

## Start here

| If you want to… | Go to |
| --- | --- |
| Install CGE-Core | {doc}`getting-started/installation` |
| Run a model in a few minutes | {doc}`getting-started/quickstart` |
| See a complete policy counterfactual | {doc}`getting-started/first-simulation` |
| Understand the equations | {doc}`theory/overview` |
| Compare the available models | {doc}`models/overview` |
| Inspect validation evidence | {doc}`validation/overview` |

## What CGE-Core provides

- Pyomo-based CGE model definitions
- calibration from benchmark data
- baseline and counterfactual simulation
- Social Accounting Matrix tooling
- explicit model closure and Walras'-law handling
- pandas-based comparison of simulation results
- regression and replication benchmarks

## Models and benchmarks

| Component | Role |
| --- | --- |
| Simple CGE | Small closed-economy teaching model |
| Standard CGE | Open-economy model with trade, government and investment |
| IFPRI Standard CGE | Independently implemented benchmark and policy scenarios |
| CAMCGE | Published-model replication benchmark |

```{note}
CGE-Core is an independent project. It is not affiliated with or endorsed by the Policy Simulation Library. The `*-Core` name follows the same general scientific-software naming convention.
```

For provenance, licensing and citation information, see the project repository and `CITATION.cff`.
