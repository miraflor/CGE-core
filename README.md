# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb)

**CGE-Core is an open-source, Pyomo-based framework for computable general
equilibrium (CGE) modelling in Python, built for policy simulation, teaching,
replication, and reproducible research.**

CGE models are useful because policy changes do not stop where they begin. A
tariff, tax, subsidy, productivity change, factor-supply shock, or external
price change can propagate through production, household income, trade,
government accounts, saving and investment, factor markets, relative prices,
and welfare.

CGE-Core provides a common Python workflow for working with several established
CGE model traditions while keeping their economic equations, calibration,
closure assumptions, source material, and validation evidence explicit.

```text
benchmark → scenario → solve → compare
```

> **Independent project.** CGE-Core is not affiliated with or endorsed by the
> Policy Simulation Library. The `*-Core` name follows the broader naming
> convention used by projects such as
> [OG-Core](https://github.com/PSLmodels/OG-Core).

---

## Why CGE-Core?

CGE-Core is intended to make CGE modelling easier to inspect, teach, reproduce,
extend, and use in scientific Python without hiding the economics.

- **Learn from complete models.** Start with small textbook economies and move
  toward richer open-economy and published models in the same programming
  environment.
- **Run policy experiments.** Solve a benchmark, change an exogenous policy or
  assumption, solve the counterfactual equilibrium, and compare the results.
- **Use social accounting matrices.** Bring empirical economy-wide accounting
  data into the same workflow as calibration, simulation, and reporting.
- **Reproduce published models.** Keep benchmark targets, closures, provenance,
  and numerical validation alongside the implementation.
- **Keep model differences visible.** CGE-Core does not pretend that every CGE
  tradition is one universal equation system.
- **Fit into scientific Python.** Models, data preparation, experiments,
  notebooks, tests, documentation, and extensions can live in the same
  ecosystem.

---

## Included model families

| Entry point | Reference / tradition | Role |
|---|---|---|
| `SimpleCGE` | Hosoe, Gasawa & Hashimoto (2010), ch. 3–4 | Small closed-economy model for learning CGE mechanics |
| `StandardCGE` | Hosoe, Gasawa & Hashimoto (2010), ch. 5–6 | Open economy with intermediate inputs, government, Armington/CET trade, saving, and investment |
| `CamCGE` | Condon, Dahl & Devarajan (1987) | Published Cameroon model used for historical replication and policy-experiment validation |
| `IFPRICGE` | Lofgren, Harris & Robinson / IFPRI Standard CGE tradition | Richer CGE implementation with explicit macro closures and recorded policy scenarios |

These are separate economic implementations brought together by a common
project, validation philosophy, and practitioner workflow.

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

The ordinary workflow stays at the modelling level:

1. choose a model;
2. solve the benchmark;
3. create an isolated scenario;
4. apply an economic shock;
5. solve the counterfactual;
6. compare it with the benchmark.

Advanced users can still choose a solver explicitly, inspect Pyomo objects,
work with lower-level APIs, or build custom models.

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

For solver-specific or reproducibility work:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

---

## What a CGE experiment means

A CGE experiment is not a manually imposed change in an endogenous output or
price.

Instead:

```text
benchmark economy
      ↓
change an exogenous policy, endowment, or external assumption
      ↓
solve the complete equilibrium system again
      ↓
counterfactual equilibrium
      ↓
compare with benchmark
```

For example, removing a tariff changes the relevant policy wedge. The model
then determines the resulting changes in imports, domestic production, factor
demand, household income, government revenue, prices, saving, investment, and
welfare according to that model's equations and closure.

---

## Common workflow

### Solve a benchmark

```python
base = StandardCGE.example().solve()
```

### Create a scenario

```python
policy = base.scenario("Policy reform")
```

### Apply shocks

```python
policy.tariff("BRD", change=-0.50)
policy.production_tax("MLK", 0.05)
policy.endowment("CAP", change=0.10)
```

For a model component without a dedicated semantic helper:

```python
policy.set("taum", "BRD", 0.0)
```

### Solve and compare

```python
result = policy.solve()

result.summary()
result.compare(base)
```

The benchmark remains unchanged.

---

## What can be studied?

The exact shocks available depend on the selected model, but CGE-Core supports
work involving changes such as:

- tariffs and trade-policy wedges;
- production and indirect taxes;
- factor endowments;
- productivity and technology assumptions;
- foreign saving and external-balance assumptions;
- world prices;
- exchange-rate and macro-closure choices;
- government saving or direct-tax adjustment; and
- model-specific policy parameters.

The economic interpretation of a shock belongs to the model itself. CGE-Core
does not assume that every model exposes the same variables, closures, or policy
instruments.

---

## Bring your own SAM

A social accounting matrix (SAM) records the circular flow of income and
expenditure across production activities, commodities, factors, households,
government, investment, and the rest of the world.

For a balanced SAM using canonical Hosoe-style account labels:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

For country-specific account labels:

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

A balanced SAM is necessary but not sufficient for a particular CGE
specification. The data must also satisfy the institutional structure,
nonzero-flow requirements, and calibration assumptions of the selected model.

---

## Model notes

### SimpleCGE

`SimpleCGE` is a small closed-economy model useful for learning production,
factor demand, household income, consumption, market clearing, relative prices,
and the benchmark/counterfactual distinction.

```python
from cge_core import SimpleCGE

base = SimpleCGE.example().solve()
```

### StandardCGE

`StandardCGE` extends the structure to include intermediate inputs, government,
indirect taxes, tariffs, imports and exports, Armington composite demand, CET
transformation, saving and investment, and an open-economy external account.

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

### CamCGE

```python
from cge_core import CamCGE

base = CamCGE.example().solve()

windfall = base.scenario("Oil windfall")
windfall.set("fsav", None, 500)

result = windfall.solve()
```

`CamCGE` is based on the published Cameroon model of Condon, Dahl, and
Devarajan (1987). It is included as a historical replication target with
model-specific validation evidence kept separate from the installed runtime
implementation.

See:

- [`CAMCGE_REPLICATION_GUIDE.md`](CAMCGE_REPLICATION_GUIDE.md)
- [`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md)
- [`validation/cam/README.md`](validation/cam/README.md)

### IFPRI Standard CGE

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()

reform = base.scenario("TARCUT1").solve()
reform.compare(base)
```

The IFPRI implementation retains its own dataset schema, algebraic calibration,
macro closures, factor-market treatment, scenario construction, nonlinear
solve path, reporting, and validation machinery.

The public package contains an independently authored, redistributable
synthetic IFPRI-format economy for tests, tutorials, and continuous
integration. It is **not** the official IFPRI benchmark dataset. Official-source
replication remains a separate path for users who possess the required
external material.

See:

- [`docs/IFPRI.md`](docs/IFPRI.md)
- [`docs/ifpri_cleanroom.md`](docs/ifpri_cleanroom.md)
- [`docs/validation.md`](docs/validation.md)

---

## Learn without installing

- **[CGE-Core Control Room](https://miraflor.github.io/CGE-core/control-room/)** —
  inspect models, their economic structure, and policy experiments.
- **[Notebook course](https://miraflor.github.io/CGE-core/tutorials/colab-notebooks.html)** —
  progress from a first solve to SAMs, CAMCGE, IFPRI, model authoring, and
  internals.
- **[Open the first notebook in Colab](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb)**.
- **[Documentation](https://miraflor.github.io/CGE-core/)** —
  theory, models, tutorials, validation, API reference, and developer
  documentation.

The canonical v0.8.0 notebook sequence is:

| # | Notebook | Purpose |
|---:|---|---|
| 01 | [`01_first_cge.ipynb`](notebooks/01_first_cge.ipynb) | Solve and read an economy |
| 02 | [`02_policy_experiments.ipynb`](notebooks/02_policy_experiments.ipynb) | Benchmark → shock → counterfactual → comparison |
| 03 | [`03_your_own_sam.ipynb`](notebooks/03_your_own_sam.ipynb) | Inspect and load a SAM |
| 04 | [`04_camcge.ipynb`](notebooks/04_camcge.ipynb) | Reproduce a published CGE model |
| 05 | [`05_ifpri.ipynb`](notebooks/05_ifpri.ipynb) | IFPRI synthetic public path and clean-room boundary |
| 06 | [`06_build_a_model.ipynb`](notebooks/06_build_a_model.ipynb) | Functional Python and experimental `.cge.md` authoring |
| 90 | [`90_internals.ipynb`](notebooks/90_internals.ipynb) | Pyomo and lower-level CGE-Core internals |

---

## Validation

CGE-Core treats numerical validation and provenance as part of the software.

The bundled families are tested against the relevant benchmark behavior and
source material. Validation code and evidence are kept distinct from ordinary
runtime use so that users can distinguish:

- an implementation used for simulation;
- the source model or published specification it follows; and
- the tests or replication evidence used to check it.

No claim of originality is implied merely because a model is implemented,
reorganized, tested, documented, or exposed through a new API.

---

## Provenance and credit

CGE-Core is a **corrected, maintained, and extended fork of
[PyCGE](https://github.com/juanfung/pycge)** by **Juan Fung and Charley
Burtwistle** of the U.S. National Institute of Standards and Technology (NIST).

The inherited PyCGE code is a work of the U.S. federal government and is in the
public domain under 17 U.S.C. §105. The original NIST notice is preserved in
[`LICENSE_NIST.txt`](LICENSE_NIST.txt).

The economic model families also have their own intellectual sources:

- `SimpleCGE` and `StandardCGE`: Hosoe, Gasawa & Hashimoto (2010);
- `CamCGE`: Condon, Dahl & Devarajan (1987);
- `IFPRICGE`: the IFPRI Standard CGE tradition, including Lofgren, Harris &
  Robinson (2002), together with the separately obtained official source
  material where applicable.

CGE-Core's repository-level work includes corrections, integration,
maintenance, API design, tests, documentation, validation workflows, packaging,
tutorials, and additional implementation work. **Those activities do not
transfer authorship of inherited code or of the underlying published economic
models to the repository maintainer.**

Development of the fork has been substantially AI-assisted. Human maintenance
has included directing changes, reviewing outputs, checking numerical behavior,
curating releases, and deciding project scope. The project therefore uses
**collective project authorship for software citation** rather than presenting
the maintainer as the sole author.

---

## Citation

If you use CGE-Core, cite:

1. **CGE-Core as software**, using the project-level metadata in
   [`CITATION.cff`](CITATION.cff); and
2. **the upstream model/source material relevant to the model you actually
   use**.

The project-level BibTeX form is:

```bibtex
@software{cgecore2026,
  author  = {{CGE-Core contributors}},
  title   = {{CGE-Core}: a practitioner-first computable general equilibrium toolkit},
  year    = {2026},
  version = {0.8.0},
  url     = {https://github.com/miraflor/CGE-core}
}
```

For example:

- using `SimpleCGE` or `StandardCGE` should also cite Hosoe, Gasawa & Hashimoto;
- using `CamCGE` should also cite Condon, Dahl & Devarajan;
- using `IFPRICGE` should also cite the relevant IFPRI Standard CGE
  documentation/source;
- work that relies materially on inherited PyCGE should acknowledge/cite Fung &
  Burtwistle as appropriate.

**James Matthew Miraflor is the project maintainer, not the sole software
author.**

---

## Maintainer

**James Matthew Miraflor**

Maintenance includes release coordination, integration, review, testing,
documentation, and project stewardship. Maintainer status is not presented as a
claim of sole authorship over the inherited software or underlying model
specifications.

Contributions, bug reports, replication checks, documentation improvements, and
model extensions are welcome through GitHub issues and pull requests.

---

## License

CGE-Core contains code with different provenance:

- inherited PyCGE material: public domain as a U.S. federal government work;
- modifications and new repository material: MIT License;
- underlying books, papers, model documentation, datasets, and external source
  packages retain their own copyrights and terms.

See:

- [`LICENSE`](LICENSE)
- [`LICENSE_NIST.txt`](LICENSE_NIST.txt)
- [`CITATION.cff`](CITATION.cff)
