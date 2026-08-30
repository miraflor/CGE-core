"""CGE-Core: practitioner-first computable general equilibrium modelling."""

from cge_core import sam
from cge_core.datasets import example_data
from cge_core._version import __version__
from cge_core.models import CamCGE, IFPRICGE, SimpleCGE, StandardCGE
from cge_core.workflow import CGE, Equilibrium, Result, Scenario
from cge_core._pycge import (
    CGEError,
    ComponentError,
    DataValidationError,
    PyCGE,
    SolveError,
    WorkflowError,
)

__all__ = [
    "SimpleCGE", "StandardCGE", "CamCGE", "IFPRICGE",
    "CGE", "Equilibrium", "Scenario", "Result",
    "sam", "example_data",
    "PyCGE", "CGEError", "WorkflowError", "ComponentError",
    "DataValidationError", "SolveError", "__version__",
]
