# Contributing to CGE-Core

Thank you for considering a contribution. Issues and pull requests are
welcome — bug reports, documentation fixes, new tests, and model
extensions alike.

## Development setup

```bash
git clone https://github.com/miraflor/CGE-core
cd CGE-core
pip install -e ".[dev]"
```

A usable NLP solver is needed for the full numerical test suite.
For local development, `conda install -c conda-forge ipopt` is the most
predictable explicit setup. Without a usable solver, solver-dependent tests
skip and the structural tests still run.

This developer requirement is separate from the ordinary practitioner API:
`StandardCGE.example().solve()` performs the supported default solver setup
internally when needed.

## Running the tests

```bash
pytest tests/ -v
```

CI runs three jobs: structural (py3.9–3.12, no solver), solver (real
IPOPT, fails if anything skips), and packaging (wheel hygiene). Match
that bar locally where you can.

## What a good pull request looks like

- **Behavior changes come with tests.** The bugs this fork exists to fix
  were all silent — plausible numbers, no errors — so every behavioral
  guarantee is pinned by a regression test, and yours should be too.
- **Model changes come with references.** Anything touching the
  equations must cite the corresponding Hosoe chapter and GAMS equation
  name, and update `docs/MODEL.md`.
- **Docstrings follow the OG-Core convention** (NumPy style, `.. math::`
  blocks, Args/Returns); see any rule in
  `cge_core/models/standard/model.py` for the pattern.
- **Changelog entry** under an "Unreleased" heading, in the existing
  style (what was wrong, why it mattered, what changed).

## Provenance and licensing

By contributing you agree your contribution is licensed under the MIT
License. The original PyCGE basis is public-domain NIST work; keep the
attribution headers intact.

## Conduct

See `CODE_OF_CONDUCT.md`.
