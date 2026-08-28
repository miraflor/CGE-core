# Getting Started

For the Hosoe teaching models, CGE-Core v0.6 is organized around one explicit
counterfactual workflow:

**configure model → solve benchmark → create scenario → shock → solve → compare**

If you are new to the project, use these pages in order:

1. {doc}`../architecture` — see how the public façade, economic equations,
   validated engine, solver, and result snapshots fit together.
2. {doc}`installation` — create an environment and install CGE-Core.
3. {doc}`quickstart` — solve the standard benchmark and one tariff reform.
4. {doc}`first-simulation` — understand the benchmark, scenario, and result
   objects economically and computationally.

The public Hosoe workflow is deliberately small: `CGE` is a stateless blueprint,
`Equilibrium` protects a solved benchmark, `Scenario` holds one independent
counterfactual, and `Result` is an immutable numerical snapshot.

The IFPRI subsystem and CAMCGE replication benchmark keep their own validated
workflows; they are not forced through the Hosoe façade.

For the lower-level `PyCGE` state machine used underneath the Hosoe façade and
for advanced inspection, see {doc}`../workflow`.
