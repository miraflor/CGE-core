"""v0.7 public-engine adapter over the validated PyCGE engine.

The inherited equations and lower-level v0.6 PyCGE API remain untouched.
This adapter changes extension semantics: benchmark protection is explicit
metadata, and solver choice is delegated to cge_core.solvers.
"""
from __future__ import annotations

import logging
import math
from typing import Any

from pyomo.environ import Param, Var, value

from cge_core.compat.pycge import ComponentError, PyCGE, WorkflowError
from cge_core.model_spec import ModelSpec
from cge_core.solver import SolverResolutionError, resolve_solver

logger = logging.getLogger(__name__)


def _component_key(name: str, index: Any):
    try:
        hash(index)
        safe_index = index
    except TypeError:
        safe_index = repr(index)
    return name, safe_index


class CoreEngine(PyCGE):
    """PyCGE-compatible engine with the v0.7 explicit metadata contract."""

    def __init__(self, model_def, spec: ModelSpec):
        super().__init__(model_def)
        self.model_spec = spec

    @staticmethod
    def _available_solver(preferred=None):
        try:
            return resolve_solver(preferred)
        except SolverResolutionError as exc:
            from cge_core.compat.pycge import SolveError
            raise SolveError(str(exc)) from exc

    def _modify(self, *, base: bool, name, index, new_value, fix=True, undo=False):
        """v0.7 mutation logic with explicit protection metadata only."""
        instance = self.base if base else self.sim
        history = self.dict_base if base else self.dict_sim
        label = "BASE" if base else "SIM"
        if instance is None:
            first = ("base instance. Call `model_instance` first." if base
                     else "sim instance. Call `model_sim` first.")
            raise WorkflowError("Must first create " + first)

        component = instance.component(name)
        if component is None:
            raise ComponentError(f"'{name}' does not exist in the current instance.")
        if component.ctype not in (Var, Param):
            raise ComponentError(f"'{name}' is not a variable or mutable parameter.")
        if component.ctype is Param and not component.mutable:
            raise ComponentError(f"'{name}' is immutable and cannot be modified.")

        try:
            item = self._data_item(component, index)
        except (KeyError, TypeError) as exc:
            raise ComponentError(f"'{index}' is not an index of '{name}'.") from exc

        if name in self.model_spec.benchmark_only or (
            base and name in self.model_spec.base_protected
        ):
            scope = "BASE" if base else "SIM"
            raise ComponentError(
                f"{scope} component '{name}' is declared benchmark/base-protected "
                "by this model and cannot be modified in-place."
            )

        key = _component_key(name, index)
        if undo:
            original = history.get(key)
            if original is None:
                raise ComponentError(f"No stored original value for {name}[{index}].")
            prior_value = value(item, exception=False)
            prior_fixed = bool(item.fixed) if component.ctype is Var else None
            try:
                item.set_value(original["value"])
                if component.ctype is Var:
                    item.fix() if original["fixed"] else item.unfix()
            except Exception:
                try:
                    item.set_value(prior_value)
                    if component.ctype is Var:
                        item.fix() if prior_fixed else item.unfix()
                except Exception:
                    logger.exception("Failed to roll back undo for %s[%s].", name, index)
                raise
            del history[key]
        else:
            if component.ctype is Var and not fix and key == self.numeraire:
                raise ComponentError(
                    f"{name}[{index}] is the numeraire and cannot be unfixed."
                )
            try:
                numeric = float(new_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"VALUE for {name}[{index}] must be a finite numeric scalar."
                ) from exc
            if not math.isfinite(numeric):
                raise ValueError(
                    f"VALUE for {name}[{index}] must be a finite numeric scalar."
                )

            prior_value = value(item, exception=False)
            prior_fixed = bool(item.fixed) if component.ctype is Var else None
            added_history = key not in history
            try:
                if component.ctype is Var:
                    lb = value(item.lb, exception=False)
                    ub = value(item.ub, exception=False)
                    if lb is not None and numeric < lb:
                        raise ValueError(f"value {numeric} is below lower bound {lb}")
                    if ub is not None and numeric > ub:
                        raise ValueError(f"value {numeric} is above upper bound {ub}")
                if added_history:
                    history[key] = {"value": prior_value, "fixed": prior_fixed}
                item.set_value(numeric)
                if component.ctype is Var:
                    item.fix() if fix else item.unfix()
            except Exception:
                try:
                    item.set_value(prior_value)
                    if component.ctype is Var:
                        item.fix() if prior_fixed else item.unfix()
                except Exception:
                    logger.exception(
                        "Failed to roll back %s[%s] after rejected modification.",
                        name, index,
                    )
                if added_history:
                    history.pop(key, None)
                raise

        if base:
            self._invalidate_base_solution()
        else:
            self.sim_results = None
            self.sim_solved = False
        logger.info("%s updated.", label)
        return True
