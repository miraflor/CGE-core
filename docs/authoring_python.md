# Build your own model in Python

CGE-Core does not require model authors to inherit from a framework class.

Create a normal Python module:

```python
from pyomo.environ import ConcreteModel, Constraint, Param, Set, Var

model_name = "MyCGE"
benchmark_only = {"sam0"}
shockable = {"tax", "endowment"}


def build_model(data):
    m = ConcreteModel()
    # declare sets, data, parameters, variables and equations
    return m


def apply_default_closure(model):
    # explicitly fix the numeraire / exogenous closure variables
    # and deactivate the model's redundant equation if applicable
    ...
```

Use it:

```python
from cge_core.experimental.authoring import model_from_module

economy = model_from_module("my_model.py", data=my_data)
base = economy.solve()
scenario = base.scenario("Policy")
scenario.set("tax", "AGR", 0.0)
result = scenario.solve()
```

The author learns **sets, calibration, variables, equations, closure, and shockability**. Classes, inheritance, factories, decorators, and engine state are framework concerns, not modelling prerequisites.

See `examples/custom_python_model/model.py` for a complete tiny equilibrium.


## Shockability declaration

`shockable` is optional. If it is omitted, the adapter remains open for model-author experimentation (subject to immutable-parameter and benchmark-only protections). If it is declared, it is an allow-list. In particular, `shockable = set()` intentionally means that **nothing is shockable**.

For temporary datasets created by `StandardCGE.from_sam()`, the returned economy also supports `close()` and the context-manager protocol when you want deterministic cleanup.
