# Loading Your Own SAM

CGE-Core can build a standard-model dataset from a single balanced SAM CSV.

```python
from cge_core import CGE, samtools
from cge_core.models import StdCGE

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

model = CGE(
    model=StdCGE(accounts=accounts),
    data="my_data_dir",
)
```

`samtools.build_dataset()` writes the set files and SAM file expected by the
Standard CGE model. `StdCGE(accounts=accounts)` tells the model which labels in
your SAM correspond to the household, government, investment, external,
indirect-tax, and tariff accounts.

The SAM must be square, have unique labels, contain finite values, and balance by account.

The goods set is inferred from accounts that are neither declared factors nor named institutions.

The resulting `CGE` object is a model blueprint. To solve a benchmark, choose
the appropriate numeraire and redundant market equation for your model and
call `solve_benchmark()` as shown in the quick start.

```{warning}
A balanced SAM is necessary but not sufficient for successful calibration. Benchmark flows used inside ratios, Cobb-Douglas shares, and CES/CET calibration must also satisfy the positivity and nonzero assumptions of the reference model.
```
