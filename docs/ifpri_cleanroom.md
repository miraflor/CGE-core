# IFPRI public path and clean-room boundary

CGE-Core keeps two IFPRI evidence lanes deliberately separate.

## 1. Redistributable public lane

The package includes an **independently authored synthetic IFPRI-format economy**. It is used for:

- public CI;
- wheel/package smoke tests;
- Colab and tutorials;
- exercising calibration, closure, policy-scenario, reporting, and solver paths;
- verifying that the IFPRI implementation can run without restricted external inputs.

```python
from cge_core import IFPRICGE

base = IFPRICGE.synthetic().solve()
result = base.scenario("TARCUT1").solve()
```

This dataset is not the official IFPRI benchmark.

## 2. Official-source replication lane

The official benchmark comparison requires separately obtained source material. CGE-Core does not redistribute that source package or `test.dat`.

Users who possess the required source material can use the advanced `cge_core.ifpri` official-source path. External-data tests remain marked separately from public synthetic tests.

## What may be claimed

A successful synthetic run demonstrates that the **public software path works on the redistributable synthetic economy**. It does not by itself prove equality with the official IFPRI benchmark.

The official replication claim rests on the separately executed official-source comparison and its retained validation targets. Documentation and tests should never collapse those two statements into one.
