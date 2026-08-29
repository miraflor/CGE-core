"""Practitioner entry point for the Hosoe Simple CGE model."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from cge_core.datasets import example_data
from cge_core.model_spec import SIMPLE_SPEC
from cge_core.workflow import CGE
from .model import SplModelDef

class SimpleCGE:
    """Hosoe simple CGE with its canonical closure already declared."""

    def __init__(self, data, *, solver: Optional[str] = None):
        self.data = Path(data)
        self.solver = solver

    @classmethod
    def example(cls, *, solver: Optional[str] = None):
        return cls(example_data("splcge"), solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        return CGE(
            model=SplModelDef(),
            data=self.data,
            spec=SIMPLE_SPEC,
        ).solve_benchmark(solver=solver or self.solver)
