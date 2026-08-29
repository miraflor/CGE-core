"""Practitioner-first bundled-model entry points for CGE-Core v0.7."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Any, Optional, Sequence

import pandas as pd
from pyomo.environ import value

from cge_core.api import CGE
from cge_core.datasets import example_data
from cge_core.model_spec import CAM_SPEC, IFPRI_SPEC, SIMPLE_SPEC, STANDARD_SPEC
from cge_core.solvers import resolve_solver


class SimpleCGE:
    """Hosoe simple CGE with its canonical closure already declared."""

    def __init__(self, data, *, solver: Optional[str] = None):
        self.data = Path(data)
        self.solver = solver

    @classmethod
    def example(cls, *, solver: Optional[str] = None):
        return cls(example_data("splcge"), solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        from cge_core.models import SplCGE
        return CGE(model=SplCGE(), data=self.data, spec=SIMPLE_SPEC).solve_benchmark(
            solver=solver or self.solver
        )


class StandardCGE:
    """Hosoe standard CGE for ordinary policy analysis."""

    def __init__(self, data, *, accounts=None, solver: Optional[str] = None,
                 _tempdir=None):
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
        """Construct StandardCGE from one balanced SAM plus economic roles.

        Canonical Hosoe labels are defaults, so a SAM using those labels needs
        only ``StandardCGE.from_sam('sam.csv')``.  Real-country SAMs should pass
        the economically meaningful account roles explicitly.
        """
        from cge_core import samtools

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
        data = samtools.build_dataset(
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
        """Release a temporary dataset created by :meth:`from_sam`."""
        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def solve(self, *, solver: Optional[str] = None):
        from cge_core.models import StdCGE
        return CGE(
            model=StdCGE(accounts=self.accounts or None),
            data=self.data,
            spec=STANDARD_SPEC,
        ).solve_benchmark(solver=solver or self.solver)


class CamCGE:
    """First-class installed CAMCGE model using its own canonical closure."""

    def __init__(self, data, *, solver: Optional[str] = None):
        self.data = Path(data)
        self.solver = solver

    @classmethod
    def example(cls, *, solver: Optional[str] = None):
        import cam
        return cls(Path(cam.__file__).resolve().parent / "data", solver=solver)

    @classmethod
    def from_data(cls, data_dir, *, solver: Optional[str] = None):
        return cls(data_dir, solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        from cam.cam_model_def import CamModelDef
        return CGE(model=CamModelDef(), data=self.data, spec=CAM_SPEC).solve_benchmark(
            solver=solver or self.solver
        )


@dataclass(frozen=True)
class IFPRIEquilibrium:
    _dataset: Any
    _calibration: Any
    _model: Any
    _report: Any
    _solver: Optional[str] = None

    @property
    def raw(self):
        return self._model

    @property
    def closure(self):
        return "IFPRI canonical BASE closure (model-owned)"

    def value(self, component: str, *index):
        item = getattr(self._model, component)
        if index:
            item = item[index if len(index) > 1 else index[0]]
        return float(value(item))

    def summary(self) -> pd.DataFrame:
        return _ifpri_summary("BASE", self._report)

    def scenario(self, name: str):
        from cge_core.ifpri import build_ifpri_scenario_model, normalize_ifpri_scenario
        selected = normalize_ifpri_scenario(name)
        model = build_ifpri_scenario_model(self._dataset, selected, self._calibration)
        return IFPRIScenario(
            name=selected.value,
            base=self,
            model=model,
            solver=self._solver,
        )


@dataclass
class IFPRIScenario:
    name: str
    base: IFPRIEquilibrium
    model: Any
    solver: Optional[str] = None

    @property
    def raw(self):
        return self.model

    def solve(self, *, solver: Optional[str] = None):
        from cge_core.ifpri import solve_ifpri_scenario
        selected = resolve_solver(solver or self.solver)
        report = solve_ifpri_scenario(self.model, solver=selected)
        return IFPRIResult(self.name, self.model, report)

    def set(self, *args, **kwargs):
        raise NotImplementedError(
            "The bundled IFPRI implementation uses named, model-specific policy "
            "scenarios and macro closures. Use scenario('TARCUT1'), etc., or the "
            "advanced cge_core.ifpri API for custom closure work."
        )


@dataclass(frozen=True)
class IFPRIResult:
    name: str
    _model: Any
    _report: Any

    @property
    def raw(self):
        return self._model

    def value(self, component: str, *index):
        item = getattr(self._model, component)
        if index:
            item = item[index if len(index) > 1 else index[0]]
        return float(value(item))

    def summary(self) -> pd.DataFrame:
        return _ifpri_summary(self.name, self._report)

    def compare(self, reference: IFPRIEquilibrium) -> pd.DataFrame:
        from cge_core.ifpri import compare_ifpri_models
        if not isinstance(reference, IFPRIEquilibrium):
            raise TypeError("IFPRI comparisons require an IFPRIEquilibrium reference.")
        return compare_ifpri_models(reference.raw, self.raw, scenario=self.name)


def _ifpri_summary(label, report):
    return pd.DataFrame([{
        "model": IFPRI_SPEC.name,
        "family": IFPRI_SPEC.family,
        "state": label,
        "solver": report.solver,
        "status": report.status,
        "termination": report.termination_condition,
        "degrees_of_freedom": report.degrees_of_freedom,
        "max_abs_equation_residual": report.max_abs_equation_residual,
    }])


class IFPRICGE:
    """IFPRI Standard CGE adapter with an explicit synthetic/official boundary."""

    def __init__(self, dataset, *, source_kind: str, solver: Optional[str] = None):
        self.dataset = dataset
        self.source_kind = source_kind
        self.solver = solver

    @classmethod
    def synthetic(cls, *, solver: Optional[str] = None):
        from cge_core.ifpri.synthetic import build_synthetic_ifpri_dataset
        return cls(build_synthetic_ifpri_dataset(), source_kind="synthetic", solver=solver)

    @classmethod
    def from_official_source(cls, source, *, solver: Optional[str] = None):
        from cge_core.ifpri import load_ifpri_test_data
        return cls(load_ifpri_test_data(source), source_kind="official-source", solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        from cge_core.ifpri import (
            build_ifpri_base_solve_model,
            calibrate_ifpri_benchmark,
            solve_ifpri_base,
        )
        selected = resolve_solver(solver or self.solver)
        calibration = calibrate_ifpri_benchmark(self.dataset)
        model = build_ifpri_base_solve_model(self.dataset, calibration)
        report = solve_ifpri_base(model, solver=selected)
        return IFPRIEquilibrium(
            self.dataset, calibration, model, report, selected
        )
