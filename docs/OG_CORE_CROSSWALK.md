# Reading CGE-Core if you know OG-Core

CGE-Core follows several documentation conventions familiar from
[OG-Core](https://github.com/PSLmodels/OG-Core) (DeBacker & Evans), including
calibrated-parameter transparency and a strict separation of *model algebra*
from *solution workflow*. The two frameworks nevertheless solve structurally
different problems. This note maps one onto the other so an OG-Core reader can
orient quickly.

## What kind of model this is

| | OG-Core | CGE-Core |
| --- | --- | --- |
| Model class | Dynamic overlapping-generations, general equilibrium | Static, single-period computable general equilibrium |
| Reference | DeBacker & Evans, *OG-Core* theory docs | Hosoe, Gasawa & Hashimoto (2010), Ch. 3–6 |
| Households | Many age cohorts, lifetime optimization | One representative household, Cobb-Douglas utility |
| Firms | CES production, dynamic capital accumulation | Cobb-Douglas value added + Leontief intermediates; Armington/CET trade |
| Government | Rich tax functions (`tax.py`), debt dynamics | Flat direct tax, production tax, tariff; savings-driven closure |
| Solution | Steady state (`SS.py`) + transition path (`TPI.py`) via fixed-point iteration | One square nonlinear system solved simultaneously by IPOPT |
| Data anchor | Calibrated `Specifications` object | A balanced social accounting matrix (SAM) |

The deeper difference is computational. OG-Core computes equilibrium by
iterating on aggregates until household and firm behavior is consistent with
prices. CGE-Core hands a square simultaneous equilibrium system to a nonlinear
solver. Walras' law therefore appears concretely in the Hosoe models as a
closure requirement: one redundant market-clearing equation is removed and
one price is chosen as numeraire.

## Public workflow mapping

| OG-Core role | OG-Core interface | CGE-Core public interface |
| --- | --- | --- |
| Model specification | `Specifications` plus model modules | `StdCGE` / `SplCGE` model definition passed to `CGE` |
| Benchmark solution | `SS.run_SS(p)` | `CGE.solve_benchmark(...)` |
| Reform specification | `Specifications.update_specifications(...)` | `benchmark.scenario(...)` then `Scenario.set(...)` |
| Counterfactual solution | `SS.run_SS(...)` or transition machinery | `Scenario.solve()` |
| Read outputs | dictionaries / output utilities | `Equilibrium.value(...)`, `Result.value(...)`, `Result.objective` |
| Compare reform with reference | output tables / plots | `Result.compare(benchmark)` |
| Data helpers | `utils.py` and calibration inputs | `cge_core.datasets`, `cge_core.sam` |

## Workflow correspondence

OG-Core:

```python
p = Specifications()
p.update_specifications(reform)
ss_output = SS.run_SS(p)
```

CGE-Core:

```python
from cge_core import CGE
from cge_core.models import StdCGE

model = CGE(model=StdCGE(), data=data_dir)

benchmark = model.solve_benchmark(
    numeraire=("pf", "LAB"),
    redundant=("eqpf", "LAB"),
    solver=solver,
)

scenario = benchmark.scenario("tariff abolition")
scenario.set("taum", "BRD", 0.0)

result = scenario.solve(solver=solver)
comparison = result.compare(benchmark)
```

Two conventions are worth flagging because they have no direct OG-Core
analogue:

1. **Numeraire.** All prices are relative. In the standard Hosoe example,
   `numeraire=("pf", "LAB")` fixes the labor-factor price as the price anchor.
2. **Redundant market equation.** Walras' law makes one market-clearing
   equation redundant. `redundant=("eqpf", "LAB")` tells the Hosoe workflow
   which equation to deactivate so the solved system is square.

The test suite also checks the dropped market after solution as an
internal-consistency test, loosely analogous to resource-constraint checks on
OG-Core output.

## Lower-level implementation

The public lifecycle above is implemented by the supported lower-level
`PyCGE`/Pyomo engine. Advanced users can still work directly with
`cge_core._pycge.PyCGE`, including its explicit benchmark/simulation state
machine. That engine API is documented separately and is not the recommended
interface for ordinary Hosoe-model policy experiments.

This distinction is important: the public facade is the stable scientific
workflow, while the lower-level engine remains available for implementation
inspection, model development, and compatibility.

## Docstring conventions

Every calibration initializer and constraint rule in the model definitions
carries an OG-Core-style docstring:

```python
def eqF_rule(model, h, i):
    r"""Factor demand from cost minimization (stdcge.gms: ``eqF``).

    .. math::
        F_{h,i} = \frac{\beta_{h,i}\, p^{y}_{i}\, Y_{i}}{p^{f}_{h}}

    Args: ...
    Returns: ...
    """
```

The equation label (`eqF`) is the name used in the GAMS Model Library source
(`stdcge.gms`, SEQ=276), so equations can be checked against the published
reference implementation; `docs/MODEL.md` collects the full equation table.
