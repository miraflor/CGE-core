# CGE-Core Colab Notebooks

A progressive, executable introduction to CGE-Core.

**New to CGE? Start with Notebook 00 and move downward.**  
Every notebook is self-contained: open it in Google Colab and choose **Runtime → Run all**.

| # | Notebook | What you learn | Open |
|---:|---|---|---|
| 00 | [Start Here](00_start_here.ipynb) | Colab, CGE-Core, and the learning path | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/00_start_here.ipynb) |
| 01 | [Your First CGE](01_your_first_cge.ipynb) | Production, households, factors, prices, market clearing | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/01_your_first_cge.ipynb) |
| 02 | [Open-Economy CGE](02_open_economy_cge.ipynb) | Government, trade, taxes, saving, investment | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/02_open_economy_cge.ipynb) |
| 03 | [Policy Experiments](03_policy_experiments.ipynb) | Compare multiple shocks from one calibrated baseline | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/03_policy_experiments.ipynb) |
| 04 | [Bring Your Own SAM](04_bring_your_own_sam.ipynb) | Convert a balanced SAM CSV into CGE-Core data | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/04_bring_your_own_sam.ipynb) |
| 05 | [IFPRI Standard CGE](05_ifpri_standard_cge.ipynb) | Richer model structure, closures, and IFPRI scenarios | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/05_ifpri_standard_cge.ipynb) |
| 06 | [CAMCGE Replication](06_camcge_replication.ipynb) | Reproduce a published CGE benchmark and experiment | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/06_camcge_replication.ipynb) |
| 07 | [Under the Hood](07_under_the_hood.ipynb) | Pyomo, calibration, closure, DOF, Walras' law | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/07_under_the_hood.ipynb) |

## Learning path

```text
START
  │
  ▼
What is a CGE?
  │
  ▼
Tiny closed economy
  │
  ▼
Open economy + government + trade
  │
  ▼
Policy scenario laboratory
  │
  ▼
Your own SAM
  │
  ▼
IFPRI Standard CGE
  │
  ▼
Published CAMCGE replication
  │
  ▼
Pyomo / equations / closure / solver
```

## Notes

- The Hosoe notebooks use CGE-Core's bundled `splcge` and `stdcge` datasets.
- The IFPRI notebook defaults to CGE-Core's independently authored, redistributable synthetic IFPRI-format economy. The official IFPRI `test.dat` is not distributed by CGE-Core.
- The CAMCGE notebook uses the repository-level `cam/` replication benchmark.
- Solver notebooks install the open-source IPOPT solver from the AMPL COIN module and expose it to Pyomo.
- These notebooks are tutorials. For exact equations, validation claims, provenance, and APIs, use the [CGE-Core documentation](https://miraflor.github.io/CGE-core/).

## Citation

If you use CGE-Core in research, see the repository's `CITATION.cff` and README for the software citation and the required citations for underlying model sources.
