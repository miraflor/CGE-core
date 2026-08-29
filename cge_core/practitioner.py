"""Compatibility import path for the v0.7 practitioner façade."""
from cge_core.models.camcge.api import CamCGE
from cge_core.models.ifpri.api import IFPRICGE, IFPRIEquilibrium, IFPRIResult, IFPRIScenario
from cge_core.models.simple.api import SimpleCGE
from cge_core.models.standard.api import StandardCGE

__all__ = [
    "SimpleCGE", "StandardCGE", "CamCGE", "IFPRICGE",
    "IFPRIEquilibrium", "IFPRIScenario", "IFPRIResult",
]
