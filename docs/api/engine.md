# Advanced PyCGE compatibility API

`PyCGE` is the retained lower-level workflow implementation for advanced
inspection, debugging, validation, and existing code. Its implementation lives
under `cge_core.compat` so it is visibly separate from the normal practitioner
workflow.

Existing imports remain valid:

```python
from cge_core import PyCGE
# older code also remains valid:
from cge_core.engine import PyCGE
```

```{eval-rst}
.. autoclass:: cge_core.compat.pycge.PyCGE
   :members:
   :show-inheritance:
```

## Exceptions

```{eval-rst}
.. autoclass:: cge_core.compat.pycge.CGEError
   :show-inheritance:

.. autoclass:: cge_core.compat.pycge.WorkflowError
   :show-inheritance:

.. autoclass:: cge_core.compat.pycge.ComponentError
   :show-inheritance:

.. autoclass:: cge_core.compat.pycge.DataValidationError
   :show-inheritance:

.. autoclass:: cge_core.compat.pycge.SolveError
   :show-inheritance:
```
