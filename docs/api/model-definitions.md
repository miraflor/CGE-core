# Model Definition API

The model-definition classes contain the economic algebra. The v0.6 public
namespace gives them scientific model names while preserving the validated
underlying implementations.

```python
from cge_core.models import SplCGE, StdCGE
```

They are passed to `CGE(model=..., data=...)`; the public façade then manages
the benchmark/scenario lifecycle through the existing engine-backed model
definition.

## Simple model — `SplCGE`

`SplCGE` is the public alias for the Hosoe simple closed-economy model
definition.

```{eval-rst}
.. autoclass:: cge_core.models.SplCGE
   :members:
   :show-inheritance:
```

## Standard model — `StdCGE`

`StdCGE` is the public alias for the Hosoe standard open-economy model
definition. Its `accounts=` argument remains available for relabelled
institutional accounts when using `samtools`.

```{eval-rst}
.. autoclass:: cge_core.models.StdCGE
   :members:
   :show-inheritance:
```

The historical class names and import locations remain available for existing
code, but examples and new documentation use `cge_core.models`.

## From code back to economics

The implementation above corresponds to the economic blocks documented in:

- {doc}`../theory/production`
- {doc}`../theory/final-demand`
- {doc}`../theory/trade`
- {doc}`../theory/closure`

For the complete equation-name crosswalk to the GAMS reference, see {doc}`../MODEL`.
