# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb)

**CGE-Core is an open-source, Pyomo-based framework for computable general
equilibrium modelling, built for policy simulation, teaching, replication,
and reproducible research in Python.**

Computable general equilibrium (CGE) models are useful precisely because policy
changes do not stop where they begin. A tariff, tax, subsidy, productivity
change, or factor-supply shock can propagate through production, household
income, trade, government accounts, saving and investment, factor markets,
relative prices, and welfare. A CGE model makes those economy-wide connections
explicit and solves for a new internally consistent equilibrium.

The difficulty is that learning or applying CGE often means learning several
things at once: the economics, the social accounting structure, calibration,
closure choices, nonlinear solution, and the surrounding software workflow.

**CGE-Core exists to make CGE easier to inspect, teach, reproduce, extend, and
use in scientific Python without simplifying away the economics.**

## Why CGE-Core?

CGE-Core is intended to provide a common scientific home for CGE work in
Python.

- **Learn from complete models.** Start with small textbook economies and move
  toward richer open-economy and published models without changing programming
  ecosystems.
- **Run policy experiments.** Begin from a calibrated benchmark, change an
  exogenous policy or assumption, solve the counterfactual equilibrium, and
  compare it with the benchmark.
- **Bring economic data into the workflow.** Use a social accounting matrix
  (SAM) as the empirical accounting foundation of a model, with explicit
  validation of the structure required by the chosen specification.
- **Reproduce published models.** Treat benchmark targets, closures,
  provenance, and numerical validation as part of the software rather than as
  external afterthoughts.
- **Keep the economics visible.** CGE-Core removes routine repository, solver,
  and framework setup from ordinary use, but it does not hide model equations,
  closure assumptions, shocks, benchmark data, or validation evidence.
- **Fit CGE into scientific Python.** Models, data preparation, experiments,
  reporting, tests, notebooks, and extensions can live in the same environment
  as the rest of a Python research workflow.

The goal is **not** to impose one universal CGE equation system. Different CGE
traditions make different modelling choices. CGE-Core instead gives distinct
model families a common high-level lifecycle:

```text
benchmark → scenario → solve → compare
```

while allowing each family to retain its own equations, calibration, closure,
variables, data requirements, and validation targets.

## Included model families

| Entry point | Reference / tradition | Role |
|---|---|---|
| `SimpleCGE` | Hosoe, Gasawa & Hashimoto (2010), ch. 3–4 | Small closed-economy model for learning CGE mechanics |
| `StandardCGE` | Hosoe, Gasawa & Hashimoto (2010), ch. 5–6 | Open economy with intermediate inputs, government, Armington/CET trade, saving, and investment |
| `CamCGE` | Condon, Dahl & Devarajan (1987) | Published Cameroon model used for historical replication and policy-experiment validation |
| `IFPRICGE` | IFPRI Standard CGE tradition | Richer CGE implementation with explicit macro closures and recorded policy scenarios |

These are not four skins over the same model. They are separate economic
implementations brought together by a common project, validation philosophy,
and practitioner workflow.

> **Independent project.** CGE-Core is not affiliated with or endorsed by the
> Policy Simulation Library. The `*-Core` name follows the broader naming
> convention used by projects such as
> [OG-Core](https://github.com/PSLmodels/OG-Core).

---

## Start in thirty seconds

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)

result = reform.solve()

result.summary()
result.compare(base)
```

The ordinary workflow stays at the modelling level: choose a model, solve the
benchmark, define a scenario, apply an economic shock, solve again, and compare
the two equilibria.

Advanced users can still select a solver explicitly, inspect Pyomo objects,
work with the lower-level API, or build custom models.

## What a CGE experiment means

A CGE experiment is not a manually imposed change in output or price.

Instead:

```text
benchmark economy
      ↓
change an exogenous policy, endowment, or external assumption
      ↓
solve the entire system again
      ↓
new equilibrium
      ↓
compare with benchmark
```

For example, removing a tariff changes the relevant tax wedge. The model then
endogenously determines the resulting changes in imports, domestic production,
factor demand, household income, government revenue, prices, saving,
investment, and welfare according to the equations and closure of that model.

That economy-wide adjustment is the point of CGE.

---

## Explore without installing

- **[CGE-Core Control Room](https://miraflor.github.io/CGE-core/control-room/)** —
  inspect bundled models, read their economic structure, configure a policy
  experiment, and generate runnable Python.
- **[Notebook course](https://miraflor.github.io/CGE-core/tutorials/colab-notebooks.html)** —
  a progressive sequence from the first solve to SAMs, CAMCGE, IFPRI, model
  authoring, and internals.
- **[Open the first notebook in Colab](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb)** —
  one installation cell, then modelling code.
- **[Documentation](https://miraflor.github.io/CGE-core/)** —
  theory, models, tutorials, validation, API reference, and developer
  documentation.

---

## Install

Install the v0.8.0 release wheel:

```bash
pip install "https://github.com/miraflor/CGE-core/releases/download/v0.8.0/cge_core-0.8.0-py3-none-any.whl"
```

Then:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

The release wheel contains the runtime package and required bundled model data,
not the entire GitHub repository. Runtime dependencies such as Pyomo and solver
support are resolved separately by `pip`.

CGE-Core uses an existing supported nonlinear solver when one is available.
Otherwise the normal `.solve()` path prepares the supported default open-source
backend internally.

For reproducibility or solver-specific work, advanced users can request a
particular backend explicitly:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

---

## The common modelling workflow

Although the bundled model families are economically different, the
practitioner workflow is deliberately consistent.

### 1. Solve a benchmark

```python
base = StandardCGE.example().solve()
```

The benchmark is the calibrated reference equilibrium.

### 2. Create an isolated scenario

```python
policy = base.scenario("Policy reform")
```

A scenario is independent of the solved benchmark and of other scenarios.

### 3. Apply an economic shock

```python
policy.tariff("BRD", change=-0.50)
policy.production_tax("MLK", 0.05)
policy.endowment("CAP", change=0.10)
```

Semantic helpers are used where a model has a clear economic interpretation.

For an advanced component without a dedicated helper:

```python
policy.set("taum", "BRD", 0.0)
```

### 4. Solve and compare

```python
result = policy.solve()

result.summary()
result.compare(base)
```

The comparison reports the counterfactual relative to the benchmark rather
than mutating or replacing the original equilibrium.

---

## What can be studied?

The exact shocks available depend on the model, but CGE-Core is designed for
experiments involving changes such as:

- tariffs and trade-policy wedges;
- production and indirect taxes;
- factor endowments;
- productivity and technology assumptions;
- foreign saving and external-balance assumptions;
- world prices;
- exchange-rate and macro-closure choices;
- government saving or direct-tax adjustment;
- model-specific policy parameters.

The economic interpretation of a shock belongs to the model itself. CGE-Core
does not assume that every model has the same variables or policy instruments.

---

## Bring your own SAM

A social accounting matrix records the circular flow of income and expenditure
across production activities, commodities, factors, households, government,
investment, and the rest of the world.

For a balanced SAM using the canonical Hosoe account labels:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

For country-specific account labels, state the economic roles explicitly:

```python
economy = StandardCGE.from_sam(
    "country_sam.csv",
    factors=["LAB", "CAP"],
    household="HH",
    government="GOVT",
    investment="SAVINV",
    rest_of_world="ROW",
    indirect_tax="PTAX",
    tariff="TARIFF",
)
```

`from_sam()` validates the accounting table and constructs the internal model
dataset.

A balanced SAM is necessary but not sufficient for a particular CGE
specification. The SAM must also satisfy that model's institutional structure,
nonzero-flow requirements, and calibration assumptions.

---

## SimpleCGE and StandardCGE

The Hosoe models provide the clearest route into CGE-Core.

### `SimpleCGE`

`SimpleCGE` is a small closed-economy model useful for learning the mechanics
of:

- production;
- factor demand;
- household income;
- consumption;
- factor markets;
- commodity markets;
- relative prices;
- the benchmark/counterfactual distinction.

```python
from cge_core import SimpleCGE

base = SimpleCGE.example().solve()
```

### `StandardCGE`

`StandardCGE` extends the structure to include:

- intermediate inputs;
- government;
- indirect taxes;
- tariffs;
- imports and exports;
- Armington composite demand;
- CET transformation;
- saving and investment;
- an open-economy external account.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

These implementations follow the textbook models of Hosoe, Gasawa, and
Hashimoto and remain separately validated against their reference behavior.

---

## CAMCGE

```python
from cge_core import CamCGE

base = CamCGE.example().solve()

windfall = base.scenario("Oil windfall")
windfall.set("fsav", None, 500)

result = windfall.solve()
```

`CamCGE` is based on the Cameroon model published by Condon, Dahl, and
Devarajan (1987).

It is included as a first-class installed model because it provides something
different from the Hosoe models: a published historical CGE specification with
reported benchmark levels and policy experiments that can be used as
independent replication targets.

The runtime model lives under:

```text
cge_core/models/camcge/
```

while replication and validation utilities live separately under:

```text
validation/cam/
```

This keeps the installed model distinct from the evidence used to verify it.

See:

- [`CAMCGE_REPLICATION_GUIDE.md`](CAMCGE_REPLICATION_GUIDE.md)
- [`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md)
- [`validation/cam/README.md`](validation/cam/README.md)

---

## IFPRI Standard CGE

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()

reform = base.scenario("TARCUT1").solve()
reform.compare(base)
```

The IFPRI implementation is architecturally richer than the Hosoe models and
retains its own:

- dataset schema;
- algebraic calibration;
- macro closures;
- factor-market treatment;
- scenario construction;
- nonlinear solve path;
- reporting;
- validation machinery.

Recorded policy scenarios include experiments such as tariff cuts, changes in
foreign saving, changes in world import prices, and devaluation under the
appropriate closure.

### IFPRI clean-room boundary

The public package includes an **independently authored, redistributable
synthetic IFPRI-format economy** so that the implementation can be exercised in
CI, notebooks, and tutorials.

It is not the official IFPRI benchmark dataset.

Official-source replication remains a separate validation path for users who
possess the required external material. CGE-Core does not redistribute the
official IFPRI source package or `test.dat`.

See:

- [`docs/IFPRI.md`](docs/IFPRI.md)
- [`docs/ifpri_cleanroom.md`](docs/ifpri_cleanroom.md)
- [`docs/validation.md`](docs/validation.md)

---

## Notebook course

The canonical v0.8.0 sequence is:

| # | Notebook | What you will do | Open in Colab |
|---:|---|---|---|
| 01 | [`01_first_cge.ipynb`](notebooks/01_first_cge.ipynb) | Solve and read an economy | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb) |
| 02 | [`02_policy_experiments.ipynb`](notebooks/02_policy_experiments.ipynb) | Benchmark → shock → counterfactual → comparison | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/02_policy_experiments.ipynb) |
| 03 | [`03_your_own_sam.ipynb`](notebooks/03_your_own_sam.ipynb) | Inspect and load a SAM | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/03_your_own_sam.ipynb) |
| 04 | [`04_camcge.ipynb`](notebooks/04_camcge.ipynb) | Reproduce a published CGE model | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/04_camcge.ipynb) |
| 05 | [`05_ifpri.ipynb`](notebooks/05_ifpri.ipynb) | IFPRI synthetic public path and clean-room boundary | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/05_ifpri.ipynb) |
| 06 | [`06_build_a_model.ipynb`](notebooks/06_build_a_model.ipynb) | Functional Python and experimental `.cge.md` authoring | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/06_build_a_model.ipynb) |
| 90 | [`90_internals.ipynb`](notebooks/90_internals.ipynb) | Pyomo and lower-level CGE-Core internals | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/90_internals.ipynb) |

**[View the full notebook course →](https://miraflor.github.io/CGE-core/tutorials/colab-notebooks.html)**

Historical notebook filenames remain available in earlier Git tags; the active directory contains one course only.

---

## Build or extend a model

CGE-Core has two extension paths.

### Functional Python authoring

A custom model can be constructed with ordinary Python functions rather than
requiring inheritance from a framework base class:

```python
def build_model(data):
    ...
    return model


def apply_default_closure(model):
    ...
```

Model metadata can explicitly declare concepts such as benchmark-only
components and shockable parameters.

### Experimental `.cge.md`

The experimental `.cge.md` format allows prose and executable model
specification to coexist in one Markdown document.

Only fenced `cge` blocks are executable; surrounding prose is inert.

The format is intentionally limited and experimental. The validated bundled
models are **not** being rewritten into the DSL merely for architectural
uniformity.

---

## Source layout

The v0.8.0 source tree has one canonical location for each responsibility:

```text
cge_core/
├── workflow.py          benchmark → scenario → result lifecycle
├── _engine.py           v0.8 engine policy adapter
├── _pycge.py            inherited lower-level PyCGE engine
├── solver.py            numerical-backend resolution
├── sam.py               social-accounting-matrix tools
├── models/              bundled economic model families
│   ├── simple/
│   ├── standard/
│   ├── camcge/
│   └── ifpri/
└── experimental/        optional authoring and .cge.md work

validation/
└── cam/                 CAMCGE replication and validation utilities
```

Pre-v0.8 module paths are documented in `docs/migration-v0.8.md` and remain
recoverable from earlier Git tags rather than being duplicated as executable
redirect modules in the current package.

---

## Validation and scientific safeguards

CGE-Core treats validation as part of the model implementation.

The repository includes checks for:

- balanced, square, finite SAM inputs;
- complete and structurally compatible model datasets;
- valid goods/factor/institution partitions;
- model-owned closure information;
- zero degrees of freedom after closure;
- isolated scenario state;
- preservation of solved benchmarks;
- solver optimality and termination;
- immutable numerical result snapshots;
- model-specific replication targets;
- published CAMCGE benchmark levels and policy experiments;
- IFPRI synthetic/public validation and separate official-source evidence;
- executable notebook regression tests;
- wheel/package-content boundaries.

The current release is designed so that changes to software architecture do not
silently become changes to economic equations.

See:

- [`docs/validation.md`](docs/validation.md)
- [`docs/GAMS_STDCGE_VALIDATION.md`](docs/GAMS_STDCGE_VALIDATION.md)
- [`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md)
- [`docs/IFPRI.md`](docs/IFPRI.md)

---

## Advanced API

Most users should begin with:

```python
from cge_core import SimpleCGE, StandardCGE, CamCGE, IFPRICGE
```

The lower-level lifecycle remains intentionally available for advanced
inspection, validation, and engine-level work:

```python
from cge_core import CGE, PyCGE, example_data
```

This is a supported lower-level API, not a preserved historical namespace.
Obsolete module paths from earlier releases were removed in v0.8.0; see
[`docs/migration-v0.8.md`](docs/migration-v0.8.md).

---

## Scientific scope of v0.8.0

v0.8.0 is an architecture-consolidation release. It keeps the validated model
implementations and practitioner workflow while removing obsolete redirect
namespaces, re-homing the inherited PyCGE engine, and making the notebook
course and source tree unambiguous.

It does **not** use those software changes as justification for silently
changing validated economic equations.

Hosoe, CAMCGE, and IFPRI retain their own model-specific equations, calibration
logic, closures, provenance, and validation evidence.

---

## Provenance

CGE-Core is a corrected and extended fork of
[PyCGE](https://github.com/juanfung/pycge), originally developed by Juan Fung
and Charley Burtwistle of the U.S. National Institute of Standards and
Technology.

The original PyCGE code is a U.S. Government work and is public domain under
17 U.S.C. 105; the original notice is retained in
[`LICENSE_NIST.txt`](LICENSE_NIST.txt).

The underlying economic models also retain their original intellectual
provenance:

- Hosoe, Gasawa & Hashimoto for the Simple and Standard textbook models;
- Condon, Dahl & Devarajan for CAMCGE;
- the IFPRI Standard CGE tradition for the IFPRI implementation.

CGE-Core's contribution is the Python framework, corrected workflow,
validation infrastructure, model integration, practitioner API, SAM tooling,
replication machinery, notebooks, documentation, tests, and related
extensions—not authorship of the underlying published model specifications.

---

## Citation

If you use CGE-Core, cite the software and the relevant underlying model
sources.

```bibtex
@software{miraflor2026cgecore,
  author  = {James Matthew Miraflor},
  title   = {{CGE-Core}: an open-source Python framework for computable general equilibrium modelling},
  year    = {2026},
  version = {0.8.0},
  url     = {https://github.com/miraflor/CGE-core}
}
```

Machine-readable citation metadata is available in
[`CITATION.cff`](CITATION.cff).

When applicable, also cite the corresponding model source:

- Hosoe, N., Gasawa, K. & Hashimoto, H. (2010), *Textbook of Computable
  General Equilibrium Modelling: Programming and Simulations*;
- Condon, T., Dahl, H. & Devarajan, S. (1987), *Implementing a Computable
  General Equilibrium Model on GAMS: The Cameroon Model*;
- the relevant IFPRI Standard CGE documentation/source;
- PyCGE/NIST for inherited PyCGE code.

---

## License

CGE-Core modifications are released under the MIT License.

See:

- [`LICENSE`](LICENSE)
- [`LICENSE_NIST.txt`](LICENSE_NIST.txt)
- [`CITATION.cff`](CITATION.cff)

CGE-Core is maintained by **James Matthew Miraflor**.
