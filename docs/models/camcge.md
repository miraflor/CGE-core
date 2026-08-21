# CAMCGE

CAMCGE is included as a repository-level replication benchmark.

Its role is different from the installed core models: it tests whether CGE-Core can reproduce a published CGE implementation beyond the Hosoe and IFPRI benchmark families.

The replication checks:

- published base-equilibrium variable levels;
- the published objective value; and
- three published policy experiments.

CAMCGE remains outside the installed `cge_core` package because it is a replication benchmark rather than an independently authored core model subsystem.
