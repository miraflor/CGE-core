# Bundled models

CGE-Core 0.7 uses one lifecycle while preserving distinct model economics.

## SimpleCGE

```python
from cge_core import SimpleCGE
base = SimpleCGE.example().solve()
```

Small Hosoe teaching model. Useful for learning, smoke tests, and future model-spec equivalence work.

## StandardCGE

```python
from cge_core import StandardCGE
base = StandardCGE.example().solve()
```

Open-economy Hosoe standard model with production, intermediate demand, Armington imports, CET exports, household/government/investment demand, factor markets, taxes, and saving-investment closure.

## CamCGE

```python
from cge_core import CamCGE
base = CamCGE.example().solve()
```

The validated Cameroon model is packaged as a first-class installed model. It keeps its own savings-driven closure: `mps` is fixed and `caeq` is the redundant current-account equation. It is not forced into Hosoe's factor-price closure.

## IFPRICGE

```python
from cge_core import IFPRICGE
base = IFPRICGE.synthetic().solve()
```

The installed synthetic economy is a redistributable demonstration of the IFPRI-format code path.

Named model-specific scenarios are available:

```python
result = base.scenario("TARCUT1").solve()
```

The official-source path remains separate because the official benchmark source has its own licensing/provenance boundary.
