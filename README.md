# CGE-Core

**CGE-Core is an open, reproducible CGE modelling system for people who want to do economics, not manage solver plumbing.**

Version **0.7.0** introduces a practitioner-first interface over the validated CGE-Core model implementations. The scientific model equations remain inspectable Pyomo code; the ordinary workflow becomes small enough to teach, use in a policy office, or put in a notebook without Git/PATH/Pyomo setup machinery.

## Start here

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)

result = reform.solve()
result.summary()
result.compare(base)
```

That is the intended CGE-Core experience. The model already knows its canonical closure. Solver selection is automatic once a supported numerical backend is installed.

## Install

```bash
pip install cge-core
```

CGE-Core uses an NLP solver such as IPOPT. Check your environment with:

```bash
cge doctor
```

For a one-time CGE-Core-managed open-source solver setup:

```bash
pip install "cge-core[solver]"
cge install-solver
```

Or, in Python/Colab, call `install_solver()` once in the installation cell. Existing IPOPT/cyipopt installations remain supported. Solver discovery, module paths, and solver names stay out of normal modelling code.

## Four bundled model families

| Entry point | Purpose | Ordinary start |
|---|---|---|
| `SimpleCGE` | Small Hosoe teaching model | `SimpleCGE.example().solve()` |
| `StandardCGE` | Hosoe standard open-economy CGE | `StandardCGE.example().solve()` |
| `CamCGE` | Published Cameroon CAMCGE benchmark | `CamCGE.example().solve()` |
| `IFPRICGE` | IFPRI Standard CGE family | `IFPRICGE.synthetic().solve()` |

The interfaces share a lifecycle, **not one universal equation template**. Each model owns its economics and closure conventions.

## Bring your own SAM

A SAM using the canonical Hosoe account labels needs only:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

For a real-country SAM, name the economic roles explicitly:

```python
economy = StandardCGE.from_sam(
    "philippines_sam.csv",
    factors=["LAB", "CAP"],
    household="HH",
    government="GOV",
    investment="SAVINV",
    rest_of_world="ROW",
    indirect_tax="IDT",
    tariff="TRF",
)
```

CGE-Core validates balance and creates the internal Pyomo dataset representation for you.

## Policy shocks

`StandardCGE` provides thin economic helpers:

```python
policy = base.scenario("Policy")
policy.tariff("BRD", change=-0.50)       # cut tariff rate by 50%
policy.production_tax("MLK", 0.05)      # set rate to 5%
policy.endowment("CAP", change=0.10)    # raise capital endowment by 10%
result = policy.solve()
```

The advanced generic operation remains available:

```python
policy.set("taum", "BRD", 0.0)
```

Semantic helpers are model-specific mappings, not a universal tax ontology.

## IFPRI: synthetic is not official

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()
reform = base.scenario("TARCUT1").solve()
reform.compare(base)
```

The installed synthetic economy is independently authored and redistributable. It exercises the IFPRI code path; **it is not the official IFPRI benchmark and is not evidence that licensed official-source replication has become redistributable.** Users with the required source material can use `IFPRICGE.from_official_source(...)` and the advanced `cge_core.ifpri` API.

## Build your own model without inheritance

The documented Python authoring path is functional:

```python
def build_model(data):
    ...
    return model


def apply_default_closure(model):
    ...

benchmark_only = {"SAM0"}
shockable = {"tax", "endowment"}
```

Then:

```python
from cge_core.authoring import model_from_module

economy = model_from_module("my_model.py", data=my_data)
base = economy.solve()
```

You do not need to learn a CGE-Core inheritance tree.

## Experimental `.cge.md`

CGE-Core 0.7.0 also ships an **experimental model specification**. Markdown prose documents the economics; only fenced `cge` blocks execute.

````markdown
# Two-good exchange economy

This paragraph is documentation only.

```cge
set goods = [FOOD, MFG]
param alpha[FOOD] = 0.5
param alpha[MFG] = 0.5
param endowment[FOOD] = 60
param endowment[MFG] = 40
var p[i in goods] > 0
var q[i in goods] >= 0

equation demand_food:
    q[FOOD] = alpha[FOOD] * (p[FOOD]*endowment[FOOD] + p[MFG]*endowment[MFG]) / p[FOOD]
equation demand_mfg:
    q[MFG] = alpha[MFG] * (p[FOOD]*endowment[FOOD] + p[MFG]*endowment[MFG]) / p[MFG]
equation market_food:
    q[FOOD] = endowment[FOOD]
equation market_mfg:
    q[MFG] = endowment[MFG]

fix p[FOOD] = 1
drop market_food
shockable endowment
```
````

Validate before solving:

```bash
cge check model.cge.md
cge solve model.cge.md
```

The grammar is intentionally limited and may evolve before 1.0. Prose never changes computation, and no LLM infers missing equations.

## Notebooks

The public sequence is:

1. `01_first_cge.ipynb` — first solve
2. `02_policy_experiments.ipynb` — benchmark → shock → compare
3. `03_your_own_sam.ipynb` — bring a SAM
4. `04_camcge.ipynb` — larger bundled model
5. `05_ifpri.ipynb` — synthetic IFPRI and provenance boundary
6. `06_build_a_model.ipynb` — `.cge.md` and functional Python authoring
7. `90_internals.ipynb` — Pyomo and `PyCGE` for advanced users

Ordinary notebooks contain no `git clone`, branch-reset logic, repository-root `chdir`, `sys.path` manipulation, PATH injection, or solver-discovery code.

## Advanced / lower-level API

The v0.6 `CGE(...)` lifecycle remains supported, and `PyCGE` remains available for engine inspection and existing code:

```python
from cge_core import CGE, PyCGE
from cge_core.models import StdCGE
```

High-level results expose `raw` when direct Pyomo access is genuinely needed.

## Scientific integrity

v0.7.0 is an architectural/usability release. It is designed around a strict rule: **do not rewrite validated economic equations merely to make the software prettier.** StandardCGE, CAMCGE, and IFPRI keep their model-specific implementations and validation evidence. The new public layers alter construction, solver resolution, scenario ownership, packaging, authoring, and documentation around those equations.

See `docs/validation.md` and the retained model-specific validation material for the exact claim boundaries.

## Citation and provenance

CGE-Core is maintained by James Matthew Miraflor. The inherited PyCGE code, underlying Hosoe/IFPRI/CAMCGE model specifications, and source materials retain their own authorship and licensing/provenance. See `CITATION.cff`, `LICENSE`, `LICENSE_NIST.txt`, and the model documentation.

## License

See `LICENSE` and `LICENSE_NIST.txt`.
