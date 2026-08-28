# Developer Reference

CGE-Core separates the public scientific workflow from the lower-level engine
that implements it.

## Stable downstream surface

Packages that compose CGE-Core with other scientific software should depend on
the narrow {doc}`extension-contract`. It defines the supported
benchmark -> scenario -> solve -> read lifecycle and the public/private
boundary.

The extension contract is intentionally smaller than the complete public API.
Its purpose is to protect the capabilities that downstream packages need
without turning CGE-Core into a plugin framework.

## Advanced implementation surface

The Hosoe models are currently realized through the validated `PyCGE`/Pyomo
engine. Direct engine access remains available for advanced work, debugging,
model development, and compatibility, but its mutable implementation state is
not part of the downstream extension contract.

The main implementation areas are:

- Pyomo model definitions;
- benchmark calibration and solution;
- counterfactual scenario state;
- solver integration;
- result comparison;
- validation and regression testing.

The IFPRI subsystem and CAMCGE replication retain their dedicated workflows
rather than being forced behind the Hosoe facade.

If you are familiar with OG-Core, see {doc}`../OG_CORE_CROSSWALK`.
