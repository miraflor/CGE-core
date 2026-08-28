# CGE-Core Colab Notebooks

A progressive, executable introduction to CGE-Core.

**New to CGE? Start with Notebook 00 and move downward.**  
Every notebook is self-contained: open it in Google Colab and choose **Runtime → Run all**.

| # | Notebook | What you learn | Open |
|---:|---|---|---|
| 00 | [Start Here](00_start_here.ipynb) | Colab, CGE-Core, and the learning path | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/00_start_here.ipynb) |
| 01 | [Your First CGE](01_your_first_cge.ipynb) | Benchmark equilibrium, Scenario, Result, production and household response | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/01_your_first_cge.ipynb) |
| 02 | [Open-Economy CGE](02_open_economy_cge.ipynb) | Government, trade, taxes, saving, investment, and a tariff scenario | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/02_open_economy_cge.ipynb) |
| 03 | [Policy Experiments](03_policy_experiments.ipynb) | Keep multiple independent Scenario objects alive from one benchmark | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/03_policy_experiments.ipynb) |
| 04 | [Bring Your Own SAM](04_bring_your_own_sam.ipynb) | Convert a balanced SAM CSV into CGE-Core data, solve, and branch a scenario | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/04_bring_your_own_sam.ipynb) |
| 05 | [IFPRI Standard CGE](05_ifpri_standard_cge.ipynb) | Richer model structure, closures, and the dedicated IFPRI scenario API | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/05_ifpri_standard_cge.ipynb) |
| 06 | [CAMCGE Replication](06_camcge_replication.ipynb) | Reproduce a published CGE benchmark and experiment | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/06_camcge_replication.ipynb) |
| 07 | [Under the Hood](07_under_the_hood.ipynb) | PyCGE/Pyomo internals, calibration, closure, DOF, and Walras' law | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/07_under_the_hood.ipynb) |

## Learning path

```text
START
  │
  ▼
What is a CGE?
  │
  ▼
CGE → benchmark Equilibrium → Scenario → Result
  │
  ▼
Open economy + government + trade
  │
  ▼
Several isolated policy scenarios from one benchmark
  │
  ▼
Your own SAM
  │
  ▼
IFPRI Standard CGE (dedicated API)
  │
  ▼
Published CAMCGE replication
  │
  ▼
PyCGE / Pyomo / equations / closure / solver
```

## Branch-safe notebook development

The setup cell no longer hard-resets a cached checkout to `origin/main`.

- Outside Colab, if the notebook is run from a CGE-Core git checkout, it uses the **current checkout** directly.
- In Colab, the notebooks default to `main`.
- To validate another branch or tag in Colab/automation, set the environment variable `CGE_CORE_REF` before running the setup cell, for example `CGE_CORE_REF=v0.6.0`.

This prevents a development notebook from silently testing old `main` while its source came from another branch.

## Notes

- Notebooks 01–04 use the v0.6 `CGE` / `Equilibrium` / `Scenario` / `Result` public workflow.
- The IFPRI notebook intentionally keeps CGE-Core's validated dedicated IFPRI API in v0.6.
- The CAMCGE notebook intentionally keeps the repository-level `cam/` replication workflow.
- Notebook 07 intentionally uses `PyCGE` and raw Pyomo objects because it teaches engine internals; `PyCGE` remains a supported advanced/lower-level API.
- Solver notebooks use an existing IPOPT executable when available; otherwise they install the open-source IPOPT solver from the AMPL COIN module.
- These notebooks are tutorials. For exact equations, validation claims, provenance, and APIs, use the [CGE-Core documentation](https://miraflor.github.io/CGE-core/).

## Citation

If you use CGE-Core in research, see the repository's `CITATION.cff` and README for the software citation and the required citations for underlying model sources.
