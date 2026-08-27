# -*- coding: utf-8 -*-
"""Public domain API for CGE-Core v0.6.

This module is new CGE-Core work.  It provides a small scientific-Python
facade over the validated legacy :class:`cge_core.engine.PyCGE` workflow
without changing the economic equations or the legacy engine contract.

The public lifecycle is::

    CGE -> solve_benchmark -> Equilibrium -> Scenario -> Result

``CGE`` is a configuration blueprint.  Every benchmark solve owns a fresh
legacy engine.  Every Scenario owns a deep-copied engine, so simultaneously
live counterfactuals cannot share the legacy engine's single ``sim`` slot.
``Result`` stores plain numerical snapshots so earlier results never change
when a Scenario is subsequently modified and solved again.

Provenance: new CGE-Core v0.6 facade written for the CGE-Core reengineering
work (2026), via an AI-assisted workflow directed and reviewed by the project
maintainer.  The underlying PyCGE engine and Hosoe model ports retain their
own provenance; this module does not claim authorship of them.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Set, Tuple

import pandas as pd
from pyomo.environ import Objective, Param, Var, value

from cge_core.engine import ComponentError, PyCGE, WorkflowError

_ComponentKey = Tuple[str, Tuple[Any, ...]]


def _index_tuple(index: Any) -> Tuple[Any, ...]:
    """Normalize a Pyomo index to the snapshot's tuple representation."""
    if index is None:
        return ()
    if isinstance(index, tuple):
        return index
    return (index,)


def _scenario_key(name: str, index: Any) -> Tuple[str, Any]:
    """Return a hashable key used only by the facade's Scenario bookkeeping."""
    try:
        hash(index)
        safe = index
    except TypeError:
        safe = repr(index)
    return name, safe


def _number(item: Any) -> Optional[float]:
    """Return a Pyomo numeric value as a plain float, preserving ``None``."""
    resolved = value(item, exception=False)
    if resolved is None:
        return None
    return float(resolved)


def _component_item(instance, name: str, index: Any):
    """Resolve one Var/Param item with the legacy engine's scalar convention."""
    component = instance.component(name)
    if component is None:
        raise ComponentError(f"'{name}' does not exist in this scenario.")
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
    except (KeyError, TypeError):
        raise ComponentError(f"'{index}' is not an index of '{name}'.")
    return component, item


def _extract_components(instance, ctype) -> Dict[_ComponentKey, Optional[float]]:
    """Extract one Pyomo component type into backend-neutral numeric values."""
    values: Dict[_ComponentKey, Optional[float]] = {}
    for component in instance.component_objects(ctype, active=True):
        name = component.name
        if component.is_indexed():
            iterator = component.items()
        else:
            iterator = ((None, component),)
        for index, item in iterator:
            values[(name, _index_tuple(index))] = _number(item)
    return values


def _extract_objective(instance) -> Optional[float]:
    """Return the first active scalar objective value, if the model has one."""
    for objective in instance.component_data_objects(Objective, active=True):
        return _number(objective)
    return None


def _solver_metadata(results) -> Mapping[str, Optional[str]]:
    """Return small, serializable solver metadata rather than SolverResults."""
    if results is None:
        return MappingProxyType({})
    solver = getattr(results, "solver", None)
    if solver is None:
        return MappingProxyType({})
    status = getattr(solver, "status", None)
    termination = getattr(solver, "termination_condition", None)
    return MappingProxyType({
        "status": None if status is None else str(status),
        "termination_condition": (
            None if termination is None else str(termination)
        ),
    })


@dataclass(frozen=True)
class _Snapshot:
    """Private immutable numerical state shared by Equilibrium and Result."""

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
            raise ComponentError(
                f"Component '{component}' is not present in this result."
            )
        shown = index if index else "scalar"
        raise ComponentError(
            f"Index {shown!r} does not identify a value of '{component}'."
        )


class CGE:
    """Configured static-CGE blueprint.

    ``CGE`` owns no solved model state.  Each :meth:`solve_benchmark` call
    creates a fresh legacy backend that is thereafter owned by the returned
    :class:`Equilibrium`.

    Args:
        model: engine-backed model-definition object exposing ``model()``.
        data: path-like data directory accepted by ``PyCGE.model_data``.
    """

    def __init__(self, model, data):
        self._model_definition = model
        self._data = data
        self._model_id = type(model).__name__

    def solve_benchmark(
        self,
        *,
        numeraire: Tuple[str, Any],
        redundant: Tuple[str, Any],
        solver: Optional[str] = None,
        solver_manager: Optional[str] = None,
    ) -> "Equilibrium":
        """Construct, close, solve, and snapshot the benchmark equilibrium.

        ``numeraire`` and ``redundant`` are the closure spelling of the
        engine-backed Hosoe family.  They are intentionally keyword-only and
        are not a promised universal closure interface for future backends.
        """
        if not isinstance(numeraire, tuple) or len(numeraire) != 2:
            raise ValueError("numeraire must be a (component, index) pair.")
        if not isinstance(redundant, tuple) or len(redundant) != 2:
            raise ValueError("redundant must be a (component, index) pair.")

        engine = PyCGE(self._model_definition)
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
        return Equilibrium(_engine=engine, _snapshot=snapshot)


@dataclass(frozen=True)
class Equilibrium:
    """Solved, protected benchmark equilibrium.

    ``frozen=True`` protects the public wrapper from rebinding.  The private
    legacy engine remains mutable by design so it can be deep-copied when a
    Scenario is created; public reads always come from the immutable snapshot.
    """

    _engine: PyCGE
    _snapshot: _Snapshot

    @property
    def objective(self) -> Optional[float]:
        return self._snapshot.objective

    def value(self, component: str, *index: Any) -> Optional[float]:
        """Read a variable or parameter value without traversing Pyomo."""
        return self._snapshot.value(component, *index)

    def scenario(self, name: str) -> "Scenario":
        """Create an isolated mutable counterfactual from this benchmark."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Scenario name must be a non-empty string.")

        # Whole-engine copying is deliberate in v0.6: it preserves all of
        # PyCGE's validated mutation/rollback logic while eliminating shared
        # access to its single ``sim`` slot.  A permanent test guards this
        # copyability contract against future Pyomo changes.
        engine = copy.deepcopy(self._engine)
        engine.model_sim()
        return Scenario(
            name=name.strip(),
            model_id=self._snapshot.model_id,
            engine=engine,
        )


class Scenario:
    """Independent mutable counterfactual derived from one benchmark."""

    def __init__(self, *, name: str, model_id: str, engine: PyCGE):
        self.name = name
        self._model_id = model_id
        self._engine = engine
        self._fixed_by_scenario: Set[Tuple[str, Any]] = set()

    def set(self, component: str, index: Any, new_value: Any) -> None:
        """Set a mutable parameter, or set-and-fix a variable, in this scenario."""
        model_component, _ = _component_item(
            self._engine.sim, component, index
        )
        self._engine.model_modify_sim(
            component, index, new_value, fix=True, undo=False
        )
        if model_component.ctype is Var:
            self._fixed_by_scenario.add(_scenario_key(component, index))

    def unfix(self, component: str, index: Any = None) -> None:
        """Release a variable previously fixed by :meth:`set` in this Scenario.

        Structurally exogenous quantities implemented as Pyomo ``Param``
        objects can be shocked with :meth:`set`, but cannot be endogenized by
        this facade.  That requires a model-definition/closure change and is
        deliberately outside v0.6.
        """
        model_component, item = _component_item(
            self._engine.sim, component, index
        )
        if model_component.ctype is Param:
            raise ComponentError(
                f"'{component}' is exogenous as a parameter in this model "
                "implementation; set() can change its value, but making it "
                "endogenous requires a model-definition change, not a "
                "scenario operation."
            )
        if model_component.ctype is not Var:
            raise ComponentError(f"'{component}' is not a variable.")

        key = _scenario_key(component, index)
        if key == self._engine.numeraire:
            raise ComponentError(
                f"{component}[{index}] is the benchmark numeraire and cannot "
                "be released by a scenario."
            )
        if key not in self._fixed_by_scenario:
            raise ComponentError(
                f"{component}[{index}] was not fixed by set() in this "
                "scenario; unfix() only releases variables previously fixed "
                "by this Scenario."
            )
        if not item.fixed:
            raise ComponentError(
                f"{component}[{index}] is already endogenous in this scenario."
            )

        # The legacy engine's fix=False path also accepts a value.  Passing
        # the current value preserves it exactly as the solver starting point.
        current = _number(item)
        self._engine.model_modify_sim(
            component, index, current, fix=False, undo=False
        )
        self._fixed_by_scenario.remove(key)

    def solve(
        self,
        *,
        solver: Optional[str] = None,
        solver_manager: Optional[str] = None,
    ) -> "Result":
        """Solve this scenario and return an immutable numerical snapshot."""
        dof = self._engine.degrees_of_freedom(self._engine.sim)
        if dof != 0:
            raise WorkflowError(
                "Scenario closure is incomplete: degrees of freedom = "
                f"{dof}; restore a square system before solve()."
            )

        self._engine.model_solve(solver=solver, mgr=solver_manager or "")
        snapshot = _Snapshot.from_instance(
            model_id=self._model_id,
            label=self.name,
            instance=self._engine.sim,
            results=self._engine.sim_results,
        )
        return Result(_snapshot=snapshot)


@dataclass(frozen=True)
class Result:
    """Immutable numerical snapshot of one successfully solved state."""

    _snapshot: _Snapshot

    @property
    def name(self) -> str:
        return self._snapshot.label

    @property
    def objective(self) -> Optional[float]:
        return self._snapshot.objective

    @property
    def solver(self) -> Mapping[str, Optional[str]]:
        return self._snapshot.solver

    def value(self, component: str, *index: Any) -> Optional[float]:
        """Read a variable or parameter value from this immutable snapshot."""
        return self._snapshot.value(component, *index)

    def compare(self, reference) -> pd.DataFrame:
        """Compare this solved result against an Equilibrium or another Result.

        Differences are always ``self - reference``.  Percentage change is
        ``difference / reference * 100`` and is NaN when the reference value
        is zero.  The default table compares solution variables only; model
        parameters remain available through :meth:`value`.  When selecting a
        single pandas Series row, use ``row["pct_change"]`` rather than
        attribute access because ``Series.pct_change`` is a pandas method.
        """
        if isinstance(reference, Equilibrium):
            other = reference._snapshot
        elif isinstance(reference, Result):
            other = reference._snapshot
        else:
            raise TypeError("reference must be an Equilibrium or Result.")

        if self._snapshot.model_id != other.model_id:
            raise WorkflowError(
                "Cannot compare results from different model definitions."
            )
        if set(self._snapshot.variables) != set(other.variables):
            raise WorkflowError(
                "Cannot compare structurally incompatible model results."
            )

        keys = sorted(
            self._snapshot.variables,
            key=lambda item: (item[0], repr(item[1])),
        )
        max_dims = max((len(index) for _, index in keys), default=0)
        rows = []
        for component, index in keys:
            current = self._snapshot.variables[(component, index)]
            base = other.variables[(component, index)]
            difference = None
            pct_change = None
            if current is not None and base is not None:
                difference = current - base
                pct_change = (
                    math.nan if base == 0 else difference / base * 100.0
                )
            row = {"component": component}
            for dimension in range(max_dims):
                row[f"index_{dimension + 1}"] = (
                    index[dimension] if dimension < len(index) else ""
                )
            row.update({
                "reference_value": base,
                "value": current,
                "difference": difference,
                "pct_change": pct_change,
            })
            rows.append(row)

        columns = (
            ["component"]
            + [f"index_{n + 1}" for n in range(max_dims)]
            + ["reference_value", "value", "difference", "pct_change"]
        )
        frame = pd.DataFrame(rows, columns=columns)
        if self.objective is None or other.objective is None:
            objective_difference = None
        else:
            objective_difference = self.objective - other.objective
        frame.attrs["objective"] = {
            "reference": other.objective,
            "value": self.objective,
            "difference": objective_difference,
        }
        return frame
