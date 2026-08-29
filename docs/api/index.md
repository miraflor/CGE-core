# API reference

## Practitioner entry points

- {doc}`public` — `SimpleCGE`, `StandardCGE`, `CamCGE`, `IFPRICGE`, benchmark/scenario/results
- {doc}`samtools` — SAM conversion and validation
- {doc}`ifpri` — advanced IFPRI-specific API

## Lower-level compatibility

- {doc}`model-definitions` — model-definition classes
- {doc}`datasets` — packaged example data
- {doc}`engine` — `PyCGE` / engine-level implementation

New application code should normally begin with a model-specific practitioner entry point.
The lower-level API remains supported for advanced inspection and compatibility.
