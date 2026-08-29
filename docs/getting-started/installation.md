# Installation

## Released v0.7.0 source

Until CGE-Core is distributed through a package index, install the tagged release directly:

```bash
pip install "cge-core[solver] @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
```

Then, once per environment if an NLP solver is not already available:

```bash
cge install-solver
```

Ordinary model code does not name the solver:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

## Google Colab

Use the **Open in Colab** badge in the repository README. The canonical notebooks contain
one installation cell; the rest of the notebook is economics and model use.

## Developer checkout

Contributors working from a local clone can install the checkout in editable mode:

```bash
pip install -e ".[test,docs]"
```

That developer workflow is intentionally separate from the practitioner notebooks.
