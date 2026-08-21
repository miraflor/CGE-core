# Hosoe / GAMS Validation

The simple and standard models are checked against their corresponding GAMS Model Library references.

For the standard model, CGE-Core maintains an equation-by-equation crosswalk to `stdcge.gms` and regression tests the numerical equilibrium using a real nonlinear solver.

The validation also checks the model's explicit handling of the redundant market-clearing equation implied by Walras' law.

For the detailed validation record, see {doc}`../GAMS_STDCGE_VALIDATION`.
