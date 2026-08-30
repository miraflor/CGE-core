# Install

## Local Python

Install the **v0.8.0 release wheel**:

```bash
pip install "https://github.com/miraflor/CGE-core/releases/download/v0.8.0/cge_core-0.8.0-py3-none-any.whl"
```

The wheel contains the installed CGE-Core runtime packages and required model data. It does
not make pip download the documentation site, notebook course, tests, GitHub workflows, or
other repository-only files as part of CGE-Core itself.

Runtime dependencies such as Pyomo, pandas, and solver support are resolved separately by pip.

Then use the model:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

That is the normal setup. CGE-Core uses an existing supported nonlinear solver when one is
available and otherwise prepares its default open-source backend internally on first use.

## Google Colab

Every canonical notebook has one installation cell:

```python
%pip install -q "https://github.com/miraflor/CGE-core/releases/download/v0.8.0/cge_core-0.8.0-py3-none-any.whl"
```

The next cell is modelling code.

There is no Git clone/fetch/reset logic, repository `chdir`, `sys.path` manipulation, PATH
injection, solver-installation call, solver-name selection, numeraire choice, or
Walras-equation bookkeeping in the beginner workflow.

## Source checkout

The GitHub tag ZIP is a **source archive**, not the normal installation artifact. It contains
the whole repository because it is intended for source browsing and development.

Contributors who intentionally want the source checkout can use:

```bash
pip install -e ".[test,docs]"
```

from a cloned repository.

## Advanced solver choice

Most users should ignore this section. For reproducibility or solver-specific work:

```python
base = StandardCGE.example().solve(solver="ipopt")
```

`cge doctor` reports the solver backends visible to CGE-Core.
