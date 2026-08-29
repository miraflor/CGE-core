# CGE-Core

**A practitioner-first Python/Pyomo toolkit for computable general equilibrium modelling and reproducible policy simulation.**

CGE-Core keeps the economic model families distinct while giving ordinary users a common
way to work:

**choose an economy → solve the benchmark → create a scenario → apply an economic shock → solve → compare**

## Start here

- <a href="control-room/" target="_blank" rel="noopener"><strong>Interactive Control Room ↗</strong></a>
  — a six-step visual guide to model choice, economic structure, data, closure, policy shocks,
  runnable code, and outputs.
- **{doc}`getting-started/quickstart`** — the shortest complete Standard CGE experiment.
- **{doc}`tutorials/colab-notebooks`** — the browser-based course.
- **{doc}`architecture`** — the public v0.7 architecture and the lower-level PyCGE engine.
- **{doc}`theory/overview`** — the economic structure and interactive Mermaid diagrams.
- **{doc}`validation/overview`** — Hosoe/GAMS, IFPRI, and CAMCGE evidence.
- **{doc}`api/index`** — Python API reference.

## The v0.7 practitioner workflow

```python
from cge_core import StandardCGE

base = StandardCGE.example().solve()

reform = base.scenario("Tariff abolition")
reform.tariff("BRD", 0)

result = reform.solve()
result.summary()
result.compare(base)
```

The ordinary workflow does not ask the modeller to choose a solver name, manipulate `PATH`,
select a numeraire, drop a Walras equation, change directories, or manage repository state.
Those are implementation details rather than policy assumptions.

A scenario is a **new internally consistent equilibrium**, not a spreadsheet-style
recalculation of one changed cell. Prices and quantities adjust together until the model's
equilibrium conditions are satisfied.

## Four bundled model families

| Model | Main use | Public entry point |
| --- | --- | --- |
| **Simple CGE** | Learn general-equilibrium mechanics in a closed economy | `SimpleCGE` |
| **Standard CGE** | Open-economy policy analysis with government, trade and intermediates | `StandardCGE` |
| **IFPRI Standard CGE** | Richer institutions and explicit named macro-closure experiments | `IFPRICGE` |
| **CAMCGE** | Published Cameroon replication and historical validation | `CamCGE` |

The shared surface is a workflow, not a claim that these models have the same equations.

## Advanced compatibility

The v0.6 `CGE → Equilibrium → Scenario → Result` lifecycle and the lower-level `PyCGE`
engine remain available for advanced or downstream code. They are compatibility and
inspection paths; new practitioner material should start with the four model-specific
entry points above.

```{note}
CGE-Core is an independent project. It is not affiliated with or endorsed by the
Policy Simulation Library.
```

For provenance, licensing, and citation metadata, see
[CITATION.cff](https://github.com/miraflor/CGE-core/blob/main/CITATION.cff).
