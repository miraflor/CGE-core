"""CGE-Core: practitioner-first computable general equilibrium modelling."""

# Data helpers are cheap and available to model façades during package import.
from cge_core import sam
from cge_core.datasets import example_data
from cge_core._version import __version__

# Primary practitioner API.
from cge_core.models import CamCGE, IFPRICGE, SimpleCGE, StandardCGE
from cge_core.workflow import CGE, Equilibrium, Result, Scenario

# Retained lower-level compatibility API.
from cge_core.compat import (
    CGEError,
    ComponentError,
    DataValidationError,
    PyCGE,
    SolveError,
    WorkflowError,
)

# Historical public alias retained for v0.7 compatibility.
samtools = sam

__all__ = [
    "SimpleCGE",
    "StandardCGE",
    "CamCGE",
    "IFPRICGE",
    "CGE",
    "Equilibrium",
    "Scenario",
    "Result",
    "sam",
    "example_data",
    "PyCGE",
    "CGEError",
    "WorkflowError",
    "ComponentError",
    "DataValidationError",
    "SolveError",
    "samtools",
    "__version__",
]
