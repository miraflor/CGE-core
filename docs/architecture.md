# Architecture

CGE-Core v0.8 separates six concerns:

1. **economic model definitions**;
2. **benchmark data and calibration**;
3. **model-owned closure and policy metadata**;
4. **counterfactual workflow**;
5. **numerical result interfaces**; and
6. **solver resolution**.

The public interface is deliberately smaller than the implementation. The four bundled
model families present a similar modelling workflow, but v0.8 does **not** force them
through one internal implementation when their economics or validation requirements differ.

## Practitioner-first public architecture

```{mermaid} diagrams/cge-core-v080-public.mmd
:name: cge-core-v080-public-architecture
:alt: CGE-Core v0.8 architecture showing the generic Simple, Standard, and CAMCGE workflow beside the IFPRI-specific workflow, converging on Pyomo and centralized nonlinear-solver resolution.
```

Use the mouse wheel or a trackpad pinch gesture to **zoom**, drag to **pan**, or select
**⛶** to inspect the diagram in full screen.

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/cge-core-v080-public.mmd>`

```{literalinclude} /diagrams/cge-core-v080-public.mmd
:language: text
```
````

For the Hosoe Simple, Hosoe Standard, and CAMCGE families, the modeller sees the generic
scientific lifecycle:

```text
StandardCGE.example()
        │
        └── solve()
              ↓
         Equilibrium
              │
              ├── scenario("A") → tariff/endowment/... → solve() → Result A
              │
              └── scenario("B") → tariff/endowment/... → solve() → Result B

Result A.compare(Equilibrium)
Result A.compare(Result B)
```

`SimpleCGE`, `StandardCGE`, and `CamCGE` configure this lifecycle with their own model
definition and `ModelSpec`. Their canonical closure is therefore model-owned even though
the surrounding workflow is shared.

`IFPRICGE` deliberately follows a parallel path. It exposes the same benchmark → scenario →
solve → inspect idea through `IFPRIEquilibrium`, `IFPRIScenario`, and `IFPRIResult`, while
retaining IFPRI-specific calibration, named policy scenarios, and macro-closure machinery.
It does not pass through the generic `CGE` / `CoreEngine` workflow merely for architectural
symmetry.

For the generic Simple/Standard/CAMCGE path, a scenario owns one independent clone of the
calibrated benchmark. The benchmark remains protected, and solved results expose immutable
numerical snapshots for ordinary inspection. IFPRI provides its own result objects over its
model-specific solved states.

## Generic workflow and the retained PyCGE engine

The generic v0.8 path has three distinct software layers:

1. `CGE → Equilibrium → Scenario → Result` is the **scientific workflow layer**;
2. `CoreEngine` is the **CGE-Core policy adapter**; and
3. `PyCGE` is the retained **lower-level engine mechanics**.

```{mermaid} diagrams/pycge-architecture.mmd
:name: pycge-software-architecture
:alt: CGE-Core v0.8 generic workflow architecture showing model definition and ModelSpec, the workflow layer, CoreEngine over PyCGE, Pyomo, centralized solver resolution, and a supported nonlinear backend.
```

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/pycge-architecture.mmd>`

```{literalinclude} /diagrams/pycge-architecture.mmd
:language: text
```
````

### `ModelSpec`

`ModelSpec` carries model-specific software policy that should not be guessed from component
names: default closure metadata, protected benchmark components, semantic policy shocks, and
required data declarations. Economic equations remain in the model-definition modules.

### `CoreEngine`

`CoreEngine` is intentionally small. It subclasses `PyCGE` and changes the protection policy
so benchmark/base protection comes from `ModelSpec` rather than historical naming rules such
as a trailing `0`.

### `PyCGE`

The retained lower-level engine owns the mature mechanics used by the generic workflow:
instance construction, mutation, undo/rollback, solver execution, and result bookkeeping.
Advanced users can still import it intentionally with:

```python
from cge_core import PyCGE
```

The practitioner façades do **not** rewrite validated economic algebra. They configure and
call the appropriate model-specific implementation while hiding routine framework plumbing.

## Solver boundary

Ordinary code calls `.solve()` rather than managing solver installation or `PATH` state.
`cge_core.solver` resolves a supported nonlinear backend and is shared by the generic and
IFPRI paths. It prefers a usable system Ipopt, then a working `cyipopt`, and otherwise can
prepare the packaged COIN/Ipopt NL route used through Pyomo.

The architecture therefore separates an economic modelling decision from the numerical
backend used to solve it.

## Model-family boundaries

| Family | v0.8 public path | Closure |
| --- | --- | --- |
| Hosoe Simple | Generic `CGE → Equilibrium → Scenario → Result` | Model-owned canonical closure |
| Hosoe Standard | Generic `CGE → Equilibrium → Scenario → Result` | Model-owned canonical closure |
| CAMCGE | Generic `CGE → Equilibrium → Scenario → Result` | CAMCGE-specific closure |
| IFPRI Standard | IFPRI-specific equilibrium/scenario/result adapter | IFPRI-specific closure and named scenarios |

The project therefore shares practitioner semantics without pretending there is one
universal CGE equation template or one mandatory internal workflow.

## Experimental authoring boundary

The optional authoring tools live only under `cge_core.experimental`:

- `cge_core.experimental.authoring` adapts functional Python models; and
- `cge_core.experimental.spec` implements the deterministic `.cge.md` specification.

They are intentionally outside the main bundled-model pipeline. Experimental authoring can
evolve before 1.0 without forcing the validated Hosoe, CAMCGE, or IFPRI implementations to
be rewritten around it.

## The Standard CGE in economic blocks

| Block | Main role |
| --- | --- |
| Production and factors | Firms combine factors and intermediate inputs |
| Household | Factor income finances consumption, saving, and direct taxes |
| Government | Tax revenue finances government demand and saving |
| Investment | Domestic and foreign saving finance investment demand |
| Armington trade | Imports and domestic goods form composite supply |
| CET transformation | Output is allocated between domestic and export markets |
| Market clearing | Commodity and factor markets balance |
| External balance | Export receipts and foreign saving finance imports |
| Closure | A price anchor and independent equilibrium conditions complete the system |

## Trace economics to implementation

| Economic concept | Theory | Detailed equations | Public workflow |
| --- | --- | --- | --- |
| Production | {doc}`theory/production` | {doc}`MODEL` | `StandardCGE.example().solve()` |
| Final demand | {doc}`theory/final-demand` | {doc}`MODEL` | result inspection |
| Trade | {doc}`theory/trade` | {doc}`MODEL` | `scenario.tariff(...)` |
| Closure / Walras' law | {doc}`theory/closure` | {doc}`workflow` | model-owned for bundled models |
| SAM loading | {doc}`theory/sam` | {doc}`workflow` | `StandardCGE.from_sam(...)` |
| Policy simulation | {doc}`getting-started/first-simulation` | {doc}`workflow` | benchmark → scenario → result |
| IFPRI scenarios | {doc}`models/ifpri` | {doc}`IFPRI` | `IFPRICGE.synthetic().solve()` |
| Advanced engine inspection | {doc}`api/engine` | {doc}`workflow` | `.raw` / `PyCGE` |

The intended reading path is:

**economic meaning → equation → practitioner workflow → lower-level implementation only when needed**.
