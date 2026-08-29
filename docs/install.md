# Install

## Package

```bash
pip install cge-core
```

CGE-Core supports Python 3.9+ and uses Pyomo as the algebraic modelling backend.

## Numerical solver

CGE models in this release require a nonlinear-programming backend such as IPOPT. CGE-Core centralizes **selection**, so ordinary scripts simply call `.solve()`.

Check what CGE-Core can see:

```bash
cge doctor
```

For a one-time CGE-Core-managed setup of the open-source IPOPT backend:

```bash
pip install "cge-core[solver]"
cge install-solver
```

`cge install-solver` installs the optional open-source COIN/Ipopt module and keeps its path handling inside CGE-Core. If you already manage IPOPT or cyipopt yourself, CGE-Core uses that installation instead.

## Colab

A public notebook should have at most one installation cell:

```python
%pip install -q "cge-core[solver]==0.7.0"
from cge_core import install_solver
install_solver()
```

The notebook itself should not contain Git branch management, repository checkout logic, `sys.path` changes, PATH injection, or solver-selection code. The helper performs solver-module setup once; no Git, PATH, executable discovery, or solver name appears in the modelling cells.
