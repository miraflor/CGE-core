"""IFPRI Standard CGE model family.

The package root deliberately exposes only the practitioner façade. Advanced
implementation APIs live in the explicit submodules such as ``calibration``,
``model``, ``scenarios``, and ``validation``.
"""
from .api import IFPRICGE, IFPRIEquilibrium, IFPRIResult, IFPRIScenario

__all__ = ["IFPRICGE", "IFPRIEquilibrium", "IFPRIScenario", "IFPRIResult"]
