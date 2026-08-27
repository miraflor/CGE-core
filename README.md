# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/00_start_here.ipynb)

A Pyomo-based **Computable General Equilibrium (CGE)** framework for calibrated
policy simulation, model validation, and reproducible research.

CGE-Core currently supports four benchmark families:

| Subsystem | Reference | Role |
| --- | --- | --- |
| `splcge` | Hosoe, Gasawa & Hashimoto (2010), ch. 3–4 | Simple closed-economy teaching model |
| `stdcge` | Hosoe, Gasawa & Hashimoto (2010), ch. 5–6 | Open economy with Armington/CET, government, trade, and investment |
| `cge_core.ifpri` | IFPRI Standard CGE test economy | Independently implemented benchmark with explicit closures and policy scenarios |
| `cam/` | Condon, Dahl & Devarajan (1987) CAMCGE | Repository-level replication and regression benchmark |

> **Independent project.** CGE-Core is not affiliated with or endorsed by the
> Policy Simulation Library. The `*-Core` name follows the general naming
> convention used by projects such as [OG-Core](https://github.com/PSLmodels/OG-Core).

---

## Explore, learn, then use

CGE-Core has three entry points depending on what you want to do.

### 1. Interactive Control Room

**[Launch the CGE-Core Control Room →](https://miraflor.github.io/CGE-core/control-room/)**

Explore the model families visually, inspect closures and policy shocks, and
generate runnable scenario code in the browser. No installation is required.

### 2. Learn CGE-Core in Google Colab

**[Start the Colab notebook course →](notebooks/README.md)**

The notebook series is deliberately progressive:

| # | Notebook | What it teaches | Colab |
| ---: | --- | --- | --- |
| 00 | [Start Here](notebooks/00_start_here.ipynb) | CGE-Core, Colab, and the learning path | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/00_start_here.ipynb) |
| 01 | [Your First CGE](notebooks/01_your_first_cge.ipynb) | The smallest complete CGE: production, households, factors, prices, market clearing | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/01_your_first_cge.ipynb) |
| 02 | [Open-Economy CGE](notebooks/02_open_economy_cge.ipynb) | Government, taxes, imports, exports, saving, and investment | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/02_open_economy_cge.ipynb) |
| 03 | [Policy Experiments](notebooks/03_policy_experiments.ipynb) | Compare tariff, production-tax, and factor-endowment shocks | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/03_policy_experiments.ipynb) |
| 04 | [Bring Your Own SAM](notebooks/04_bring_your_own_sam.ipynb) | Convert a balanced SAM CSV into model-ready data | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/04_bring_your_own_sam.ipynb) |
| 05 | [IFPRI Standard CGE](notebooks/05_ifpri_standard_cge.ipynb) | Richer model structure, macro closures, and IFPRI scenarios | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/05_ifpri_standard_cge.ipynb) |
| 06 | [CAMCGE Replication](notebooks/06_camcge_replication.ipynb) | Reproduce a published CGE benchmark and policy experiment | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/06_camcge_replication.ipynb) |
| 07 | [Under the Hood](notebooks/07_under_the_hood.ipynb) | Pyomo, calibration, closure, degrees of freedom, numeraire, and Walras' law | [Open ↗](https://colab.research.google.com/github/miraflor/CGE-core/blob/main/notebooks/07_under_the_hood.ipynb) |

Each notebook is self-contained: open it in Colab and choose **Runtime → Run all**.

### 3. Documentation

**[Read the CGE-Core documentation →](https://miraflor.github.io/CGE-core/)**

The documentation covers model architecture, theory, equations, closures,
tutorials, validation, and the Python API.

---

## What CGE-Core does

CGE-Core separates the **economic model definition**, the solved **benchmark
equilibrium**, and mutable **counterfactual scenarios**.

```text
SplCGE / StdCGE + data
          │
          ▼
         CGE
          │  solve_benchmark(...)
          ▼
     Equilibrium
          │  scenario(...)
          ▼
       Scenario
          │  set(...)
          │  solve()
          ▼
        Result
          │  value(...)
          └  compare(...)
```

`CGE` is a stateless blueprint. Each benchmark solve owns its own calibrated
backend, and every `Scenario` owns isolated mutable state. A solved `Result` is
an immutable numerical snapshot, so later scenario changes cannot rewrite an
earlier result.

The v0.6 façade currently covers the engine-backed Hosoe models (`SplCGE` and
`StdCGE`). The validated IFPRI subsystem keeps its dedicated API, and CAMCGE
remains a repository-level replication benchmark.

A CGE policy experiment is not a partial-equilibrium price change or a manually
imposed output response. A shock changes an exogenous policy, endowment, or
external assumption; the model then solves for a new internally consistent
equilibrium.

Under the façade, CGE-Core continues to reuse the validated `PyCGE` engine.
Advanced users may still access that workflow directly, but new user-facing
code should prefer the `CGE` interface below.

---

## Installation

CGE-Core requires Pyomo and one nonlinear solver.

### Option A — IPOPT executable with conda

```bash
conda install -c conda-forge ipopt
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e .
```

Then use solver name `ipopt`.

### Option B — cyipopt

```bash
sudo apt-get install -y coinor-libipopt-dev
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e ".[solver,test]"
python -m pyomo.contrib.pynumero.build
```

Then use solver name `cyipopt`.

The bundled Hosoe examples auto-detect an available supported local solver.

---

## Quick start

```python
from cge_core import CGE, example_data
from cge_core.models import StdCGE

model = CGE(
    model=StdCGE(),
    data=example_data("stdcge"),
)

benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)

scenario = benchmark.scenario("tariff abolition")
scenario.set("taum", "BRD", 0)
scenario.set("taum", "MLK", 0)

result = scenario.solve()

print(result.value("Z", "BRD"))
print(result.objective)
print(result.compare(benchmark))
```

`result.compare(benchmark)` reports **scenario minus benchmark**.
Percentage changes are `(scenario - benchmark) / benchmark × 100`.

### Legacy and advanced workflow API

`PyCGE` remains importable and behavior-compatible for advanced users,
low-level model inspection, and existing code during the v0.6 migration.
It is no longer the canonical interface for new user-facing examples.

```python
from cge_core import PyCGE
```

---

## Why one market-clearing equation is dropped

After fixing a numeraire, a CGE should have the same number of independent
equilibrium conditions as free endogenous variables. **Walras' law** makes one
market-clearing condition redundant: if every other market clears and all
budget constraints hold, the final market clears automatically.

For the Hosoe façade, the closure is stated explicitly when the benchmark is
solved:

```python
benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

The underlying validated engine accepts only model-declared redundant
market-clearing candidates and checks that the resulting system has zero
degrees of freedom.

---

## Using your own SAM

`cge_core.samtools` converts a single balanced SAM CSV into the set and
parameter files consumed by the Hosoe standard model.

```python
from cge_core import CGE, samtools
from cge_core.models import StdCGE

accounts = dict(
    hoh="HH",
    gov="GOVT",
    inv="SAV-INV",
    ext="ROW",
    idt="ITAX",
    trf="TARIFF",
)

samtools.build_dataset(
    "my_sam.csv",
    "my_data_dir",
    factors=["CAP", "LAB"],
    institutions=accounts.values(),
)

model = CGE(
    model=StdCGE(accounts=accounts),
    data="my_data_dir",
)

benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
)
```

A balanced SAM is necessary but not sufficient: it must also have the
institutional structure and nonzero/positivity properties required by the
reference model's calibration equations.

---

## IFPRI Standard CGE subsystem

`cge_core.ifpri` implements an independently authored Python/Pyomo version of
the IFPRI Standard CGE **test economy**, including:

- algebraic calibration;
- explicit macro and factor-market closures;
- nonlinear BASE solving;
- five recorded policy scenarios;
- pandas-based reporting;
- external validation against full-precision reference targets.

Implemented scenarios include:

| Scenario | Experiment |
| --- | --- |
| `TARCUT1` | 50% tariff cut; government saving flexible |
| `TARCUT2` | 50% tariff cut; government saving fixed and direct tax adjusts |
| `FSAVINCR` | foreign saving +10% |
| `PWMINCR` | world import prices +10% |
| `DEVAL` | 10% devaluation under a fixed-exchange-rate closure |

The official IFPRI source package and `test.dat` are **not distributed** with
CGE-Core. Public tests and the Colab tutorial use an independently authored,
redistributable synthetic IFPRI-format economy.

See [`docs/IFPRI.md`](docs/IFPRI.md).

---

## CAMCGE replication benchmark

The repository-level `cam/` module reproduces the Cameroon CGE model published
by Condon, Dahl, and Devarajan (1987).

The replication checks:

- the published base objective value;
- 98 published base-equilibrium variable levels;
- the dropped current-account equation;
- three published policy experiments.

This is a **replication and regression benchmark**, not a claim that the
underlying Cameroon model was authored as part of CGE-Core.

See:

- [`cam/README.md`](cam/README.md)
- [`CAMCGE_REPLICATION_GUIDE.md`](CAMCGE_REPLICATION_GUIDE.md)
- [`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md)

---

## Reliability safeguards

CGE-Core includes explicit checks for:

- balanced, square, finite SAM inputs;
- complete model data directories;
- valid goods/factor/institution partitions;
- safe workflow ordering;
- declared closure anchors;
- declared redundant market-clearing equations;
- zero degrees of freedom after closure;
- isolated scenario state and repeated scenario re-solving;
- solver optimality/termination;
- preservation of the solved benchmark;
- immutable numerical result snapshots and comparison tables.

The test suite covers the Hosoe models, the engine, SAM tools, IFPRI calibration
and scenarios, CAMCGE data/structure/replication, and solver-dependent
regressions.

```bash
pytest tests/ -v
```

---

## Provenance and license

CGE-Core is a corrected fork of
[PyCGE](https://github.com/juanfung/pycge) by Juan Fung and Charley
Burtwistle of the U.S. National Institute of Standards and Technology.

The original PyCGE code is a U.S. Government work and is public domain under
17 U.S.C. 105; the original notice is retained in `LICENSE_NIST.txt`.

CGE-Core modifications — including the revised workflow, degree-of-freedom
handling, input validation, reporting utilities, SAM tooling, clean-room IFPRI
subsystem, CAMCGE replication benchmark, documentation, and test suite — are
released under the MIT License.

### Authorship

**James Matthew Miraflor**  
Scientific Computing Laboratory  
Department of Computer Science  
University of the Philippines Diliman  
<jbmiraflor@up.edu.ph>

This fork is maintained by James Matthew Miraflor, who directed and reviewed an
AI-assisted revision, testing, and documentation workflow. Authorship of
CGE-Core as a revised software project does not imply authorship of the
underlying PyCGE code, Hosoe models, IFPRI specification, or CAMCGE model.

---

## Citation

If you use CGE-Core, cite the software and the relevant underlying model
sources.

```bibtex
@software{miraflor2026cgecore,
  author  = {James Matthew Miraflor},
  title   = {{CGE-Core}: a Pyomo-based computable general equilibrium framework},
  year    = {2026},
  version = {0.5.0},
  url     = {https://github.com/miraflor/CGE-core}
}
```

Also cite:

- Fung & Burtwistle / NIST PyCGE for inherited PyCGE code;
- Hosoe, Gasawa & Hashimoto (2010) when using `splcge` or `stdcge`;
- the official IFPRI Standard CGE documentation/source when using the IFPRI subsystem;
- Condon, Dahl & Devarajan (1987) and GAMS `camcge` when using the CAMCGE benchmark.

Machine-readable citation metadata is in [`CITATION.cff`](CITATION.cff).

---

## References

- Hosoe, N., Gasawa, K. & Hashimoto, H. (2010). *Textbook of Computable
  General Equilibrium Modelling: Programming and Simulations.* Palgrave
  Macmillan.
- GAMS Model Library:
  [`splcge.gms`](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_splcge.html),
  [`stdcge.gms`](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_stdcge.html)
- Condon, T., Dahl, H. & Devarajan, S. (1987). *Implementing a Computable
  General Equilibrium Model on GAMS: The Cameroon Model.* World Bank DRD290.
- Original PyCGE: https://github.com/juanfung/pycge
