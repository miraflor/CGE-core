# -*- coding: utf-8 -*-
"""Public scientific lifecycle for CGE-Core v0.7.

The public path is intentionally small:
    configure -> solve -> scenario -> shock -> solve -> inspect

The economic equations remain in their validated model-definition modules.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Set, Tuple

import pandas as pd
from pyomo.environ import Objective, Param, Var, value

from cge_core.compat.pycge import ComponentError, WorkflowError
from cge_core.model_spec import ModelSpec
from cge_core._engine import CoreEngine

_ComponentKey = Tuple[str, Tuple[Any, ...]]


def _index_tuple(index: Any) -> Tuple[Any, ...]:
    if index is None:
        return ()
    if isinstance(index, tuple):
        return index
    return (index,)


def _scenario_key(name: str, index: Any) -> Tuple[str, Any]:
    try:
        hash(index)
        safe = index
    except TypeError:
        safe = repr(index)
    return name, safe


def _number(item: Any) -> Optional[float]:
    resolved = value(item, exception=False)
    return None if resolved is None else float(resolved)


def _component_item(instance, name: str, index: Any):
    component = instance.component(name)
    if component is None:
        raise ComponentError(f"'{name}' does not exist in this model state.")
    if component.ctype not in (Var, Param):
        raise ComponentError(f"'{name}' is not a variable or parameter.")
    try:
        if component.is_indexed():
            if index is None:
                raise KeyError(index)
            item = component[index]
        else:
            if index not in (None, ""):
                raise KeyError(index)
            item = component
    except (KeyError, TypeError) as exc:
        raise ComponentError(f"'{index}' is not an index of '{name}'.") from exc
    return component, item


def _extract_components(instance, ctype) -> Dict[_ComponentKey, Optional[float]]:
    values: Dict[_ComponentKey, Optional[float]] = {}
    for component in instance.component_objects(ctype, active=True):
        iterator = component.items() if component.is_indexed() else ((None, component),)
        for index, item in iterator:
            values[(component.name, _index_tuple(index))] = _number(item)
    return values


def _extract_objective(instance) -> Optional[float]:
    for objective in instance.component_data_objects(Objective, active=True):
        return _number(objective)
    return None


def _solver_metadata(results) -> Mapping[str, Optional[str]]:
    if results is None or getattr(results, "solver", None) is None:
        return MappingProxyType({})
    solver = results.solver
    return MappingProxyType({
        "status": None if getattr(solver, "status", None) is None else str(solver.status),
        "termination_condition": (
            None if getattr(solver, "termination_condition", None) is None
            else str(solver.termination_condition)
        ),
    })


@dataclass(frozen=True)
class _Snapshot:
    model_id: str
    label: str
    variables: Mapping[_ComponentKey, Optional[float]]
    parameters: Mapping[_ComponentKey, Optional[float]]
    objective: Optional[float]
    solver: Mapping[str, Optional[str]]

    @classmethod
    def from_instance(cls, *, model_id: str, label: str, instance, results):
        return cls(
            model_id=model_id,
            label=label,
            variables=MappingProxyType(_extract_components(instance, Var)),
            parameters=MappingProxyType(_extract_components(instance, Param)),
            objective=_extract_objective(instance),
            solver=_solver_metadata(results),
        )

    @property
    def component_names(self) -> Set[str]:
        return {
            *(name for name, _ in self.variables),
            *(name for name, _ in self.parameters),
        }

    def value(self, component: str, *index: Any) -> Optional[float]:
        key = (component, tuple(index))
        if key in self.variables:
            return self.variables[key]
        if key in self.parameters:
            return self.parameters[key]
        if component not in self.component_names:
            raise ComponentError(f"Component '{component}' is not present in this result.")
        shown = index if index else "scalar"
        raise ComponentError(f"Index {shown!r} does not identify a value of '{component}'.")


def _summary_frame(snapshot: _Snapshot, spec: Optional[ModelSpec]) -> pd.DataFrame:
    return pd.DataFrame([{
        "model": spec.name if spec else snapshot.model_id,
        "family": spec.family if spec else snapshot.model_id,
        "state": snapshot.label,
        "status": snapshot.solver.get("status"),
        "termination": snapshot.solver.get("termination_condition"),
        "objective": snapshot.objective,
    }])


class CGE:
    """Configured static-CGE blueprint.

    The v0.6 constructor remains valid.  v0.7 additionally accepts a ModelSpec
    so model-owned default closure and semantic metadata can be used.
    """

    def __init__(self, model, data, *, spec: Optional[ModelSpec] = None):
        self._model_definition = model
        self._data = data
        self._model_id = type(model).__name__
        self._spec = spec

    def solve_benchmark(
        self,
        *,
        numeraire: Optional[Tuple[str, Any]] = None,
        redundant: Optional[Tuple[str, Any]] = None,
        solver: Optional[str] = None,
        solver_manager: Optional[str] = None,
    ) -> "Equilibrium":
        """Construct, close, solve, and snapshot the benchmark equilibrium."""
        if self._spec:
            numeraire = numeraire or self._spec.default_numeraire
            redundant = redundant or self._spec.default_redundant
        if not isinstance(numeraire, tuple) or len(numeraire) != 2:
            raise ValueError("numeraire must be a (component, index) pair.")
        if not isinstance(redundant, tuple) or len(redundant) != 2:
            raise ValueError("redundant must be a (component, index) pair.")

        spec = self._spec or ModelSpec(
            name=self._model_id,
            family=self._model_id,
            default_numeraire=numeraire,
            default_redundant=redundant,
            benchmark_only=frozenset(
                getattr(self._model_definition, "benchmark_only_components", ())
            ),
            base_protected=frozenset(
                getattr(self._model_definition, "base_protected_components", ())
            ),
            required_data=frozenset(
                getattr(self._model_definition, "required_data_files", ())
            ),
        )
        engine = CoreEngine(self._model_definition, spec)
        engine.model_data(self._data)
        engine.model_instance(numeraire[0], numeraire[1])
        engine.model_drop_redundant(redundant[0], redundant[1])
        engine.model_calibrate(solver=solver, mgr=solver_manager or "")
        snapshot = _Snapshot.from_instance(
            model_id=self._model_id,
            label="benchmark",
            instance=engine.base,
            results=engine.base_results,
        )
        return Equilibrium(_engine=engine, _snapshot=snapshot, _spec=spec)


@dataclass(frozen=True)
class Equilibrium:
    """Solved protected benchmark with immutable numerical reads."""

    _engine: CoreEngine
    _snapshot: _Snapshot
    _spec: Optional[ModelSpec] = None

    @property
    def objective(self) -> Optional[float]:
        return self._snapshot.objective

    @property
    def raw(self):
        """Advanced escape hatch to the live Pyomo benchmark model."""
        return self._engine.base

    @property
    def closure(self):
        return None if self._spec is None else self._spec.closure

    def value(self, component: str, *index: Any) -> Optional[float]:
        return self._snapshot.value(component, *index)

    def summary(self) -> pd.DataFrame:
        return _summary_frame(self._snapshot, self._spec)

    def scenario(self, name: str) -> "Scenario":
        """Create one independent counterfactual using exactly one model clone."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Scenario name must be a non-empty string.")

        # Shallow-copy engine bookkeeping, then deep-copy only the calibrated
        # concrete model.  The benchmark is shared read-only; the scenario owns
        # one and only one independent mutable model clone.
        engine = copy.copy(self._engine)
        engine.sim = copy.deepcopy(self._engine.base)
        engine.sim_results = None
        engine.sim_solved = False
        engine.dict_sim = {}
        return Scenario(
            name=name.strip(),
            model_id=self._snapshot.model_id,
            engine=engine,
            spec=self._spec,
        )


class Scenario:
    """Independent mutable policy experiment derived from one benchmark."""

    def __init__(self, *, name: str, model_id: str, engine: CoreEngine,
                 spec: Optional[ModelSpec] = None):
        self.name = name
        self._model_id = model_id
        self._engine = engine
        self._spec = spec
        self._fixed_by_scenario: Set[Tuple[str, Any]] = set()

    @property
    def raw(self):
        return self._engine.sim

    def set(self, component: str, index: Any, new_value: Any) -> "Scenario":
        model_component, _ = _component_item(self._engine.sim, component, index)
        self._engine.model_modify_sim(component, index, new_value, fix=True, undo=False)
        if model_component.ctype is Var:
            self._fixed_by_scenario.add(_scenario_key(component, index))
        return self

    def undo(self, component: str, index: Any = None) -> "Scenario":
        self._engine.model_modify_sim(component, index, 0, fix=True, undo=True)
        self._fixed_by_scenario.discard(_scenario_key(component, index))
        return self

    def _semantic(self, concept: str, index: Any, value_: Any = None,
                  *, change: Optional[float] = None) -> "Scenario":
        if self._spec is None or concept not in self._spec.semantic_shocks:
            raise ComponentError(
                f"This model does not declare a semantic '{concept}' shock; use set()."
            )
        component = self._spec.semantic_shocks[concept]
        if value_ is not None and change is not None:
            raise ValueError("Give either a level value or change=, not both.")
        if change is not None:
            _, item = _component_item(self._engine.sim, component, index)
            current = _number(item)
            if current is None:
                raise ComponentError(f"{component}[{index}] has no numeric value.")
            value_ = current * (1.0 + float(change))
        if value_ is None:
            raise ValueError("A level value or change= is required.")
        return self.set(component, index, value_)

    def tariff(self, good: Any, value_: Any = None, *, change: Optional[float] = None):
        return self._semantic("tariff", good, value_, change=change)

    def production_tax(self, good: Any, value_: Any = None,
                       *, change: Optional[float] = None):
        return self._semantic("production_tax", good, value_, change=change)

    def endowment(self, factor: Any, value_: Any = None,
                  *, change: Optional[float] = None):
        return self._semantic("endowment", factor, value_, change=change)

    def unfix(self, component: str, index: Any = None) -> "Scenario":
        model_component, item = _component_item(self._engine.sim, component, index)
        if model_component.ctype is Param:
            raise ComponentError(
                f"'{component}' is exogenous as a parameter; changing closure "
                "requires an advanced model/closure operation."
            )
        key = _scenario_key(component, index)
        if key == self._engine.numeraire:
            raise ComponentError(f"{component}[{index}] is the benchmark numeraire.")
        if key not in self._fixed_by_scenario:
            raise ComponentError(
                f"{component}[{index}] was not fixed by set(); only variables "
                "fixed by this scenario can be unfixed."
            )
        current = _number(item)
        self._engine.model_modify_sim(component, index, current, fix=False, undo=False)
        self._fixed_by_scenario.remove(key)
        return self

    def solve(self, *, solver: Optional[str] = None,
              solver_manager: Optional[str] = None) -> "Result":
        dof = self._engine.degrees_of_freedom(self._engine.sim)
        if dof != 0:
            raise WorkflowError(
                f"Scenario closure is incomplete: degrees of freedom = {dof}."
            )
        self._engine.model_solve(solver=solver, mgr=solver_manager or "")
        snapshot = _Snapshot.from_instance(
            model_id=self._model_id,
            label=self.name,
            instance=self._engine.sim,
            results=self._engine.sim_results,
        )
        return Result(_snapshot=snapshot, _spec=self._spec, _raw=self._engine.sim)


@dataclass(frozen=True)
class Result:
    """Immutable numerical snapshot of one successful scenario solve."""

    _snapshot: _Snapshot
    _spec: Optional[ModelSpec] = None
    _raw: Any = field(default=None, repr=False, compare=False)

    @property
    def name(self) -> str:
        return self._snapshot.label

    @property
    def objective(self) -> Optional[float]:
        return self._snapshot.objective

    @property
    def solver(self) -> Mapping[str, Optional[str]]:
        return self._snapshot.solver

    @property
    def raw(self):
        """Advanced live model access; snapshot reads remain immutable."""
        return self._raw

    def value(self, component: str, *index: Any) -> Optional[float]:
        return self._snapshot.value(component, *index)

    def summary(self) -> pd.DataFrame:
        return _summary_frame(self._snapshot, self._spec)

    def compare(self, reference) -> pd.DataFrame:
        if isinstance(reference, Equilibrium):
            other = reference._snapshot
        elif isinstance(reference, Result):
            other = reference._snapshot
        else:
            raise TypeError("reference must be an Equilibrium or Result.")
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
            difference = pct_change = None
            if current is not None and base is not None:
                difference = current - base
                pct_change = math.nan if base == 0 else difference / base * 100.0
            row = {"component": component}
            for dimension in range(max_dims):
                row[f"index_{dimension + 1}"] = index[dimension] if dimension < len(index) else ""
            row.update({
                "reference_value": base,
                "value": current,
                "difference": difference,
                "pct_change": pct_change,
            })
            rows.append(row)
        columns = (["component"] + [f"index_{n + 1}" for n in range(max_dims)]
                   + ["reference_value", "value", "difference", "pct_change"])
        frame = pd.DataFrame(rows, columns=columns)
        objective_difference = None
        objective_pct = None
        if self.objective is not None and other.objective is not None:
            objective_difference = self.objective - other.objective
            objective_pct = (
                math.nan if other.objective == 0
                else objective_difference / other.objective * 100.0
            )
        frame.attrs["objective"] = {
            # ``reference`` is the v0.6 public key; retain it.
            "reference": other.objective,
            "reference_value": other.objective,
            "value": self.objective,
            "difference": objective_difference,
            "pct_change": objective_pct,
        }
        return frame
