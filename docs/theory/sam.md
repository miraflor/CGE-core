# Social Accounting Matrix

A Social Accounting Matrix (SAM) is the benchmark accounting system from which a CGE model is calibrated.

A SAM records payments between economic accounts such as:

- commodities or activities;
- factors of production;
- households;
- government;
- taxes;
- investment or saving; and
- the rest of the world.

For a balanced SAM, each account's total receipts equal its total payments.

CGE-Core uses benchmark flows to recover model parameters such as expenditure shares, factor shares, input coefficients, tax rates and saving rates. The calibrated model should reproduce the benchmark data before a policy shock is applied.

CGE-Core's `samtools` utilities can build a model data directory from a single SAM CSV.

See {doc}`../tutorials/loading-sam` for a worked example.
