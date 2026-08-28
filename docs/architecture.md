# Architecture

CGE-Core separates four concerns that are often mixed together in small CGE
implementations:

1. **benchmark data and calibration**;
2. **economic equations**;
3. **counterfactual workflow**; and
4. **numerical result snapshots**.

## Public Hosoe workflow

For the Hosoe simple and standard models, the v0.6 user-facing architecture is:

```text
CGE                     stateless configured blueprint
 │
 └── solve_benchmark(...)
          ↓
     Equilibrium         protected solved benchmark
          │
          ├── scenario("A") ──→ Scenario A ── set(...) ── solve() ──→ Result A
          │
          └── scenario("B") ──→ Scenario B ── set(...) ── solve() ──→ Result B

Result A.compare(Equilibrium)
Result A.compare(Result B)
```

`CGE` owns no solved state. Each benchmark solve creates a fresh validated
`PyCGE` backend. A solved `Equilibrium` owns that benchmark backend plus an
immutable numerical snapshot. Creating a `Scenario` deep-copies the calibrated
backend so multiple counterfactuals can coexist without sharing the legacy
engine's single simulation slot. A successful scenario solve returns an
immutable `Result` snapshot.

The public snapshot contract is intentional: ordinary result inspection should
not require traversing mutable Pyomo objects.

## Underlying PyCGE software architecture

```{mermaid} diagrams/pycge-architecture.mmd
:name: pycge-software-architecture
:alt: PyCGE software architecture showing the data, model definition, workflow engine, solver, benchmark, simulation, and results layers.
```

Use the mouse wheel or a trackpad pinch gesture to **zoom**, drag to **pan**,
or select **⛶** to inspect the diagram in full screen.

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/pycge-architecture.mmd>`

```{literalinclude} /diagrams/pycge-architecture.mmd
:language: text
```
````

The Hosoe façade is additive: it reuses the validated `PyCGE` engine rather
than replacing or rewriting the equations. The economic algebra remains in the
model-definition classes; the lower-level engine manages data loading,
numeraire/redundant-equation handling, calibration, mutable simulation state,
and nonlinear solving.

The IFPRI subsystem is deliberately separate because it is an independently
implemented model family with its own calibration, closure, and scenario
machinery.

CAMCGE remains at repository level as a replication benchmark rather than as
another installed core model.

## The standard model in economic blocks

| Block | Main role |
| --- | --- |
| Production and factors | Firms combine factors and intermediate inputs |
| Household | Factor income finances consumption, saving, and direct taxes |
| Government | Tax revenue finances government demand and saving |
| Investment | Domestic and foreign saving finance investment demand |
| Armington trade | Imports and domestic goods form composite supply |
| CET transformation | Domestic output is allocated between home and export markets |
| Market clearing | Commodity and factor markets balance |
| External balance | Export receipts and foreign saving finance imports |
| Closure | A numeraire and independent equilibrium conditions complete the system |

## Trace economics to implementation

| Economic concept | Theory | Equation reference | Python/API |
| --- | --- | --- | --- |
| Production | {doc}`theory/production` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Final demand | {doc}`theory/final-demand` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Trade | {doc}`theory/trade` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Closure / Walras' law | {doc}`theory/closure` | {doc}`MODEL` | {doc}`api/public` |
| SAM loading | {doc}`theory/sam` | {doc}`workflow` | {doc}`api/samtools` |
| Policy simulation | {doc}`getting-started/first-simulation` | {doc}`workflow` | {doc}`api/public` |
| Advanced engine inspection | {doc}`theory/closure` | {doc}`workflow` | {doc}`api/engine` |

The intended reading path is:

**economic meaning → equation → public workflow → lower-level implementation when needed**.
