# Installation and workflow

## Installation

```bash
pip install cge-core
```

A local NLP solver is required at runtime. Either put an `ipopt`
executable on PATH (`conda install -c conda-forge ipopt`) or install
cyipopt (`pip install "cge-core[solver]"`; needs the IPOPT system
library plus a PyNumero ASL build).

## Quick start

```python
import logging
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

logging.basicConfig(level=logging.INFO)      # see the engine's progress

cge = PyCGE(StdModelDef())
cge.model_data(example_data('stdcge'))

cge.model_instance('pf', 'LAB')              # fix numeraire: pf_LAB = 1
cge.model_drop_redundant('eqpf', 'LAB')      # Walras' law -> square system
cge.model_calibrate()                        # solve baseline (reproduces SAM)

cge.model_sim()                              # clone baseline -> sim
cge.model_modify_sim('taum', 'BRD', 0)       # reform: abolish bread tariff
cge.model_solve()                            # solve counterfactual

frame = cge.model_compare()                  # pandas DataFrame, sim vs base
frame.attrs['objective']                     # utility: base, sim, difference
```

## The engine's contract

The workflow is a state machine:

```
model_data -> model_instance -> model_drop_redundant
    -> model_calibrate -> model_sim -> model_modify_sim
    -> model_solve -> model_compare / model_postprocess
```

Calling methods out of order raises a typed exception whose message
names the method to call first:

| Exception             | Meaning                                          |
| --------------------- | ------------------------------------------------ |
| `WorkflowError`       | Methods called out of order                      |
| `ComponentError`      | Unknown/ineligible component, index, or undo     |
| `DataValidationError` | Bad input data (unbalanced SAM, missing dir, …)  |
| `SolveError`          | Solver did not reach an acceptable optimum       |

Progress messages go through the standard `logging` module on the
`cge_core` logger; nothing is printed except displays you explicitly
request (`model_compare('print')`, `model_postprocess(..., 'print')`).

All comparison differences are **sim minus base**, including the
objective, and percentages are percentage changes. Passing a directory
path to `model_compare` writes `compared.csv` there.

## Why one equation must be dropped

A CGE is a square system: after fixing one price as numeraire, the
number of independent equilibrium conditions equals the number of free
variables. But Walras' law makes one market-clearing equation redundant
— once every other market clears, the last clears automatically. With
every market-clearing equation retained, the assembled system is
over-determined by exactly one equation, and IPOPT aborts with "too few
degrees of freedom". `model_drop_redundant` deactivates exactly one
market-clearing equation, transactionally: the change is rolled back
unless it leaves exactly zero degrees of freedom. The test suite
asserts the dropped market still clears at the solution. See
{doc}`MODEL` for the full accounting.

## Loading your own SAM

`cge_core.samtools` turns a single SAM CSV into a data directory, and
the `accounts=` mapping on the model definitions relabels the
institutional accounts the equations read:

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

The goods set is derived from the SAM itself: every account that is
neither a named factor nor a named institution is a good. The SAM is
validated (square, unique labels, finite cells, balanced per account), and
the generated goods/factor/full-account sets are cross-checked against it
before anything is written. A balanced SAM with the standard model's
account *structure* — activities, factors, one household, government,
indirect-tax and tariff rows, investment, rest of world — loads this
way without editing model code, provided benchmark flows used in
ratios and CES/CET or Cobb-Douglas calibration satisfy the reference
model's nonzero/positivity assumptions. The test suite verifies that a
fully relabelled SAM calibrates to the identical equilibrium.

## Reform shocks and undo

`model_modify_sim(name, index, value)` changes a mutable parameter or
fixes a variable; the original value and fixed-status are recorded, so
`model_modify_sim(name, index, 0, undo=True)` reliably restores the
first value even after repeated edits. The SAM and every benchmark-only
`*0` parameter are protected on both BASE and SIM: changing them either
leaves calibrated parameters stale or creates a silent no-op shock.
Factor endowments are protected on the baseline but remain valid SIM
shocks. Change benchmark data in the input CSVs and rebuild instead.
