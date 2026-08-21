# Five-Minute Quick Start

This example solves the standard model, removes one import tariff, and compares the counterfactual with the calibrated base equilibrium.

```python
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

# 1. Define the model and load the bundled benchmark data.
cge = PyCGE(StdModelDef())
cge.model_data(example_data("stdcge"))

# 2. Fix a numeraire and remove one redundant market-clearing equation.
cge.model_instance("pf", "LAB")
cge.model_drop_redundant("eqpf", "LAB")

# 3. Calibrate and solve the benchmark equilibrium.
cge.model_calibrate()

# 4. Clone the benchmark into a simulation.
cge.model_sim()

# 5. Policy shock: abolish the bread import tariff.
cge.model_modify_sim("taum", "BRD", 0)

# 6. Solve the counterfactual.
cge.model_solve()

# 7. Compare simulation and base.
result = cge.model_compare()
print(result)
```

The workflow is:

```text
data
  ↓
model instance
  ↓
base calibration
  ↓
simulation copy
  ↓
policy shock
  ↓
counterfactual solution
  ↓
comparison
```

All differences reported by `model_compare()` are **simulation minus base**.

Next: {doc}`first-simulation`.
