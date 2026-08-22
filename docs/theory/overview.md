# CGE Theory

A computable general equilibrium model describes an economy as a system of
mutually dependent markets and institutions.

## Standard-model structure

```{mermaid}
flowchart LR

    SAM["Benchmark SAM"] --> CAL["Calibration"]

    subgraph PROD["Production"]
        FAC["Primary factors"] --> FIRMS["Firms / activities"]
        INT["Intermediate inputs"] --> FIRMS
        FIRMS --> OUT["Domestic output"]
        FIRMS --> FINC["Factor income"]
    end

    subgraph INST["Institutions and final demand"]
        FINC --> HH["Households"]
        HH --> CONS["Household consumption"]
        HH --> PSAV["Private saving"]
        HH --> DTAX["Direct taxes"]
        DTAX --> GOV["Government"]
        PTAX["Production taxes"] --> GOV
        MTAX["Import tariffs"] --> GOV
        GOV --> GCONS["Government consumption"]
        GOV --> GSAV["Government saving"]
        PSAV --> SAV["Total saving"]
        GSAV --> SAV
        FSAV["Foreign saving"] --> SAV
        SAV --> INV["Investment demand"]
    end

    subgraph TRADE["Trade"]
        OUT --> CET["CET transformation"]
        CET --> EXP["Exports"]
        CET --> DOM["Domestic sales"]
        IMP["Imports"] --> ARM["Armington composite"]
        DOM --> ARM
    end

    ARM --> CONS
    ARM --> GCONS
    ARM --> INV
    ARM --> INT
    EXP --> ROW["Rest of world"]
    ROW --> IMP
    EXP --> BOP["Balance of payments"]
    IMP --> BOP
    FSAV --> BOP
    FAC --> FMKT["Factor-market clearing"]
    FIRMS --> FMKT
    ARM --> CMKT["Commodity-market clearing"]
    CONS --> CMKT
    GCONS --> CMKT
    INV --> CMKT
    INT --> CMKT
    FMKT --> EQ["General equilibrium"]
    CMKT --> EQ
    BOP --> EQ
    CLOS["Closure + numeraire"] -.-> EQ
    CAL -.-> PROD
    CAL -.-> INST
    CAL -.-> TRADE
```

CGE-Core's standard model can be understood in five blocks:

1. **benchmark accounting** — the Social Accounting Matrix;
2. **production** — firms combine factors and intermediate inputs;
3. **final demand** — households, government, and investment demand goods;
4. **trade** — domestic and foreign goods are imperfect substitutes and
   output can be allocated between domestic and export markets; and
5. **closure** — prices and quantities adjust until all independent
   equilibrium conditions hold.

The following pages explain these blocks using the equations implemented in
CGE-Core.
