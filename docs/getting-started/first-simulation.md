# Your First Policy Simulation

A CGE policy experiment compares two internally consistent equilibria:

1. the **base equilibrium**, calibrated to benchmark data; and
2. the **counterfactual equilibrium**, solved after changing an exogenous parameter or endowment.

Consider the standard model's import tariff parameter, `taum`.

## Base equilibrium

```python
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

cge = PyCGE(StdModelDef())
cge.model_data(example_data("stdcge"))
cge.model_instance("pf", "LAB")
cge.model_drop_redundant("eqpf", "LAB")
cge.model_calibrate()
```

At this point CGE-Core has recovered the model parameters needed to reproduce the benchmark equilibrium.

## Create the counterfactual

```python
cge.model_sim()
cge.model_modify_sim("taum", "BRD", 0)
cge.model_solve()
```

The shock sets the bread import tariff to zero in the simulation while leaving the calibrated base unchanged.

## Compare

```python
comparison = cge.model_compare()

print(comparison)
print(comparison.attrs["objective"])
```

The comparison table lets you inspect how quantities, prices and other model variables changed between equilibria.

## What changed economically?

Removing a tariff directly changes the domestic price wedge on imports. The model then re-solves **all markets simultaneously**: import demand, domestic production, factor demand, household demand, government revenue, saving, investment and trade adjust until a new equilibrium is reached.

That general-equilibrium feedback is the central reason to use a CGE model rather than applying the tariff change to one equation in isolation.

For the trade equations, see {doc}`../theory/trade`. For the full implementation workflow, see {doc}`../workflow`.
