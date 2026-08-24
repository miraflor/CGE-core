# Colab Notebook Course

CGE-Core includes a progressive set of executable Google Colab notebooks.
Each notebook is self-contained: open it in Colab, choose **Runtime → Run all**,
then edit the highlighted policy or data cells.

The series is designed as a learning ladder:

```text
What is a CGE?
      ↓
Tiny closed economy
      ↓
Open economy + government + trade
      ↓
Policy scenario laboratory
      ↓
Bring your own SAM
      ↓
IFPRI Standard CGE
      ↓
Published CAMCGE replication
      ↓
Pyomo / equations / closure / solver
```

## Notebook series

| # | Notebook | Main idea | Open in Colab |
| ---: | --- | --- | --- |
| 00 | **Start Here** | Colab, CGE-Core, and the learning path | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/00_start_here.ipynb) |
| 01 | **Your First CGE** | Hosoe `splcge`: production, households, factors, prices, and market clearing | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/01_your_first_cge.ipynb) |
| 02 | **Open-Economy CGE** | Hosoe `stdcge`: government, trade, taxes, saving, and investment | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/02_open_economy_cge.ipynb) |
| 03 | **Policy Experiments** | Compare tariff, production-tax, and factor-endowment shocks | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/03_policy_experiments.ipynb) |
| 04 | **Bring Your Own SAM** | Convert a balanced SAM CSV into a CGE-Core dataset with `samtools` | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/04_bring_your_own_sam.ipynb) |
| 05 | **IFPRI Standard CGE** | Richer model structure, macro closures, and IFPRI policy scenarios | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/05_ifpri_standard_cge.ipynb) |
| 06 | **CAMCGE Replication** | Reproduce a published CGE benchmark and policy experiment | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/06_camcge_replication.ipynb) |
| 07 | **Under the Hood** | Pyomo objects, calibration, degrees of freedom, numeraire, and Walras' law | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/07_under_the_hood.ipynb) |

## Why this sequence?

The first two executable models are deliberately small. `splcge` isolates the
essence of general equilibrium without government or trade. `stdcge` then adds
the institutions and external-sector structure used for policy analysis.

The next notebooks separate **model**, **scenario**, **closure**, and **data**
before moving to the substantially richer IFPRI subsystem.

CAMCGE is a replication capstone rather than merely a larger model: it shows
that CGE-Core can reproduce an independently published benchmark and policy
experiments.

```{note}
The IFPRI notebook uses CGE-Core's independently authored, redistributable
synthetic IFPRI-format economy by default. The official IFPRI `test.dat` is
not distributed with CGE-Core.
```

## Colab and solvers

The executable notebooks install the current CGE-Core checkout and make IPOPT
available to Pyomo in the Colab runtime. Nothing is permanently installed on
your own computer.

For local installation and solver options, see
{doc}`../getting-started/installation`.

For the exact model equations and assumptions, use
{doc}`../models/overview` and {doc}`../theory/overview`. The notebooks are
executable introductions, not substitutes for the reference documentation.
