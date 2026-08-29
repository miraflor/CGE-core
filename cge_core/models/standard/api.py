"""Practitioner entry point for the Hosoe Standard CGE model."""
from __future__ import annotations
from pathlib import Path
import tempfile
from typing import Optional, Sequence

import cge_core.sam as sam
from cge_core.datasets import example_data
from cge_core.model_spec import STANDARD_SPEC
from cge_core.workflow import CGE
from .model import StdModelDef

class StandardCGE:
    """Hosoe standard CGE for ordinary policy analysis."""

    def __init__(self, data, *, accounts=None, solver: Optional[str] = None, _tempdir=None):
        self.data = Path(data)
        self.accounts = dict(accounts or {})
        self.solver = solver
        self._tempdir = _tempdir

    @classmethod
    def example(cls, *, solver: Optional[str] = None):
        return cls(example_data("stdcge"), solver=solver)

    @classmethod
    def from_sam(
        cls,
        sam_path,
        *,
        factors: Sequence[str] = ("CAP", "LAB"),
        household: str = "HOH",
        government: str = "GOV",
        investment: str = "INV",
        rest_of_world: str = "EXT",
        indirect_tax: str = "IDT",
        tariff: str = "TRF",
        out_dir=None,
        solver: Optional[str] = None,
    ):
        """Construct StandardCGE from one balanced SAM plus economic roles."""
        accounts = {
            "hoh": household,
            "gov": government,
            "inv": investment,
            "ext": rest_of_world,
            "idt": indirect_tax,
            "trf": tariff,
        }
        temp = None
        if out_dir is None:
            temp = tempfile.TemporaryDirectory(prefix="cge-core-sam-")
            out_dir = temp.name

        data = sam.build_dataset(
            sam_path,
            out_dir,
            factors=list(factors),
            institutions=[
                accounts["hoh"], accounts["gov"], accounts["inv"],
                accounts["ext"], accounts["idt"], accounts["trf"],
            ],
        )
        return cls(data, accounts=accounts, solver=solver, _tempdir=temp)

    def close(self):
        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def solve(self, *, solver: Optional[str] = None):
        return CGE(
            model=StdModelDef(accounts=self.accounts or None),
            data=self.data,
            spec=STANDARD_SPEC,
        ).solve_benchmark(solver=solver or self.solver)
