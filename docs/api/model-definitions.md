# Model Definition API

The model-definition classes contain the economic algebra. They return fresh
Pyomo `AbstractModel` objects that are then managed by the `PyCGE` workflow
engine.

## Simple model

```{eval-rst}
.. autoclass:: cge_core.examples.splcge_model_def.SplModelDef
   :members:
   :show-inheritance:
```

## Standard model

```{eval-rst}
.. autoclass:: cge_core.examples.stdcge_model_def.StdModelDef
   :members:
   :show-inheritance:
```

For an economic explanation of these models, see {doc}`../models/overview`.
