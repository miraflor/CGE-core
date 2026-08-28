# API Reference

These pages are generated directly from the Python docstrings in CGE-Core.

That means the website reference follows the code: when a public method's
docstring changes, the rendered API documentation changes with it.

## Main interfaces

| Interface | Purpose |
| --- | --- |
| {doc}`public` | Canonical Hosoe workflow: `CGE`, `Equilibrium`, `Scenario`, `Result` |
| {doc}`model-definitions` | Public `SplCGE` and `StdCGE` model-definition imports |
| {doc}`samtools` | Build model datasets from a Social Accounting Matrix |
| {doc}`datasets` | Access bundled example datasets |
| {doc}`ifpri` | Public IFPRI benchmark, scenario and reporting API |
| {doc}`engine` | Advanced/lower-level `PyCGE` engine and typed exceptions |

For a guided workflow rather than function-by-function documentation, begin
with {doc}`../getting-started/quickstart`.

The Hosoe façade and the IFPRI subsystem are intentionally not presented as one
universal backend interface. Their calibration and closure structures differ,
and v0.6 preserves that distinction rather than hiding it behind speculative
abstractions.
