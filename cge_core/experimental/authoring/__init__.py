"""No-inheritance authoring interface for research CGE models."""
from .module_adapter import FunctionalEconomy, model_from_module

__all__ = ["FunctionalEconomy", "model_from_module"]
