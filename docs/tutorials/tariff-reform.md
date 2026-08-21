# Tutorial: Remove an Import Tariff

This is the smallest complete policy experiment in CGE-Core.

## 1. Calibrate the base

```python
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

cge = PyCGE(StdModelDef())
cge.model_data(example_data("stdcge"))
cge.model_instance("pf", "LAB")
cge.model_drop_redundant("eqpf", "LAB")
cge.model_calibrate()
```

## 2. Create the simulation

```python
cge.model_sim()
```

## 3. Remove the bread tariff

```python
cge.model_modify_sim("taum", "BRD", 0)
```

## 4. Solve

```python
cge.model_solve()
```

## 5. Compare with the base

```python
frame = cge.model_compare()
print(frame)
```

The tariff shock changes one parameter, but the counterfactual solution changes every endogenous variable required to restore general equilibrium.

To remove both benchmark import tariffs:

```python
cge.model_modify_sim("taum", "BRD", 0)
cge.model_modify_sim("taum", "MLK", 0)
cge.model_solve()
```
