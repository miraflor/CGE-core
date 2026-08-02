# CGE-Core

[![tests](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml/badge.svg)](https://github.com/miraflor/CGE-core/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A Pyomo-based Computable General Equilibrium framework faithful to the textbook
by Hosoe, Gasawa & Hashimoto (2010). Named to align with the Policy Simulation
Library convention (cf. [OG-Core](https://github.com/PSLmodels/OG-Core)).

> **Note.** This is an independent project. It is *not* affiliated with or
> endorsed by the [Policy Simulation Library](https://pslmodels.org/); it
> merely follows the `*-Core` naming pattern.

---

## Provenance and license

CGE-Core is a corrected fork of [PyCGE](https://github.com/juanfung/pycge) by
Juan Fung and Charley Burtwistle (U.S. National Institute of Standards and
Technology). The original PyCGE is a work of the U.S. federal government and is
in the **public domain** under [17 U.S.C. 105](https://www.law.cornell.edu/uscode/text/17/105);
the original NIST notice is preserved in `LICENSE_NIST.txt`.

Modifications in this fork — the Walras'-law degree-of-freedom fix, bug fixes,
the engine API, and the test suite — are released under the MIT License
(`LICENSE`).

### Authorship

This fork is maintained by **James Matthew Miraflor**, who produced its
revisions through an AI-assisted ("vibecoded") workflow that he directed and
reviewed. **The underlying model port is not his original work** — it is by
Charley Burtwistle and Juan Fung (NIST, 2017), and the model itself is Hosoe,
Gasawa & Hashimoto's (2010). Every fork modification is validated against the
GAMS Model Library reference implementations by the regression test suite;
machine-readable citation metadata is in `CITATION.cff`.

### Documentation conventions

Model-definition docstrings follow the conventions of
[OG-Core](https://github.com/PSLmodels/OG-Core) (DeBacker & Evans): NumPy-style
docstrings with each relationship stated in a `.. math::` block, cross-
referenced to the GAMS equation names. If you know OG-Core, start with
[`docs/OG_CORE_CROSSWALK.md`](docs/OG_CORE_CROSSWALK.md); the equation-by-
equation mapping to Hosoe is in [`docs/MODEL.md`](docs/MODEL.md).

### Citing

If you use CGE-Core, please cite both the original PyCGE and the Hosoe
textbook:

```bibtex
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

---

## What this is

CGE-Core separates **model definition** (the algebraic structure) from **model
workflow** (calibration, simulation, comparison). The model equations are a
verified 1:1 port of the GAMS Model Library files `splcge.gms` (SEQ=275) and
`stdcge.gms` (SEQ=276). All 24 constraints of the standard model have been
checked equation-by-equation against the GAMS source.

| Model    | Hosoe ch. | Description                                          |
| -------- | --------- | ---------------------------------------------------- |
| `splcge` | 3–4       | Simple closed economy: 2 goods, 2 factors            |
| `stdcge` | 5–6       | Open economy: Armington, CET, government, investment |

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
pip install -e ".[solver,test]"
# build PyNumero's ASL bridge (needs cmake + a C++ compiler)
python -m pyomo.contrib.pynumero.build
```

Then use solver name `'cyipopt'`.

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
- Bundled models reject incomplete data directories, inconsistent goods/factor/account sets, missing configured institutions, and files targeting unknown model components before Pyomo construction begins.
- A solve is marked successful only when Pyomo reports an acceptable optimum; failed solves raise `SolveError`.
- `model_drop_redundant` accepts only model-declared market-clearing candidates, deactivates one equation, and rolls back unless the resulting DOF is exactly zero.
- Scenario shocks preserve the first value and fixed/unfixed state, so `undo=True` is reliable after repeated edits.
- Only price variables can be selected as numeraires; shock values must be finite numeric scalars, failed edits/undo operations roll back completely, and the numeraire cannot be accidentally unfixed.
- Changing the SAM or benchmark-only `*0` inputs in-place is blocked on BASE and SIM; factor endowments remain valid SIM shocks.
- Multidimensional variables are exported as valid long-form CSV. Dill files are for trusted inputs only.


---

## Tests

```bash
pytest tests/ -v
```

86 test functions across five modules (plus parametrized cases):

| Module             | Covers                                                    |
| ------------------ | --------------------------------------------------------- |
| `test_stdcge.py`   | Structure (build, DOF before/after the drop), correctness (base reproduces the SAM, recovery from a perturbed start, the dropped market clears), economics (tariff abolition raises welfare), and that solving the sim leaves the base untouched |
| `test_splcge.py`   | The same structural and correctness properties for the simple model, plus goods-market clearing and zero-profit factor-income exhaustion |
| `test_engine.py`   | Engine workflow and failure-mode regressions: solver termination, state invalidation, safe equation dropping, reversible shocks, CSV export, SAM validation, persistence, and out-of-order guards |
| `test_samtools.py` | Building datasets from a single SAM, deriving goods/factor sets, and calibrating a fully relabelled SAM to the identical equilibrium |
| `test_datasets.py` | Installation-independent access to bundled example datasets |

Solver-dependent tests auto-skip if no local NLP solver is present, so the
suite is still useful without one. CI runs a job with a real IPOPT that
**fails if anything skips**, so the solver path cannot silently rot.

---

## References

- Hosoe, N., Gasawa, K. & Hashimoto, H. (2010). *Textbook of Computable General
  Equilibrium Modelling.* Palgrave Macmillan.
- GAMS Model Library:
  [splcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_splcge.html),
  [stdcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_stdcge.html)
- Original PyCGE: [github.com/juanfung/pycge](https://github.com/juanfung/pycge)
- Naming convention: [github.com/PSLmodels/OG-Core](https://github.com/PSLmodels/OG-Core)
