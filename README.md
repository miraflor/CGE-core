# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb)

**CGE-Core 0.7.0 is a practitioner-first computable general equilibrium toolkit: you specify the economics; CGE-Core hides routine solver and framework plumbing.**

The validated Hosoe, CAMCGE, and IFPRI implementations remain distinct model families. v0.7.0 adds a common high-level lifecycle around them without pretending that they share one universal equation system.

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

No Git checkout, repository-root change, `sys.path` edit, PATH injection, solver installation step, solver executable lookup, numeraire choice, or Walras-equation bookkeeping appears in the ordinary modelling workflow.

## Explore without installing

- **[CGE-Core Control Room](https://miraflor.github.io/CGE-core/control-room/)** — choose a bundled model, inspect its economics, configure a policy experiment, and generate runnable v0.7.0 Python.
- **[Open the notebook course](https://miraflor.github.io/CGE-core/tutorials/colab-notebooks.html)** — all seven notebooks have direct documentation and Colab links.
- **[Open the first notebook in Colab](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb)** — one package-install cell, then modelling code.
- **[Read the documentation](https://miraflor.github.io/CGE-core/)** — practitioner tutorials, model guide, SAM workflow, clean-room boundary, validation, and internals.

## Install

Install the **release wheel**, not the repository source archive:

```bash
pip install "https://github.com/miraflor/CGE-core/releases/download/v0.7.0/cge_core-0.7.0-py3-none-any.whl"
```

The wheel contains the installed CGE-Core runtime packages and required model data. The repository's documentation, notebooks, tests, GitHub workflows, and developer files stay in the source repository rather than being fetched as the CGE-Core package itself.

Runtime dependencies such as Pyomo and solver support are still resolved separately by pip.

Then model:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

CGE-Core uses an existing supported NLP backend when one is available. Otherwise the normal `.solve()` path prepares the default open-source backend internally. Advanced users can request a particular backend explicitly with, for example, `.solve(solver="ipopt")`.

## Four model families

| Entry point | Economic role | Ordinary start |
|---|---|---|
| `SimpleCGE` | Hosoe closed-economy teaching model | `SimpleCGE.example().solve()` |
| `StandardCGE` | Hosoe open economy with intermediates, government, trade and investment | `StandardCGE.example().solve()` |
| `CamCGE` | Published Cameroon 1987 replication model | `CamCGE.example().solve()` |
| `IFPRICGE` | IFPRI Standard CGE implementation and scenarios | `IFPRICGE.synthetic().solve()` |

The common surface is a lifecycle, not an equation template. Each model keeps its own closure, variables, calibration logic, and validation targets.

## Policy experiments

`StandardCGE` exposes model-specific economic helpers:

```python
base = StandardCGE.example().solve()

policy = base.scenario("Policy")
policy.tariff("BRD", change=-0.50)       # reduce the existing rate by 50%
policy.production_tax("MLK", 0.05)      # set the rate to 5%
policy.endowment("CAP", change=0.10)    # raise capital endowment by 10%

result = policy.solve()
result.compare(base)
```

For an advanced component that has no semantic helper:

```python
policy.set("taum", "BRD", 0.0)
```

## Bring your own SAM

A balanced SAM using the canonical Hosoe account labels can be passed directly:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

For country-specific labels, state the economic roles explicitly rather than relying on spelling guesses:

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

`from_sam()` validates the accounting table and creates the internal model data representation. It does not claim that every balanced SAM is automatically compatible with the Hosoe specification; the model's calibration assumptions still apply.

## IFPRI clean-room boundary

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()
reform = base.scenario("TARCUT1").solve()
reform.compare(base)
```

The installed synthetic IFPRI-format economy is **independently authored and redistributable**. It exists so the public package, CI, notebooks, and tutorials can exercise the IFPRI implementation without redistributing the official IFPRI source package or `test.dat`.

The synthetic economy is not the official benchmark. Official-source replication remains a separate evidence lane for users who possess the required external source material. See `docs/ifpri_cleanroom.md` and `docs/validation.md`.

## CAMCGE

```python
from cge_core import CamCGE

base = CamCGE.example().solve()
windfall = base.scenario("Oil windfall")
windfall.set("fsav", None, 500)
result = windfall.solve()
```

CAMCGE remains a model-specific historical replication with its own savings-driven closure and published validation targets. v0.7.0 makes it a first-class installed model; it does not rewrite its economics into the Hosoe structure.

## Build a model

CGE-Core 0.7.0 has two extension paths.

A functional Python model needs ordinary functions rather than framework inheritance:

```python
def build_model(data):
    ...
    return model


def apply_default_closure(model):
    ...

benchmark_only = {"SAM0"}
shockable = {"tax", "endowment"}
```

The experimental `.cge.md` format keeps prose inert and executes only fenced `cge` blocks. It is intentionally limited and is **not** used to rewrite the validated bundled models.

## Notebook course

The canonical v0.7.0 sequence is:

| # | Notebook | What you will do | Open in Colab |
|---:|---|---|---|
| 01 | [`01_first_cge.ipynb`](notebooks/01_first_cge.ipynb) | Solve and read an economy | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb) |
| 02 | [`02_policy_experiments.ipynb`](notebooks/02_policy_experiments.ipynb) | Benchmark → shock → counterfactual → comparison | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/02_policy_experiments.ipynb) |
| 03 | [`03_your_own_sam.ipynb`](notebooks/03_your_own_sam.ipynb) | Inspect and load a SAM | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/03_your_own_sam.ipynb) |
| 04 | [`04_camcge.ipynb`](notebooks/04_camcge.ipynb) | Published replication model | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/04_camcge.ipynb) |
| 05 | [`05_ifpri.ipynb`](notebooks/05_ifpri.ipynb) | Synthetic public path and clean-room boundary | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/05_ifpri.ipynb) |
| 06 | [`06_build_a_model.ipynb`](notebooks/06_build_a_model.ipynb) | Functional Python and `.cge.md` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/06_build_a_model.ipynb) |
| 90 | [`90_internals.ipynb`](notebooks/90_internals.ipynb) | Pyomo and `PyCGE` for advanced users | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/90_internals.ipynb) |

**[View the full notebook course →](https://miraflor.github.io/CGE-core/tutorials/colab-notebooks.html)**

Legacy notebook filenames from earlier releases are retained only as tiny redirect notebooks so old links do not break. They contain no Git/PATH/bootstrap machinery and are not part of the v0.7.0 learning path.

## Advanced / lower-level compatibility

The lower-level v0.6 lifecycle remains available:

```python
from cge_core import CGE, PyCGE, example_data
from cge_core.models import StdCGE
```

Use it when you genuinely need engine-level inspection. New practitioner-facing material should use `SimpleCGE`, `StandardCGE`, `CamCGE`, or `IFPRICGE`.

## Scientific scope

v0.7.0 is primarily an architecture, packaging, and usability release. It does **not** use a prettier software interface as justification for silently changing validated economic equations. Hosoe, CAMCGE, and IFPRI retain model-specific validation evidence and provenance boundaries.

See:

- `docs/validation.md`
- `CAMCGE_VALIDATION_REPORT.md`
- `docs/IFPRI.md`
- `docs/GAMS_STDCGE_VALIDATION.md`

## Citation, provenance, and license

CGE-Core is maintained by James Matthew Miraflor. The inherited PyCGE code, underlying model specifications, reference implementations, and source materials retain their original authorship and licensing/provenance. See `CITATION.cff`, `LICENSE`, and `LICENSE_NIST.txt`.
