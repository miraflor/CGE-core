# Advanced Engine API

`PyCGE` is the supported lower-level workflow engine for the Hosoe-style
models. It remains public for advanced inspection, debugging, validation, and
existing code, but new ordinary user workflows should begin with
{doc}`public`.

The v0.6 façade is additive: `CGE.solve_benchmark()` creates and drives a fresh
`PyCGE` backend, while `Equilibrium.scenario()` isolates counterfactual state
before returning snapshot-oriented public results.

```{eval-rst}
.. autoclass:: cge_core.engine.PyCGE
   :members:
   :show-inheritance:
```

For the explicit engine state machine (`model_data`, `model_instance`,
`model_calibrate`, `model_sim`, and related methods), see {doc}`../workflow`.

## Exceptions

The same typed exceptions remain useful through both the façade and lower-level
engine.

```{eval-rst}
.. autoclass:: cge_core.engine.CGEError
   :show-inheritance:

.. autoclass:: cge_core.engine.WorkflowError
   :show-inheritance:

.. autoclass:: cge_core.engine.ComponentError
   :show-inheritance:

.. autoclass:: cge_core.engine.DataValidationError
   :show-inheritance:

.. autoclass:: cge_core.engine.SolveError
   :show-inheritance:
```
