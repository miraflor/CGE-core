# Install

## Local Python

Install the v0.7.0 release directly from GitHub:

```bash
pip install "cge-core @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
```

Then use the model:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

That is the normal setup. CGE-Core uses an existing supported nonlinear solver when one is available and otherwise prepares its default open-source backend internally on first use.

## Google Colab

Every canonical notebook has one installation cell:

```python
%pip install -q "cge-core @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
```

The next cell is modelling code.

There is no Git clone/fetch/reset logic, repository `chdir`, `sys.path` manipulation, PATH injection, solver-installation call, solver-name selection, numeraire choice, or Walras-equation bookkeeping in the beginner workflow.

## Advanced solver choice

Most users should ignore this section. For reproducibility or solver-specific work:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

`cge doctor` reports the solver backends visible to CGE-Core.
