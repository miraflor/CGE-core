"""CGE-Core: a Pyomo-based computable general equilibrium framework."""
from importlib.metadata import PackageNotFoundError, version as _version

from cge_core import samtools
from cge_core.api import CGE, Equilibrium, Result, Scenario
from cge_core.datasets import example_data
from cge_core.engine import (
    CGEError,
    ComponentError,
    DataValidationError,
    PyCGE,
    SolveError,
    WorkflowError,
)

try:
    __version__ = _version("cge-core")
except PackageNotFoundError:
    __version__ = "0.3.0.dev0"

__all__ = [
    "CGE",
    "Equilibrium",
    "Scenario",
    "Result",
    "PyCGE",
    "CGEError",
    "WorkflowError",
    "ComponentError",
    "DataValidationError",
    "SolveError",
    "example_data",
    "samtools",
    "__version__",
]
