"""Hosoe Standard CGE model family."""
from .api import StandardCGE
from .model import StdModelDef
StdCGE = StdModelDef
__all__ = ["StandardCGE", "StdCGE", "StdModelDef"]
