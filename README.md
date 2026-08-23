# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A Pyomo-based Computable General Equilibrium framework validated against
three distinct benchmark families: two Hosoe, Gasawa & Hashimoto (2010)
textbook models, an independently written implementation of the IFPRI Standard
CGE test economy, and a repository-level replication of the published CAMCGE
Cameroon model. Named to align with the Policy Simulation Library convention
(cf. [OG-Core](https://github.com/PSLmodels/OG-Core)).

> **Note.** This is an independent project. It is *not* affiliated with or
> endorsed by the [Policy Simulation Library](https://pslmodels.org/); it
> merely follows the `*-Core` naming pattern.

## Interactive Control Room

**[Launch the CGE-Core Control Room →](https://miraflor.github.io/CGE-core/control-room/)**

Explore CGE-Core visually: compare the model families, inspect closures and
policy shocks, and generate runnable scenario code directly in the browser.
No installation is required.

---

## Provenance and license

CGE-Core is a corrected fork of [PyCGE](https://github.com/juanfung/pycge) by
Juan Fung and Charley Burtwistle (U.S. National Institute of Standards and
Technology). The original PyCGE is a work of the U.S. federal government and is
in the **public domain** under [17 U.S.C. 105](https://www.law.cornell.edu/uscode/text/17/105);
the original NIST notice is preserved in `LICENSE_NIST.txt`.

Modifications in this fork — the Walras'-law degree-of-freedom fix, bug fixes,
the engine API, the clean-room IFPRI implementation, the CAMCGE replication
benchmark, reporting utilities, documentation, and the test suite — are
released under the MIT License (`LICENSE`).

### Authorship

**James Matthew Miraflor**  
Scientific Computing Laboratory  
Department of Computer Science  
University of the Philippines Diliman  
<jbmiraflor@up.edu.ph>

This fork is maintained by **James Matthew Miraflor**, who directed and
reviewed an AI-assisted revision, testing, and documentation process. He is
cited as the author and maintainer of CGE-Core as this revised software
project, not as the original author of PyCGE, the inherited Hosoe model ports,
or the underlying IFPRI and CAMCGE model specifications. Those works retain
their original attribution.

The IFPRI subsystem was independently implemented within this fork from public
mathematical descriptions; the official IFPRI source package and test data
remain external. The repository-level CAMCGE code is a replication benchmark,
not an original economic model. The inherited Hosoe models are
regression-tested against GAMS Model Library references, the IFPRI benchmark
and policy simulations are checked against full-precision external reference
runs, and CAMCGE is checked against its published base equilibrium and three
policy experiments. Machine-readable citation metadata is in `CITATION.cff`.

### Documentation conventions

Model-definition docstrings follow the conventions of
[OG-Core](https://github.com/PSLmodels/OG-Core) (DeBacker & Evans): NumPy-style
docstrings with each relationship stated in a `.. math::` block, cross-
referenced to the GAMS equation names. If you know OG-Core, start with
[`docs/OG_CORE_CROSSWALK.md`](docs/OG_CORE_CROSSWALK.md); the equation-by-
equation mapping to Hosoe is in [`docs/MODEL.md`](docs/MODEL.md). The IFPRI
loader, calibration, closures, scenarios, validation, and reporting workflow
are documented in [`docs/IFPRI.md`](docs/IFPRI.md). The CAMCGE replication
procedure and completed validation are documented in
[`CAMCGE_REPLICATION_GUIDE.md`](CAMCGE_REPLICATION_GUIDE.md) and
[`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md), with execution
instructions in [`cam/README.md`](cam/README.md).

### Citing

If you use CGE-Core, please cite this software and also cite the original
PyCGE and the relevant underlying model sources:

```bibtex
@software{miraflor2026cgecore,
  author  = {James Matthew Miraflor},
  title   = {{CGE-Core}: a Pyomo-based computable general equilibrium framework},
  year    = {2026},
  version = {0.5.0},
  url     = {https://github.com/miraflor/CGE-core}
}

@software{fung2017pycge,
  author      = {Juan Fung and Charley Burtwistle},
  title       = {{PyCGE}: A Python Interface for Solving {CGE} Models},
  year        = {2017},
  url         = {https://github.com/juanfung/pycge},
  institution = {National Institute of Standards and Technology}
}

@book{hosoe2010textbook,
  author    = {Hosoe, Nobuhiro and Gasawa, Kenji and Hashimoto, Hideo},
  title     = {Textbook of Computable General Equilibrium Modelling:
               Programming and Simulations},
  year      = {2010},
  publisher = {Palgrave Macmillan},
  doi       = {10.1057/9780230281653}
}
```

Users of `cge_core.ifpri` should additionally cite the official IFPRI Standard
CGE documentation and source package they obtained separately. Users relying
on the `cam/` replication benchmark should additionally cite Condon, Dahl, and
Devarajan (1987) and the GAMS Model Library `camcge` model.

---

## What this is

CGE-Core separates **model definition** (the algebraic structure) from **model
workflow** (calibration, simulation, comparison). The two inherited textbook
models are verified 1:1 ports of the GAMS Model Library files `splcge.gms`
(SEQ=275) and `stdcge.gms` (SEQ=276). All 24 constraints of the standard model
have been checked equation-by-equation against the GAMS source.

The separate `cge_core.ifpri` subsystem implements the IFPRI Standard CGE test
economy with algebraic calibration, explicit closures, five policy scenarios,
full-precision external validation, and pandas reporting. Its official source
package and `test.dat` are not distributed with CGE-Core.

The repository-level `cam/` benchmark expresses the published CAMCGE Cameroon
model as a CGE-Core model definition. It reproduces 98 published base-
equilibrium variable levels, the objective value, and three published policy
experiments within documented numerical tolerances. It remains outside the
installed `cge_core` package because it is a replication and regression
benchmark rather than an independently authored core subsystem.

| Subsystem        | Reference                     | Description                                          |
| ---------------- | ----------------------------- | ---------------------------------------------------- |
| `splcge`         | Hosoe ch. 3–4                 | Simple closed economy: 2 goods, 2 factors            |
| `stdcge`         | Hosoe ch. 5–6                 | Open economy: Armington, CET, government, investment |
| `cge_core.ifpri` | IFPRI Standard CGE test model | External-data benchmark and five policy simulations  |
| `cam/`           | CAMCGE, Condon et al. (1987)  | Cameroon benchmark and three policy experiments      |

---

## Why a CGE needs one equation dropped (important)

A CGE is a **square system**: after fixing one price as numeraire, the number
of independent equilibrium conditions equals the number of free variables.
But **Walras' law** makes one market-clearing equation redundant — once every
other market clears, the last clears automatically. If all market-clearing
equations are kept, the assembled system is over-determined by exactly one
equation, and a gradient-based NLP solver such as IPOPT aborts with
*"too few degrees of freedom"* (return code -10).

CGE-Core handles this explicitly with `model_drop_redundant`, which deactivates
one market-clearing equation so the system is square (DOF = 0). The dropped
market then clears automatically at the solution — a built-in consistency
check on Walras' law.

The original PyCGE avoided this only by using the NEOS-hosted CONOPT/MINOS
solvers, which absorb the redundancy internally. A local IPOPT workflow does
not, so the step is required here.

---

## Installation

CGE-Core needs Pyomo and **one local NLP solver**. Two options:

**Option A — IPOPT executable (simplest if you use conda):**

```bash
conda install -c conda-forge ipopt
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e .
```

Then use solver name `'ipopt'`.

**Option B — cyipopt (pip-only, no conda):**

```bash
# system IPOPT library + headers (Debian/Ubuntu)
sudo apt-get install -y coinor-libipopt-dev
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e ".[solver,test]"  # installs cyipopt and scipy
# build PyNumero's ASL bridge (needs cmake + a C++ compiler)
python -m pyomo.contrib.pynumero.build
```

Then use solver name `'cyipopt'`.

The `solver` extra includes SciPy because Pyomo's `cyipopt` interface
imports it at runtime.

> The bundled examples detect whichever solver is available, so you do not
> normally need to name one explicitly.

---

## Quick start

```python
from pyomo.environ import value
from cge_core.examples.stdcge_model_def import StdModelDef
from cge_core import PyCGE, example_data

cge = PyCGE(StdModelDef())
cge.model_data(example_data('stdcge'))

cge.model_instance('pf', 'LAB')          # fix numeraire (Hosoe: pf_LAB = 1)
cge.model_drop_redundant('eqpf', 'LAB')  # Walras' law -> square system
cge.model_calibrate()                    # auto-detect ipopt/cyipopt

cge.model_sim()                          # clone calibrated base -> sim
cge.model_modify_sim('taum', 'BRD', 0)   # abolish bread tariff
cge.model_modify_sim('taum', 'MLK', 0)   # abolish milk tariff
cge.model_solve()                        # solve counterfactual

frame = cge.model_compare()              # pandas DataFrame, sim vs base
print(frame.attrs['objective'])          # {'base': ..., 'sim': ..., 'difference': ...}
cge.model_compare('print')               # or print the full table
```

The engine reports progress through the standard `logging` module on the
`cge_core` logger; add `logging.basicConfig(level=logging.INFO)` to see the
classic step-by-step chatter (the bundled examples do this).

Run the bundled experiments directly:

```bash
python -m cge_core.examples.stdcge   # tariff & production-tax abolition
python -m cge_core.examples.splcge   # closed-economy base calibration
```

Both expose a `main()` you can import and call rather than shelling out:

```python
from cge_core.examples.stdcge import main
cge_tariff, cge_tax = main()
```

---

## Workflow

```
ModelDef ──▶ PyCGE ──▶ model_data()
                          │
                    model_instance()        ← fix numeraire
                          │
                  model_drop_redundant()    ← Walras' law (DOF 0)
                          │
                    model_calibrate()       ← solve base
                          │
                      model_sim()           ← clone base ▶ sim
                          │
                   model_modify_sim()       ← apply shocks
                          │
                     model_solve()          ← solve counterfactual
                          │
                  model_postprocess()       ← compare / export
```

Calling these out of order is safe: each method checks its preconditions and
raises a typed exception (`WorkflowError`, `ComponentError`,
`DataValidationError`, `SolveError`) whose message names the method to call
first, rather than raising from deep inside Pyomo.

### Sign conventions

All differences reported by `model_compare` are **sim minus base**, including
the objective. Percentages are percentage *changes*, `(sim - base) / base * 100`.
`model_compare` returns a pandas DataFrame (one row per variable element,
columns `component`, `index_1..N`, `base_value`, `sim_value`, `difference`,
`pct_change`); the objective comparison rides along in
`frame.attrs['objective']`. Passing a directory path writes `compared.csv`.

### Using your own SAM

`cge_core.samtools` turns a single SAM CSV into a directory `model_data` can
load, deriving the goods set from the SAM itself; the `accounts=` mapping on
the model definitions relabels the institutional accounts the equations read:

```python
from cge_core import PyCGE, samtools
from cge_core.examples.stdcge_model_def import StdModelDef

accounts = dict(hoh='HH', gov='GOVT', inv='SAV-INV',
                ext='ROW', idt='ITAX', trf='TARIFF')
samtools.build_dataset('my_sam.csv', 'my_data_dir',
                       factors=['CAP', 'LAB'],
                       institutions=accounts.values())
cge = PyCGE(StdModelDef(accounts=accounts))
cge.model_data('my_data_dir')
```

A balanced SAM with the standard-model account *structure* (activities,
factors, one household, government, indirect-tax and tariff rows, investment,
rest of world) loads this way without editing model code, provided the
benchmark flows used in ratios and CES/CET or Cobb-Douglas calibration satisfy
the reference model's nonzero/positivity assumptions. The test suite verifies
that a fully relabelled SAM calibrates to the identical equilibrium.

### Reliability safeguards

- Input SAMs are checked for square labels, finite numeric cells, and per-account relative balance before model construction.
- Model-specific zero-flow calibration failures are converted to a clear `DataValidationError` rather than leaking a raw division-by-zero exception.
- Bundled models reject incomplete data directories, inconsistent goods/factor/account sets, missing configured institutions, and files targeting unknown model components before Pyomo construction begins.
- A solve is marked successful only when Pyomo reports an acceptable optimum; failed solves raise `SolveError`.
- `model_drop_redundant` accepts only model-declared market-clearing candidates, deactivates one equation, and rolls back unless the resulting DOF is exactly zero.
- Scenario shocks preserve the first value and fixed/unfixed state, so `undo=True` is reliable after repeated edits.
- Only model-declared closure anchors can be fixed through `model_instance`; the Hosoe models declare price numeraires, while CAMCGE declares its published fixed savings-rate closure. Shock values must be finite numeric scalars, failed edits/undo operations roll back completely, and the selected closure anchor cannot be accidentally unfixed.
- Changing the SAM or benchmark-only `*0` inputs in-place is blocked on BASE and SIM; factor endowments remain valid SIM shocks.
- Multidimensional variables are exported as valid long-form CSV. Dill files are for trusted inputs only.

---

## Tests

```bash
pytest tests/ -v
```

The suite covers the following main groups:

| Module or group     | Covers                                                    |
| ------------------- | --------------------------------------------------------- |
| `test_stdcge.py`    | Structure (build, DOF before/after the drop), correctness (base reproduces the SAM, recovery from a perturbed start, the dropped market clears), economics (tariff abolition raises welfare), and that solving the sim leaves the base untouched |
| `test_splcge.py`    | The same structural and correctness properties for the simple model, plus goods-market clearing and zero-profit factor-income exhaustion |
| `test_engine.py`    | Engine workflow and failure-mode regressions: solver termination, state invalidation, safe equation dropping, reversible shocks, CSV export, SAM validation, persistence, and out-of-order guards |
| `test_samtools.py`  | Building datasets from a single SAM, deriving goods/factor sets, and calibrating a fully relabelled SAM to the identical equilibrium |
| `test_datasets.py`  | Installation-independent access to bundled example datasets |
| `tests/ifpri/`      | IFPRI loading, calibration, closures, reporting, and five policy-scenario regressions |
| `tests/cam/`        | CAMCGE data transcription, structure, base equilibrium, and three published policy experiments |

Solver-dependent tests auto-skip if no local NLP solver is present, so the
suite is still useful without one. CI runs a job with a real IPOPT that
**fails if anything skips**, so the solver path cannot silently rot. At the
CAMCGE integration point, the complete local suite passed 180 tests with no
skips or failures; exact results are recorded in
[`CAMCGE_VALIDATION_REPORT.md`](CAMCGE_VALIDATION_REPORT.md).

---

## References

- Hosoe, N., Gasawa, K. & Hashimoto, H. (2010). *Textbook of Computable General
  Equilibrium Modelling.* Palgrave Macmillan.
- GAMS Model Library:
  [splcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_splcge.html),
  [stdcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_stdcge.html)
- Condon, T., Dahl, H. & Devarajan, S. (1987). *Implementing a Computable
  General Equilibrium Model on GAMS: The Cameroon Model.* World Bank
  Development Research Department Discussion Paper DRD290.
- GAMS Model Library: `camcge.gms` (SEQ=81).
- Original PyCGE: [github.com/juanfung/pycge](https://github.com/juanfung/pycge)
- Naming convention: [github.com/PSLmodels/OG-Core](https://github.com/PSLmodels/OG-Core)
