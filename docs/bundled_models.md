# Choose a bundled model

CGE-Core 0.8.0 gives four model families a similar practitioner workflow while preserving their different economics and, where appropriate, different internal execution paths.

| Model | Best used for | Important boundary |
|---|---|---|
| `SimpleCGE` | learning factor/commodity equilibrium | no government, trade, intermediates |
| `StandardCGE` | static sectoral tax, tariff, world-price and endowment experiments | representative household, static model |
| `CamCGE` | reproduction of the published Cameroon model and its experiments | historical replication, not a generic country template |
| `IFPRICGE` | richer institutions and explicit macro-closure scenarios | public synthetic data and official-source evidence remain separate |

## SimpleCGE

```python
from cge_core import SimpleCGE
base = SimpleCGE.example().solve()
```

## StandardCGE

```python
from cge_core import StandardCGE
base = StandardCGE.example().solve()
```

The Hosoe Standard model includes intermediate inputs, factor demand, a representative household, government, production taxes, tariffs, Armington imports, CET exports, saving and investment.

## CamCGE

```python
from cge_core import CamCGE
base = CamCGE.example().solve()
```

CAMCGE keeps its own savings-driven closure (`mps` fixed, `caeq` redundant). It is not silently converted to the Hosoe closure simply to fit the same façade.

## IFPRICGE

```python
from cge_core import IFPRICGE
base = IFPRICGE.synthetic().solve()
```

Named scenarios include `TARCUT1`, `TARCUT2`, `FSAVINCR`, `PWMINCR`, and `DEVAL`. Their meaning depends on the IFPRI macro closure, so they are intentionally model-specific rather than generic policy toggles. `IFPRICGE` therefore uses IFPRI-specific equilibrium/scenario/result classes rather than the generic `CGE → Equilibrium → Scenario → Result` implementation.
