# Colab notebooks

The complete v0.7.0 notebook course is available below. **Each notebook can be read directly in this documentation site or opened in Google Colab.**

## 01 — Your first CGE

Solve the bundled Standard CGE benchmark, inspect production, prices, trade, household demand, and understand the declared closure.

**{doc}`Read the notebook <../notebooks/01_first_cge>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/01_first_cge.ipynb)

## 02 — Policy experiments

Follow the core comparative-static workflow: benchmark → independent scenario → economic shock → new equilibrium → comparison.

**{doc}`Read the notebook <../notebooks/02_policy_experiments>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/02_policy_experiments.ipynb)

## 03 — Bring your own SAM

Inspect a social accounting matrix, verify balance, construct `StandardCGE` from a SAM, and map country-specific institutional labels explicitly.

**{doc}`Read the notebook <../notebooks/03_your_own_sam>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/03_your_own_sam.ipynb)

## 04 — CAMCGE

Use the published Cameroon 1987 replication as a first-class model and reproduce a model-specific counterfactual.

**{doc}`Read the notebook <../notebooks/04_camcge>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/04_camcge.ipynb)

## 05 — IFPRI Standard CGE

Run the independently authored synthetic public economy, execute a named IFPRI scenario, and understand the clean-room boundary between public execution and official-source validation.

**{doc}`Read the notebook <../notebooks/05_ifpri>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/05_ifpri.ipynb)

## 06 — Build a model

Explore functional Python authoring and the experimental deterministic `.cge.md` specification.

**{doc}`Read the notebook <../notebooks/06_build_a_model>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/06_build_a_model.ipynb)

## 90 — Internals and advanced access

Inspect the retained Pyomo/PyCGE machinery after learning the practitioner interface. This notebook is deliberately last.

**{doc}`Read the notebook <../notebooks/90_internals>`** ·
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/miraflor/CGE-core/blob/v0.7.0/notebooks/90_internals.ipynb)

---

In Colab, each canonical notebook begins with only:

```python
%pip install -q "cge-core @ https://github.com/miraflor/CGE-core/archive/refs/tags/v0.7.0.zip"
```

After that, the notebooks stay at the modelling level. Solver discovery and default first-use setup are internal to CGE-Core.

Earlier notebook filenames remain only as compatibility redirects for old links. They are not a second course.
