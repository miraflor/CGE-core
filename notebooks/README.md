# CGE-Core notebook course — v0.7.0

The canonical sequence is deliberately small and practitioner-first:

| # | Notebook | Main idea | Colab |
|---:|---|---|---|
| 01 | [Your first CGE](01_first_cge.ipynb) | Solve and read an economy | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb) |
| 02 | [Policy experiments](02_policy_experiments.ipynb) | Benchmark → shock → compare | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/02_policy_experiments.ipynb) |
| 03 | [Your own SAM](03_your_own_sam.ipynb) | Inspect and load a SAM | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/03_your_own_sam.ipynb) |
| 04 | [CAMCGE](04_camcge.ipynb) | Published replication model | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/04_camcge.ipynb) |
| 05 | [IFPRI](05_ifpri.ipynb) | Public synthetic lane and clean-room boundary | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/05_ifpri.ipynb) |
| 06 | [Build a model](06_build_a_model.ipynb) | Functional Python and `.cge.md` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/06_build_a_model.ipynb) |
| 90 | [Internals](90_internals.ipynb) | Pyomo / PyCGE escape hatch | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/90_internals.ipynb) |

Each canonical notebook is self-contained. In Colab there is one compact release-wheel
installation cell; after that the notebook stays at the modelling level. Solver setup is
internal to the normal `.solve()` path.

Legacy notebook filenames from v0.6 and earlier remain as tiny redirect notebooks only. They
are not part of the v0.7.0 course and contain none of the old Git/PATH/bootstrap machinery.
