"""Practitioner entry point for the IFPRI Standard CGE implementation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd
from pyomo.environ import value

from cge_core.model_spec import IFPRI_SPEC
from cge_core.solver import resolve_solver
from .calibration import calibrate_ifpri_benchmark
from .data import load_ifpri_test_data
from .reporting import compare_ifpri_models
from .scenarios import build_ifpri_scenario_model, normalize_ifpri_scenario, solve_ifpri_scenario
from .solve import build_ifpri_base_solve_model, solve_ifpri_base
from .synthetic import build_synthetic_ifpri_dataset

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
        selected = normalize_ifpri_scenario(name)
        model = build_ifpri_scenario_model(self._dataset, selected, self._calibration)
        return IFPRIScenario(selected.value, self, model, self._solver)

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
        selected = resolve_solver(solver or self.solver)
        report = solve_ifpri_scenario(self.model, solver=selected)
        return IFPRIResult(self.name, self.model, report)

    def set(self, *args, **kwargs):
        raise NotImplementedError(
            "The bundled IFPRI implementation uses named, model-specific policy "
            "scenarios and macro closures. Use scenario('TARCUT1'), etc., or the "
            "advanced cge_core.models.ifpri API for custom closure work."
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
        return cls(build_synthetic_ifpri_dataset(), source_kind="synthetic", solver=solver)

    @classmethod
    def from_official_source(cls, source, *, solver: Optional[str] = None):
        return cls(load_ifpri_test_data(source), source_kind="official-source", solver=solver)

    def solve(self, *, solver: Optional[str] = None):
        selected = resolve_solver(solver or self.solver)
        calibration = calibrate_ifpri_benchmark(self.dataset)
        model = build_ifpri_base_solve_model(self.dataset, calibration)
        report = solve_ifpri_base(model, solver=selected)
        return IFPRIEquilibrium(self.dataset, calibration, model, report, selected)
