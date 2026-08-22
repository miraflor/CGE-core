# Architecture

CGE-Core separates three things that are often mixed together in small CGE
implementations:

1. **benchmark data and calibration**;
2. **economic equations**; and
3. **simulation workflow**.

## PyCGE software architecture

```{mermaid}
%%{init: {"theme":"base","themeVariables":{"background":"transparent","primaryColor":"transparent","secondaryColor":"transparent","tertiaryColor":"transparent","primaryTextColor":"currentColor","secondaryTextColor":"currentColor","tertiaryTextColor":"currentColor","primaryBorderColor":"currentColor","secondaryBorderColor":"currentColor","tertiaryBorderColor":"currentColor","lineColor":"currentColor","textColor":"currentColor","clusterBkg":"transparent","clusterBorder":"currentColor","edgeLabelBackground":"transparent"}}}%%
flowchart TB

    USER["User script / notebook"]

    subgraph INPUT["Data layer"]
        SAM["SAM / model CSV files"]
        SAMTOOLS["samtools.build_dataset()"]
        EXAMPLE["example_data()"]
        DATA["Pyomo DataPortal"]
    end

    subgraph DEF["Economic model definition"]
        SPL["SplModelDef"]
        STD["StdModelDef"]
        ABSTRACT["Pyomo AbstractModel<br/>sets · parameters · variables · equations"]
    end

    subgraph ENG["PyCGE workflow engine"]
        LOAD["model_data()"]
        INSTANCE["model_instance()"]
        CLOSURE["Closure<br/>fix numeraire + drop redundant equation"]
        CAL["model_calibrate()"]
        CLONE["model_sim()"]
        SHOCK["model_modify_sim()"]
        SOLVE["model_solve()"]
        COMPARE["model_compare() / model_postprocess()"]
    end

    subgraph RUN["Runtime state"]
        BASE["BASE<br/>ConcreteModel"]
        SIM["SIM<br/>deep copy of BASE"]
        SOLVER["Nonlinear solver<br/>IPOPT / cyipopt"]
        RESULTS["Results<br/>DataFrame / files"]
    end

    USER --> SAMTOOLS
    USER --> EXAMPLE
    USER --> SPL
    USER --> STD
    SAM --> SAMTOOLS
    SAMTOOLS --> LOAD
    EXAMPLE --> LOAD
    LOAD --> DATA
    SPL --> ABSTRACT
    STD --> ABSTRACT
    ABSTRACT --> INSTANCE
    DATA --> INSTANCE
    INSTANCE --> BASE
    BASE --> CLOSURE
    CLOSURE --> CAL
    CAL --> SOLVER
    SOLVER --> BASE
    BASE --> CLONE
    CLONE --> SIM
    SHOCK --> SIM
    SIM --> SOLVE
    SOLVE --> SOLVER
    SOLVER --> SIM
    BASE --> COMPARE
    SIM --> COMPARE
    COMPARE --> RESULTS
```

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
