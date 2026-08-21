# Architecture

CGE-Core separates **three layers** that are often mixed together in small CGE implementations:

1. benchmark data and calibration;
2. the economic equations; and
3. the simulation workflow.

## System architecture

```{mermaid}
flowchart LR
    SAM[SAM and benchmark data] --> DEF[Model definition]
    DEF --> ENG[PyCGE workflow engine]
    ENG --> SOLVER[IPOPT or cyipopt]
    SOLVER --> BASE[Base equilibrium]

    BASE --> SIM[Simulation copy]
    SHOCK[Policy shock] --> SIM
    SIM --> SOLVER2[IPOPT or cyipopt]
    SOLVER2 --> CF[Counterfactual equilibrium]

    BASE --> CMP[Comparison]
    CF --> CMP

    IFPRI[IFPRI subsystem] --> V[Independent validation]
    CAM[CAMCGE replication] --> V
    BASE --> V
```

The Hosoe-style models use `PyCGE` as the workflow engine. The IFPRI subsystem is deliberately separate because it is an independently implemented model family with its own calibration, closure and scenario machinery. CAMCGE is kept at repository level as a replication benchmark.

## The standard model as economic blocks

```{mermaid}
flowchart TB
    PROD[Production and factors] --> INC[Factor income]
    INC --> HH[Household demand and saving]
    TAX[Taxes] --> GOV[Government demand and saving]
    HH --> DEM[Composite demand]
    GOV --> DEM
    INV[Investment demand] --> DEM

    PROD --> SUP[Domestic output]
    TRADE[Armington imports and CET exports] --> DEM
    SUP --> TRADE

    DEM --> MC[Market clearing]
    TRADE --> BOP[Balance of payments]
    MC --> EQ[General equilibrium]
    BOP --> EQ
```

## Trace a concept from economics to code

| Economic concept | Theory | Equation-level reference | Python/API |
| --- | --- | --- | --- |
| Production | {doc}`theory/production` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Final demand | {doc}`theory/final-demand` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Trade | {doc}`theory/trade` | {doc}`MODEL` | {doc}`api/model-definitions` |
| Closure / Walras' law | {doc}`theory/closure` | {doc}`MODEL` | {doc}`api/engine` |
| SAM loading | {doc}`theory/sam` | {doc}`workflow` | {doc}`api/samtools` |
| Policy simulation | {doc}`getting-started/first-simulation` | {doc}`workflow` | {doc}`api/engine` |

This crosswalk is intentional: the site should let a reader move from **economic meaning → equation → implementation** without having to infer where each piece lives.
