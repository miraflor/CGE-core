# Colab notebooks

The complete v0.8.0 notebook course is available below. Each notebook can be read directly in this documentation site or opened in Google Colab.

```{note}
If you just want to start immediately, open notebook 01 in Colab.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb)
```

## Notebook course

| # | Notebook | What it does | Read here | Run in Colab |
|---:|---|---|---|---|
| 01 | Your first CGE | Solve the bundled Standard CGE benchmark and inspect production, prices, trade, household demand, and closure. | {doc}`Read <../notebooks/01_first_cge>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/01_first_cge.ipynb) |
| 02 | Policy experiments | Follow the core workflow: benchmark → independent scenario → economic shock → new equilibrium → comparison. | {doc}`Read <../notebooks/02_policy_experiments>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/02_policy_experiments.ipynb) |
| 03 | Bring your own SAM | Inspect a social accounting matrix, verify balance, and construct `StandardCGE` from a SAM. | {doc}`Read <../notebooks/03_your_own_sam>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/03_your_own_sam.ipynb) |
| 04 | CAMCGE | Use the published Cameroon 1987 replication as a first-class model and reproduce a counterfactual. | {doc}`Read <../notebooks/04_camcge>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/04_camcge.ipynb) |
| 05 | IFPRI Standard CGE | Run the independently authored synthetic public economy and execute a named IFPRI scenario. | {doc}`Read <../notebooks/05_ifpri>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/05_ifpri.ipynb) |
| 06 | Build a model | Explore functional Python authoring and the experimental deterministic `.cge.md` specification. | {doc}`Read <../notebooks/06_build_a_model>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/06_build_a_model.ipynb) |
| 90 | Internals and advanced access | Inspect the retained Pyomo/PyCGE machinery after learning the practitioner interface. | {doc}`Read <../notebooks/90_internals>` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.8.0/notebooks/90_internals.ipynb) |

## Sequence

The recommended order is:

1. notebook 01 — first equilibrium
2. notebook 02 — policy experiments
3. notebook 03 — your own SAM
4. notebook 04 — CAMCGE
5. notebook 05 — IFPRI Standard CGE
6. notebook 06 — build a model
7. notebook 90 — internals

---

In Colab, each canonical notebook begins with only:

```python
%pip install -q "https://github.com/miraflor/CGE-core/releases/download/v0.8.0/cge_core-0.8.0-py3-none-any.whl"
```

That cell downloads the compact v0.8.0 release wheel rather than the entire GitHub repository. After that, the notebooks stay at the modelling level. Solver discovery and default first-use setup are internal to CGE-Core.

Earlier notebook filenames live in historical Git tags rather than in the active course directory.
