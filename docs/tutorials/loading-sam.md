# Loading Your Own SAM

CGE-Core can build a standard-model dataset from a single balanced SAM CSV.

```python
from cge_core import PyCGE, samtools
from cge_core.examples.stdcge_model_def import StdModelDef

accounts = dict(
    hoh="HH",
    gov="GOVT",
    inv="SAV-INV",
    ext="ROW",
    idt="ITAX",
    trf="TARIFF",
)

samtools.build_dataset(
    "my_sam.csv",
    "my_data_dir",
    factors=["CAP", "LAB"],
    institutions=accounts.values(),
)

cge = PyCGE(StdModelDef(accounts=accounts))
cge.model_data("my_data_dir")
```

The SAM must be square, have unique labels, contain finite values, and balance by account.

The goods set is inferred from accounts that are neither declared factors nor named institutions.

```{warning}
A balanced SAM is necessary but not sufficient for successful calibration. Benchmark flows used inside ratios, Cobb-Douglas shares, and CES/CET calibration must also satisfy the positivity and nonzero assumptions of the reference model.
```
