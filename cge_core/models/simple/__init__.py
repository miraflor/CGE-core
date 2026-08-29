"""Hosoe Simple CGE model family."""
from .api import SimpleCGE
from .model import SplModelDef
SplCGE = SplModelDef
__all__ = ["SimpleCGE", "SplCGE", "SplModelDef"]
