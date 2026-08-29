# Loading your own SAM

A social accounting matrix (SAM) records a balanced set of payments between production,
factors, institutions, investment, government, and the rest of the world.

For a SAM using the canonical Hosoe account names:

```python
from cge_core import StandardCGE

economy = StandardCGE.from_sam("sam.csv")
base = economy.solve()
```

For a country-specific SAM, state the **economic roles** explicitly:

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
base = economy.solve()
```

`from_sam()` validates and converts the accounting table into the internal dataset expected
by the Standard CGE model. A balanced SAM is necessary, but it does not by itself guarantee
that every empirical SAM matches the Hosoe model's structural assumptions.

If a temporary internal dataset is created, `StandardCGE` manages its lifecycle. For
long-running applications, it may also be used as a context manager.
