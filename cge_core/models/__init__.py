"""Validated model-definition imports plus canonical v0.7 model namespaces.

SplCGE and StdCGE remain for v0.6 compatibility.  Ordinary v0.7 users import
SimpleCGE/StandardCGE/CamCGE/IFPRICGE from the package root instead.
"""
from cge_core.examples.splcge_model_def import SplModelDef as SplCGE
from cge_core.examples.stdcge_model_def import StdModelDef as StdCGE

__all__ = ["SplCGE", "StdCGE"]
