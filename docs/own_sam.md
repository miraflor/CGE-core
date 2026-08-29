# Bring your own SAM

A **social accounting matrix (SAM)** is a square accounting table. Rows record receipts and columns record expenditures. For every account, total receipts and total expenditures must balance.

`StandardCGE.from_sam()` converts one balanced SAM into the internal dataset expected by the validated Hosoe Standard model.

## Canonical account labels

The bundled economy uses:

- factors: `CAP`, `LAB`
- household: `HOH`
- government: `GOV`
- saving/investment: `INV`
- rest of world: `EXT`
- indirect/production tax: `IDT`
- tariff: `TRF`

With those labels:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

## Country-specific labels

State economic roles explicitly instead of relying on naming heuristics:

```python
economy = StandardCGE.from_sam(
    "country_sam.csv",
    factors=["LAB", "CAP"],
    household="HH",
    government="GOVT",
    investment="SAVINV",
    rest_of_world="ROW",
    indirect_tax="PTAX",
    tariff="TARIFF",
)
```

CGE-Core checks square structure, numeric/finite entries, unique labels, and accounting balance, then derives the goods set from accounts that are neither declared factors nor institutions.

A balanced SAM is not automatically a valid benchmark for every CGE specification. The flows must also satisfy the calibration assumptions and positivity/nonzero requirements of the Hosoe Standard model.
