# CGE-Core

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
(`LICENSE.txt`).

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

| Model    | Hosoe ch. | Description                                              |
| -------- | --------- | ------------------------------------------------------- |
| `splcge` | 3–4       | Simple closed economy: 2 goods, 2 factors               |
| `stdcge` | 5–6       | Open economy: Armington, CET, government, investment    |

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
git clone https://github.com/jamesmiraflor/CGE-Core.git
cd CGE-Core
pip install -e .
```
Then use solver name `'ipopt'`.

**Option B — cyipopt (pip-only, no conda):**

```bash
# system IPOPT library + headers (Debian/Ubuntu)
sudo apt-get install -y coinor-libipopt-dev
git clone https://github.com/jamesmiraflor/CGE-Core.git
cd CGE-Core
pip install -e ".[solver,test]"
# build PyNumero's ASL bridge (needs cmake + a C++ compiler)
python -m pyomo.contrib.pynumero.build
```
Then use solver name `'cyipopt'`.

---

## Quick start

```python
from pyomo.environ import value
from cge_core.examples.stdcge_model_def import StdModelDef
from cge_core.engine import PyCGE

cge = PyCGE(StdModelDef())
cge.model_data('cge_core/data/stdcge_data_dir')

cge.model_instance('pf', 'LAB')          # fix numeraire (Hosoe: pf_LAB = 1)
cge.model_drop_redundant('eqpf', 'LAB')  # Walras' law -> square system
cge.model_calibrate('cyipopt')           # solve base (reproduces the SAM)

cge.model_sim()                          # clone calibrated base -> sim
cge.model_modify_sim('taum', 'BRD', 0)   # abolish bread tariff
cge.model_modify_sim('taum', 'MLK', 0)   # abolish milk tariff
cge.model_solve('cyipopt')               # solve counterfactual

cge.model_postprocess('compare', 'print')  # base vs sim, % changes
```

Run the bundled experiments directly:

```bash
python -m cge_core.examples.stdcge   # tariff & production-tax abolition
python -m cge_core.examples.splcge   # closed-economy base calibration
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

---

## Tests

```bash
python -m pytest tests/ -v
```

Seven tests check structure (build, DOF before/after the drop), correctness
(base reproduces the SAM, solver recovers from a perturbed start, the dropped
market clears), and economics (tariff abolition raises welfare). Solver-
dependent tests auto-skip if no local NLP solver is present.

---

## References

- Hosoe, N., Gasawa, K. & Hashimoto, H. (2010). *Textbook of Computable General
  Equilibrium Modelling.* Palgrave Macmillan.
- GAMS Model Library:
  [splcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_splcge.html),
  [stdcge.gms](https://www.gams.com/latest/gamslib_ml/libhtml/gamslib_stdcge.html)
- Original PyCGE: [github.com/juanfung/pycge](https://github.com/juanfung/pycge)
- Naming convention: [github.com/PSLmodels/OG-Core](https://github.com/PSLmodels/OG-Core)
