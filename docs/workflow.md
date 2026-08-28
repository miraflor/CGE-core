# Advanced PyCGE engine workflow

```{note}
For ordinary Hosoe-model use in CGE-Core v0.6, start with the public
{doc}`api/public` API. This page documents the lower-level `PyCGE` state
machine retained for advanced inspection, validation, debugging, and existing
code.
```

## Public-to-engine crosswalk

The façade is additive: it drives the validated engine rather than replacing
it.

| Public workflow | Lower-level engine work |
| --- | --- |
| `CGE(model, data)` | stores the model definition and data location |
| `solve_benchmark(...)` | create `PyCGE` → load data → instantiate → fix numeraire → drop redundant equation → calibrate |
| `Equilibrium.scenario(name)` | deep-copy calibrated engine → `model_sim()` |
| `Scenario.set(...)` | validated `model_modify_sim(...)` mutation |
| `Scenario.solve()` | degree-of-freedom precheck → `model_solve()` → immutable snapshot |
| `Result.compare(reference)` | snapshot comparison; no mutable Pyomo traversal required |

The rest of this page documents those lower-level operations directly.

## Installation

For the current source release, install CGE-Core from the repository:

```bash
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e .
```

A local NLP solver is required at runtime. The simplest route is usually to
install an IPOPT executable with conda:

```bash
conda install -c conda-forge ipopt
```

Alternatively, install the optional solver dependencies from the checkout:

```bash
pip install -e ".[solver]"
```

The `cyipopt` route additionally requires the IPOPT system library and a
working PyNumero ASL build.

## Direct PyCGE quick start

```python
import logging
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

logging.basicConfig(level=logging.INFO)

cge = PyCGE(StdModelDef())
cge.model_data(example_data('stdcge'))

cge.model_instance('pf', 'LAB')
cge.model_drop_redundant('eqpf', 'LAB')
cge.model_calibrate()

cge.model_sim()
cge.model_modify_sim('taum', 'BRD', 0)
cge.model_solve()

frame = cge.model_compare()
frame.attrs['objective']
```

## The engine's contract

The lower-level workflow is a state machine:

```text
model_data -> model_instance -> model_drop_redundant
    -> model_calibrate -> model_sim -> model_modify_sim
    -> model_solve -> model_compare / model_postprocess
```

Calling methods out of order raises a typed exception whose message names the
method to call first:

| Exception | Meaning |
| --- | --- |
| `WorkflowError` | Methods called out of order |
| `ComponentError` | Unknown/ineligible component, index, or undo |
| `DataValidationError` | Bad input data (unbalanced SAM, missing directory, etc.) |
| `SolveError` | Solver did not reach an acceptable optimum |

Progress messages go through the standard `logging` module on the
`cge_core` logger; nothing is printed except displays you explicitly request.

Legacy `model_compare()` differences are **simulation minus base**, including
the objective, and percentages are percentage changes. In the v0.6 façade,
`Result.compare(reference)` generalizes the direction explicitly to
**result minus reference**.

## Why one equation must be dropped

A CGE is a square system: after fixing one price as numeraire, the number of
independent equilibrium conditions equals the number of free variables. But
Walras' law makes one market-clearing equation redundant. Once every other
market clears and the agents' budget constraints hold, the last market clears
automatically.

With every market-clearing equation retained, the assembled standard-model
system is over-determined by one scalar equation. `model_drop_redundant`
deactivates one admissible market-clearing condition and checks that the change
leaves exactly zero degrees of freedom. The test suite then verifies that the
dropped market still clears at the solution.

In the public Hosoe façade, these two explicit closure choices are supplied as
`numeraire=(...)` and `redundant=(...)` to `solve_benchmark()`. They are not a
universal closure object for all CGE model families.

See {doc}`MODEL` for the full accounting.

## Loading your own SAM

`cge_core.samtools` turns a single SAM CSV into a data directory, and the
`accounts=` mapping on the standard model definition relabels the institutional
accounts read by the equations:

```python
from cge_core import CGE, samtools
from cge_core.models import StdCGE

accounts = dict(
    hoh='HH',
    gov='GOVT',
    inv='SAV-INV',
    ext='ROW',
    idt='ITAX',
    trf='TARIFF',
)

samtools.build_dataset(
    'my_sam.csv',
    'my_data_dir',
    factors=['CAP', 'LAB'],
    institutions=accounts.values(),
)

model = CGE(
    model=StdCGE(accounts=accounts),
    data='my_data_dir',
)
```

The goods set is derived from the SAM itself: every account that is neither a
named factor nor a named institution is a good. The SAM is validated for
squareness, unique labels, finite cells, and balance by account. The generated
goods, factor, and full-account sets are cross-checked before anything is
written.

A balanced SAM with the standard model's account structure can be loaded
without editing model code, provided benchmark flows used in ratios,
Cobb-Douglas calibration, and CES/CET calibration satisfy the reference
model's nonzero and positivity assumptions.

## Direct engine shocks and undo

`model_modify_sim(name, index, value)` changes a mutable parameter or fixes a
variable. The original value and fixed status are recorded, so an undo request
can restore the first value even after repeated edits.

The SAM and benchmark-only `*0` parameters are protected on BASE and SIM.
Factor endowments are protected on the benchmark but remain valid simulation
shocks. To change benchmark data, edit the input data and recalibrate.

For ordinary v0.6 scenarios, prefer `Scenario.set()` and immutable `Result`
snapshots. The direct undo stack remains a lower-level engine feature rather
than part of the façade contract.
