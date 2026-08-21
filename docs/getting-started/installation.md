# Installation

CGE-Core requires Python, Pyomo, and a local nonlinear-programming solver.

## Recommended: conda + IPOPT

```bash
conda create -n cgecore python=3.11
conda activate cgecore
conda install -c conda-forge ipopt
git clone https://github.com/miraflor/CGE-core.git
cd CGE-core
pip install -e .
```

This installs CGE-Core from the current repository and places the `ipopt` executable on your environment's PATH.

## Alternative: cyipopt

CGE-Core also supports Pyomo's `cyipopt` interface:

```bash
pip install -e ".[solver]"
```

This route requires the IPOPT system library and a working PyNumero ASL build.

## Check the installation

```python
from cge_core import PyCGE, example_data
from cge_core.examples.stdcge_model_def import StdModelDef

print(example_data("stdcge"))
```

If that imports successfully, continue to {doc}`quickstart`.

```{important}
A solver is required at runtime. Installing the Python package alone is not enough to solve a CGE model.
```
