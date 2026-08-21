# Standard CGE

The standard model extends the simple economy to include the institutions and trade structure commonly used in applied CGE work.

It includes:

- production with intermediate inputs and primary factors;
- household consumption and saving;
- government taxation, consumption and saving;
- investment demand;
- imports using an Armington CES composite;
- exports using CET transformation;
- a balance-of-payments condition; and
- endogenous market-clearing prices.

The implementation follows Hosoe, Gasawa and Hashimoto and is checked against the GAMS Model Library `stdcge` model.

## Read it at three levels

| Level | Where to go |
| --- | --- |
| Economic intuition | {doc}`../theory/overview` |
| Equation-by-equation specification | {doc}`../MODEL` |
| Python implementation | {doc}`../api/model-definitions` |

For the relationship among data, the model definition, the solver and the counterfactual workflow, see {doc}`../architecture`.
