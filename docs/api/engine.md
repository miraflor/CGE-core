# Advanced PyCGE API

`PyCGE` is the retained lower-level engine for advanced inspection, debugging,
validation, and engine-level work. v0.8 re-homes the implementation under the
private module `cge_core._pycge` while keeping the intentional public import:

```python
from cge_core import PyCGE
```

```{eval-rst}
.. autoclass:: cge_core._pycge.PyCGE
   :members:
   :show-inheritance:
```

## Exceptions

```{eval-rst}
.. autoclass:: cge_core._pycge.CGEError
   :show-inheritance:

.. autoclass:: cge_core._pycge.WorkflowError
   :show-inheritance:

.. autoclass:: cge_core._pycge.ComponentError
   :show-inheritance:

.. autoclass:: cge_core._pycge.DataValidationError
   :show-inheritance:

.. autoclass:: cge_core._pycge.SolveError
   :show-inheritance:
```
