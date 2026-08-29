# Architecture

CGE-Core v0.7 separates five concerns:

1. **economic model definitions**;
2. **benchmark data and calibration**;
3. **model-owned closure**;
4. **counterfactual workflow**; and
5. **numerical result snapshots**.

The public interface is deliberately smaller than the implementation.

## Practitioner-first public architecture

```{mermaid} diagrams/cge-core-v070-public.mmd
:name: cge-core-v070-public-architecture
:alt: CGE-Core v0.7 architecture showing practitioner model facades, benchmark and scenario workflow, model-specific economics, lower-level compatibility, Pyomo, and the nonlinear solver.
```

Use the mouse wheel or a trackpad pinch gesture to **zoom**, drag to **pan**, or select
**⛶** to inspect the diagram in full screen.

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/cge-core-v070-public.mmd>`

```{literalinclude} /diagrams/cge-core-v070-public.mmd
:language: text
```
````

For ordinary work, the modeller sees:

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

`SimpleCGE`, `StandardCGE`, and `CamCGE` supply their canonical closure automatically.
`IFPRICGE` retains the IFPRI model's own closure and named scenario machinery.

A scenario owns one independent concrete model clone. The benchmark remains protected.
A solved result exposes numerical snapshots for ordinary inspection so that users do not
need to traverse mutable Pyomo objects.

## Underlying PyCGE architecture

The mature lower-level engine remains part of v0.7 and is still useful for implementation,
validation, and compatibility work.

```{mermaid} diagrams/pycge-architecture.mmd
:name: pycge-software-architecture
:alt: PyCGE software architecture showing data, model definition, workflow engine, solver, benchmark, simulation, and results layers.
```

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/pycge-architecture.mmd>`

```{literalinclude} /diagrams/pycge-architecture.mmd
:language: text
```
````

The practitioner façades do **not** rewrite the validated economic algebra. They configure
and call the model-specific implementation while hiding routine framework plumbing.

## Model-family boundaries

| Family | v0.7 role | Closure |
| --- | --- | --- |
| Hosoe Simple | Teaching / closed-economy benchmark | Model-owned canonical closure |
| Hosoe Standard | Generic open-economy policy model | Model-owned canonical closure |
| CAMCGE | First-class installed historical replication | CAMCGE-specific closure |
| IFPRI Standard | Separate richer institutional model | IFPRI-specific closure and named scenarios |

The project therefore shares workflow semantics without pretending there is one universal
CGE equation template.

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
| Closure / Walras' law | {doc}`theory/closure` | {doc}`workflow` | automatic for bundled models |
| SAM loading | {doc}`theory/sam` | {doc}`workflow` | `StandardCGE.from_sam(...)` |
| Policy simulation | {doc}`getting-started/first-simulation` | {doc}`workflow` | benchmark → scenario → result |
| Advanced engine inspection | {doc}`api/engine` | {doc}`workflow` | `.raw` / lower-level API |

The intended reading path is:

**economic meaning → equation → practitioner workflow → lower-level implementation only when needed**.
