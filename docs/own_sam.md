# Bring your own SAM

A **social accounting matrix (SAM)** is a square accounting table. Rows record receipts and columns record expenditures. For every account, total receipts and total expenditures must balance.

`StandardCGE.from_sam()` turns one balanced SAM into the internal data representation required by the validated Hosoe standard model.

## Canonical labels

If your SAM uses the bundled model's account labels:

- factors: `CAP`, `LAB`
- household: `HOH`
- government: `GOV`
- saving/investment: `INV`
- external/rest of world: `EXT`
- indirect tax: `IDT`
- tariff: `TRF`

then:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

## Real-country labels

Do not rely on clever spelling inference. State the economic roles:

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

CGE-Core checks square structure, numeric/finite entries, unique labels, and accounting balance. It then derives the goods set as the accounts that are neither declared factors nor declared institutions.

`from_sam()` does **not** imply that any arbitrary SAM is economically compatible with the Hosoe model. Benchmark flows must still satisfy the model's calibration assumptions, including required positive/nonzero flows.
