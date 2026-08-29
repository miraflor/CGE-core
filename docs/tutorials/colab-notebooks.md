# Colab notebooks

The canonical v0.7.0 course contains seven notebooks.

| Notebook | Purpose |
| --- | --- |
| `01_first_cge.ipynb` | Solve a benchmark and read model output |
| `02_policy_experiments.ipynb` | Create and compare counterfactuals |
| `03_your_own_sam.ipynb` | Inspect and load a SAM |
| `04_camcge.ipynb` | Work with the Cameroon replication |
| `05_ifpri.ipynb` | Use the public synthetic IFPRI path and understand the clean-room boundary |
| `06_build_a_model.ipynb` | Functional Python authoring and experimental `.cge.md` |
| `90_internals.ipynb` | Advanced Pyomo/PyCGE internals |

The first notebook opens directly in Colab from the repository README.

Each canonical notebook uses a single installation cell:

```python
%pip install -q "cge-core[solver] @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
from cge_core import install_solver
install_solver()
```

After that cell, learners work with CGE models rather than Git, repository paths, or solver
executables.

Earlier notebook filenames remain only as compatibility redirects for old links. They are
not a second course.
