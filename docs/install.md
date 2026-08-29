# Install

## Local Python

For the v0.7.0 release directly from GitHub:

```bash
pip install "cge-core[solver] @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
```

CGE-Core uses Pyomo and a nonlinear solver. The package centralizes solver selection so modelling code can simply call `.solve()`.

Check the current environment:

```bash
cge doctor
```

Install or activate the supported open-source IPOPT backend once:

```bash
cge install-solver
```

An existing IPOPT/cyipopt setup is used when available.

## Google Colab

Every canonical notebook uses one installation cell:

```python
%pip install -q "cge-core[solver] @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
from cge_core import install_solver
install_solver()
```

After that there is no Git clone/fetch/reset logic, no repository `chdir`, no `sys.path` manipulation, no PATH injection, and no solver-name plumbing in the modelling cells.
