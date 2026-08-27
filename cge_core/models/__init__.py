"""Supported model-definition imports for the CGE-Core public API.

The v0.6 namespace is an additive import facade.  The validated Hosoe model
files remain in their existing locations; no equations are moved or rewritten.
"""
from cge_core.examples.splcge_model_def import SplModelDef as SplCGE
from cge_core.examples.stdcge_model_def import StdModelDef as StdCGE

__all__ = ["SplCGE", "StdCGE"]
