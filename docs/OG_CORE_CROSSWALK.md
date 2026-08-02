# Reading CGE-Core if you know OG-Core

CGE-Core follows the documentation conventions of
[OG-Core](https://github.com/PSLmodels/OG-Core) (DeBacker & Evans) — NumPy
docstrings with `.. math::` blocks, calibrated-parameter transparency, and a
strict separation of *model algebra* from *solution workflow* — but the two
frameworks solve structurally different problems. This note maps one onto the
other so an OG-Core reader can orient in minutes.

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

The deeper difference: OG-Core computes equilibrium by *iterating* on
aggregates until household/firm behavior is consistent with prices; CGE-Core
hands the entire first-order-condition system to an NLP solver at once. That
is why Walras' law appears here as a concrete degrees-of-freedom problem (one
market-clearing equation must be deactivated before IPOPT will solve — see
`docs/MODEL.md`), whereas in OG-Core it is absorbed by the outer-loop
construction.

## File-by-file mapping

| OG-Core role | OG-Core file(s) | CGE-Core file |
| --- | --- | --- |
| Model algebra: firms, households, taxes, aggregates | `firms.py`, `household.py`, `tax.py`, `aggregates.py` | `cge_core/examples/stdcge_model_def.py` (all agents in one simultaneous Pyomo system), `splcge_model_def.py` (pedagogical closed economy) |
| Parameters / calibration | `parameters.py` (`Specifications`), `default_parameters.json` | The `Param` declarations inside the model definitions: benchmark `*0` magnitudes read off the SAM, then share/scale parameters recovered so the base year is reproduced exactly (see "Calibration" in `docs/MODEL.md`) |
| Solving | `SS.py`, `TPI.py`, `execute.py` | `cge_core/engine.py` (`PyCGE.model_calibrate` = solve baseline; `PyCGE.model_solve` = solve counterfactual) |
| Reform specification | Reform dictionaries passed to `Specifications.update_specifications` | `PyCGE.model_modify_sim(name, index, value)` — e.g. set a tariff rate `taum` to 0 |
| Output / comparison | `output_tables.py`, `output_plots.py` | `PyCGE.model_compare`, `PyCGE.model_postprocess` (CSV exports, structured records) |
| Utilities | `utils.py` | `cge_core/datasets.py`, `cge_core/examples/_solver.py` |
| Country calibration packages | OG-USA, OG-PHL, ... | Swap the bundled two-good SAM for a country SAM with the same account structure |

## Workflow correspondence

OG-Core:

```python
p = Specifications()                    # parameters
p.update_specifications(reform)         # reform
ss_output = SS.run_SS(p)                # solve
```

CGE-Core:

```python
cge = PyCGE(StdModelDef())              # algebra
cge.model_data(data_dir)                # SAM in, validated
cge.model_instance('pf', 'LAB')         # numeraire: pf_LAB = 1
cge.model_drop_redundant('eqpf', 'LAB') # Walras' law -> square system
cge.model_calibrate(solver)             # baseline (reproduces the SAM)
cge.model_sim()                         # clone baseline
cge.model_modify_sim('taum', 'BRD', 0)  # reform: abolish a tariff
cge.model_solve(solver)                 # counterfactual
cge.model_compare('print')              # baseline vs. reform
```

Two conventions worth flagging because they have no OG-Core analogue:

1. **Numeraire.** All prices are relative; `model_instance('pf', 'LAB')`
   fixes the wage as numeraire, matching Hosoe's `pf.fx("LAB") = 1`.
2. **The dropped equation.** `model_drop_redundant` deactivates exactly one
   market-clearing condition. The test suite asserts the dropped market
   still clears at the solution (Walras' law), which is the model's
   internal-consistency check — loosely analogous to OG-Core's
   resource-constraint checks on `SS` output.

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
(`stdcge.gms`, SEQ=276), so every line can be diffed against the published
reference implementation; `docs/MODEL.md` collects the full equation table.
