# Architecture

CGE-Core separates three things that are often mixed together in small CGE
implementations:

1. **benchmark data and calibration**;
2. **economic equations**; and
3. **simulation workflow**.

## PyCGE software architecture

```{mermaid} diagrams/pycge-architecture.mmd
:name: pycge-software-architecture
:alt: PyCGE software architecture showing the data, model definition, workflow engine, solver, baseline, simulation, and results layers.
```

Use the mouse wheel or a trackpad pinch gesture to **zoom**, drag to **pan**,
or select **⛶** to inspect the diagram in full screen.

````{dropdown} Mermaid source
{download}`Download the .mmd source </diagrams/pycge-architecture.mmd>`

```{literalinclude} /diagrams/pycge-architecture.mmd
:language: text
```
````

The Hosoe-style models use `PyCGE` as the workflow engine. The economic
algebra lives in the model-definition classes; the engine manages data
loading, closure, calibration, simulation state, solution, and comparison.

The IFPRI subsystem is deliberately separate because it is an independently
implemented model family with its own calibration, closure, and scenario
machinery.

CAMCGE is kept at repository level as a replication benchmark rather than as
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
| Closure / Walras' law | {doc}`theory/closure` | {doc}`MODEL` | {doc}`api/engine` |
| SAM loading | {doc}`theory/sam` | {doc}`workflow` | {doc}`api/samtools` |
| Policy simulation | {doc}`getting-started/first-simulation` | {doc}`workflow` | {doc}`api/engine` |

The intended reading path is:

**economic meaning → equation → implementation**.
