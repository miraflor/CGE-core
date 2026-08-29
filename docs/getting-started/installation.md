# Installation

## CGE-Core v0.7.0

Install the release wheel:

```bash
pip install "https://github.com/miraflor/CGE-core/releases/download/v0.7.0/cge_core-0.7.0-py3-none-any.whl"
```

Then solve:

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()
```

The normal install fetches the packaged runtime rather than the full GitHub repository.
Dependencies are installed separately by pip as needed.

No separate solver-installation command is part of ordinary setup. CGE-Core uses a supported
backend already present in the environment or prepares its default open-source backend when
`.solve()` first needs one.

## Google Colab

Use the **Open in Colab** links in the notebook course. Each canonical notebook begins with
one wheel-install cell and then moves directly to the CGE model.

## Developer checkout

Contributors working from a local clone can install the checkout in editable mode:

```bash
pip install -e ".[test,docs]"
```

That developer workflow is intentionally separate from the practitioner notebooks.

## Advanced solver override

When a particular numerical backend matters to the experiment:

```python
base = StandardCGE.example().solve(solver="ipopt")
```
