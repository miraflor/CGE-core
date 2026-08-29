"""Functional/declarative Python model adapter.

A model-author module supplies functions and declarations, not a subclass:

    def build_model(data): ...
    def apply_default_closure(model): ...
    benchmark_only = {...}
    shockable = {...}
"""
from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Optional

import pandas as pd

from cge_core.api import _Snapshot
from cge_core.engine import ComponentError, SolveError, WorkflowError
from cge_core.solvers import resolve_solver


def _load_module(module_or_path) -> ModuleType:
    if isinstance(module_or_path, ModuleType):
        return module_or_path
    path = Path(str(module_or_path))
    if path.suffix == ".py" or path.exists():
        path = path.resolve()
        spec = importlib.util.spec_from_file_location(f"cge_user_model_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load model module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(str(module_or_path))


def _solve(model, solver=None):
    from pyomo.environ import SolverFactory
    from pyomo.opt import check_optimal_termination

    selected = resolve_solver(solver)
    results = SolverFactory(selected).solve(model)
    if not check_optimal_termination(results):
        raise SolveError(
            f"Solver did not reach an acceptable optimum: "
            f"{results.solver.status}/{results.solver.termination_condition}",
            results=results,
        )
    return results


def _dof(model):
    from cge_core.engine import PyCGE
    return PyCGE.degrees_of_freedom(model)


class FunctionalEconomy:
    """Adapter around a function-based user model module."""

    def __init__(self, module: ModuleType, data=None, *, solver: Optional[str] = None):
        self.module = module
        self.data = data
        self.solver = solver
        if not callable(getattr(module, "build_model", None)):
            raise TypeError("Custom model module must define build_model(data).")
        if not callable(getattr(module, "apply_default_closure", None)):
            raise TypeError("Custom model module must define apply_default_closure(model).")
        self.name = str(getattr(module, "model_name", module.__name__))
        self.benchmark_only = frozenset(getattr(module, "benchmark_only", ()))
        declared_shockable = getattr(module, "shockable", None)
        self.shockable = (
            None if declared_shockable is None else frozenset(declared_shockable)
        )

    def solve(self, *, solver: Optional[str] = None):
        model = self.module.build_model(self.data)
        self.module.apply_default_closure(model)
        dof = _dof(model)
        if dof != 0:
            raise WorkflowError(
                f"Custom model default closure has {dof} degrees of freedom; expected 0."
            )
        results = _solve(model, solver or self.solver)
        snapshot = _Snapshot.from_instance(
            model_id=self.name, label="benchmark", instance=model, results=results
        )
        return FunctionalEquilibrium(self, model, snapshot)


class FunctionalEquilibrium:
    def __init__(self, economy: FunctionalEconomy, model, snapshot):
        self._economy = economy
        self._model = model
        self._snapshot = snapshot

    @property
    def raw(self):
        return self._model

    @property
    def objective(self):
        return self._snapshot.objective

    def value(self, component, *index):
        return self._snapshot.value(component, *index)

    def summary(self):
        return pd.DataFrame([{
            "model": self._economy.name,
            "state": "benchmark",
            "status": self._snapshot.solver.get("status"),
            "termination": self._snapshot.solver.get("termination_condition"),
            "objective": self.objective,
        }])

    def scenario(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Scenario name must be non-empty.")
        return FunctionalScenario(self, name.strip(), copy.deepcopy(self._model))


class FunctionalScenario:
    def __init__(self, base: FunctionalEquilibrium, name: str, model):
        self.base = base
        self.name = name
        self.model = model

    @property
    def raw(self):
        return self.model

    def set(self, component, index, new_value, *, fix=True):
        from pyomo.environ import Param, Var
        target = self.model.component(component)
        if target is None or target.ctype not in (Param, Var):
            raise ComponentError(f"Unknown variable/mutable parameter {component!r}.")
        if component in self.base._economy.benchmark_only:
            raise ComponentError(f"{component!r} is declared benchmark-only.")
        if (self.base._economy.shockable is not None
                and component not in self.base._economy.shockable):
            raise ComponentError(
                f"{component!r} is not declared shockable by this custom model."
            )
        if target.ctype is Param and not target.mutable:
            raise ComponentError(f"{component!r} is immutable and cannot be modified.")
        item = target[index] if target.is_indexed() else target
        item.set_value(float(new_value))
        if target.ctype is Var:
            item.fix() if fix else item.unfix()
        return self

    def solve(self, *, solver=None):
        dof = _dof(self.model)
        if dof != 0:
            raise WorkflowError(
                f"Custom scenario closure has {dof} degrees of freedom; expected 0."
            )
        results = _solve(self.model, solver or self.base._economy.solver)
        snap = _Snapshot.from_instance(
            model_id=self.base._economy.name,
            label=self.name,
            instance=self.model,
            results=results,
        )
        return FunctionalResult(self.base._economy, self.model, snap)


class FunctionalResult:
    def __init__(self, economy, model, snapshot):
        self._economy = economy
        self._model = model
        self._snapshot = snapshot

    @property
    def raw(self):
        return self._model

    @property
    def objective(self):
        return self._snapshot.objective

    def value(self, component, *index):
        return self._snapshot.value(component, *index)

    def summary(self):
        return pd.DataFrame([{
            "model": self._economy.name,
            "state": self._snapshot.label,
            "status": self._snapshot.solver.get("status"),
            "termination": self._snapshot.solver.get("termination_condition"),
            "objective": self.objective,
        }])

    def compare(self, reference):
        if not isinstance(reference, (FunctionalEquilibrium, FunctionalResult)):
            raise TypeError("reference must be a FunctionalEquilibrium or FunctionalResult.")
        other = reference._snapshot
        if self._snapshot.model_id != other.model_id:
            raise WorkflowError("Cannot compare results from different model definitions.")
        if set(self._snapshot.variables) != set(other.variables):
            raise WorkflowError("Cannot compare structurally incompatible model results.")
        keys = sorted(self._snapshot.variables, key=lambda item: (item[0], repr(item[1])))
        max_dims = max((len(index) for _, index in keys), default=0)
        rows = []
        for component, index in keys:
            current = self._snapshot.variables[(component, index)]
            base = other.variables[(component, index)]
            difference = pct = None
            if current is not None and base is not None:
                difference = current - base
                pct = float("nan") if base == 0 else difference / base * 100
            row = {"component": component}
            for dimension in range(max_dims):
                row[f"index_{dimension + 1}"] = index[dimension] if dimension < len(index) else ""
            row.update({"reference_value": base, "value": current, "difference": difference, "pct_change": pct})
            rows.append(row)
        columns = (["component"] + [f"index_{n + 1}" for n in range(max_dims)] + ["reference_value", "value", "difference", "pct_change"])
        frame = pd.DataFrame(rows, columns=columns)
        objective_difference = objective_pct = None
        if self.objective is not None and other.objective is not None:
            objective_difference = self.objective - other.objective
            objective_pct = float("nan") if other.objective == 0 else objective_difference / other.objective * 100
        frame.attrs["objective"] = {"reference": other.objective, "reference_value": other.objective, "value": self.objective, "difference": objective_difference, "pct_change": objective_pct}
        return frame



def model_from_module(module_or_path, data=None, *, solver: Optional[str] = None):
    """Return a FunctionalEconomy from a module object, import name, or .py file."""
    return FunctionalEconomy(_load_module(module_or_path), data=data, solver=solver)
