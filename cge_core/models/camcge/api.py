"""Practitioner entry point for the published CAMCGE replication."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from cge_core.model_spec import CAM_SPEC
from cge_core.workflow import CGE
from .model import CamModelDef

_DATA_DIR = Path(__file__).resolve().parent / "data"

class CamCGE:
    """First-class installed CAMCGE model using its own canonical closure."""

    def __init__(self, data, *, solver: Optional[str] = None):
        self.data = Path(data)
        self.solver = solver

    @classmethod
    def example(cls, *, solver: Optional[str] = None):
        return cls(_DATA_DIR, solver=solver)

    @classmethod
    def from_data(cls, data_dir, *, solver: Optional[str] = None):
        return cls(data_dir, solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        return CGE(
            model=CamModelDef(),
            data=self.data,
            spec=CAM_SPEC,
        ).solve_benchmark(solver=solver or self.solver)
