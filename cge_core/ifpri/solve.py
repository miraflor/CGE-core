# -*- coding: utf-8 -*-
"""Apply the official IFPRI BASE closure and solve the benchmark with IPOPT."""
from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple, Union

from pyomo.environ import (
    Constraint,
    NonNegativeReals,
    Objective,
    SolverFactory,
    Var,
    minimize,
    value,
)
from pyomo.opt import SolverStatus, TerminationCondition

from .model import build_ifpri_benchmark_model, validate_ifpri_benchmark_model
from .schema import IfpriBenchmarkCalibration, IfpriDataset
from .validation import IfpriDataError

PathLike = Union[str, Path]
_POSITIVE_FLOOR = 1e-10
_OPTIMAL_TERMINATIONS = {
    TerminationCondition.optimal,
    TerminationCondition.locallyOptimal,
    getattr(
        TerminationCondition,
        "globallyOptimal",
        TerminationCondition.optimal,
    ),
}


@dataclass(frozen=True)
class IfpriSolveReport:
    solver: str
    status: str
    termination_condition: str
    degrees_of_freedom: int
    max_abs_equation_residual: float


@dataclass(frozen=True)
class IfpriReferenceComparison:
    compared_values: int
    max_abs_difference: float
    max_relative_difference: float
    worst_absolute: str
    worst_relative: str
    differences: Mapping[str, float]


def _fix_inactive(component, active_members, fixed_value: float = 0.0) -> None:
    """Fix structurally inactive entries at their GAMS level convention."""
    active = set(active_members)
    for index, item in component.items():
        if index not in active:
            item.fix(fixed_value)


def apply_ifpri_base_closure(model) -> None:
    """Apply the active BASE closure recorded for the official test model."""
    # Variables that are structurally absent from the benchmark model.
    _fix_inactive(model.PDD, model.CD)
    _fix_inactive(model.PDS, model.CD)
    _fix_inactive(model.PE, model.CE)
    # GAMS initializes PM.L(C)=1 for every commodity.  The pure-export
    # commodity is outside CM, so its import price is economically inactive
    # but remains at the reporting convention 1 rather than zero.
    _fix_inactive(model.PM, model.CM, 1.0)
    _fix_inactive(model.PX, model.CX)
    _fix_inactive(model.PXAC, model.QXAC_ACTIVE)
    _fix_inactive(model.QD, model.CD)
    _fix_inactive(model.QE, model.CE)
    _fix_inactive(model.QG, model.QG_ACTIVE)
    _fix_inactive(model.QH, model.QH_ACTIVE)
    _fix_inactive(model.QHA, model.QHA_ACTIVE)
    _fix_inactive(model.QINT, model.QINT_ACTIVE)
    _fix_inactive(model.QINV, model.QINV_ACTIVE)
    _fix_inactive(model.QM, model.CM)
    _fix_inactive(model.QQ, model.CQ)
    _fix_inactive(model.QT, model.CT)
    _fix_inactive(model.QX, model.CX)
    _fix_inactive(model.QXAC, model.QXAC_ACTIVE)
    _fix_inactive(model.TRII, model.TRII_ACTIVE)
    _fix_inactive(model.YIF, model.YIF_ACTIVE)

    cal = model._ifpri_calibration
    # Macro closure: CPI numeraire; fixed foreign savings, investment and
    # government demand; flexible exchange rate, government saving and DMPS.
    model.CPI.fix(cal.system.consumer_price_index)
    model.FSAV.fix(cal.system.foreign_saving)
    model.IADJ.fix(1.0)
    model.GADJ.fix(1.0)

    # The official NLP formulation does not impose WALRAS = 0 as an extra
    # equality.  It leaves WALRAS free, defines WALRASSQR = WALRAS**2, and
    # minimizes WALRASSQR.  Fixing WALRAS while retaining every equilibrium
    # equation makes the NLP overdetermined from IPOPT's perspective.
    model.WALRAS.unfix()
    if not hasattr(model, "WALRASSQR"):
        model.WALRASSQR = Var(
            domain=NonNegativeReals,
            initialize=cal.system.walras_residual ** 2,
        )
    if not hasattr(model, "walras_squared_definition"):
        model.walras_squared_definition = Constraint(
            expr=model.WALRASSQR == model.WALRAS ** 2
        )
    if not hasattr(model, "walras_objective"):
        model.walras_objective = Objective(
            expr=model.WALRASSQR,
            sense=minimize,
        )

    # Labor is mobile and fully employed.
    for f in model._ifpri_dataset.sets.labor_factors:
        model.QFS[f].fix(cal.quantities.factor_supply[f])
        for a in model.A:
            model.WFDIST[f, a].fix(cal.prices.factor_activity[(f, a)])

    # Capital is activity-specific and fully employed.
    for f in model._ifpri_dataset.sets.capital_factors:
        model.WF[f].fix(cal.prices.factor[f])
        for a in model.A:
            model.QF[f, a].fix(cal.quantities.factor_demand[(f, a)])

    _set_safe_bounds(model)
    dof = ifpri_degrees_of_freedom(model)
    if dof != 0:
        raise IfpriDataError(f"IFPRI BASE closure has {dof} degrees of freedom; expected 0.")


def _set_safe_bounds(model) -> None:
    positive_components = (
        "EXR", "PA", "PXAC", "PVA", "PINTA", "PX", "PDS", "PDD",
        "PE", "PM", "PQ", "WF", "WFDIST", "CPI", "DPI", "QA", "QVA",
        "QINTA", "QXAC", "QHA", "QX", "QD", "QE", "QM", "QQ", "QF",
        "QFS", "QINT", "QT", "QH", "QG", "QINV", "YF", "YIF", "YI",
        "TRII", "EH", "YG", "EG", "TABS", "INVSHR", "GOVSHR",
    )
    for name in positive_components:
        component = getattr(model, name)
        items = component.values() if component.is_indexed() else (component,)
        for item in items:
            if not item.fixed and value(item, exception=False) is not None and value(item) > 0:
                item.setlb(_POSITIVE_FLOOR)


def build_ifpri_base_solve_model(
    dataset: IfpriDataset,
    calibration: Optional[IfpriBenchmarkCalibration] = None,
):
    model = build_ifpri_benchmark_model(dataset, calibration)
    validate_ifpri_benchmark_model(model)
    apply_ifpri_base_closure(model)
    return model


def ifpri_degrees_of_freedom(model) -> int:
    """Return closure degrees of freedom after accounting for the objective.

    The official NLP has one optimization degree: WALRAS is free and
    WALRASSQR is minimized subject to WALRASSQR = WALRAS**2.  Counting the
    active scalar objective as the final closure condition therefore yields
    zero closure degrees of freedom while leaving IPOPT a valid NLP with one
    more free variable than equality constraints.
    """
    free = sum(
        1
        for item in model.component_data_objects(Var, active=True)
        if not item.fixed
    )
    equations = sum(
        1 for _ in model.component_data_objects(Constraint, active=True)
    )
    objectives = sum(
        1 for _ in model.component_data_objects(Objective, active=True)
    )
    return free - equations - objectives


def perturb_ifpri_start(model, factor: float = 1.02) -> None:
    """Move every free nonzero variable away from the benchmark start."""
    if factor <= 0 or math.isclose(factor, 1.0):
        raise ValueError("factor must be positive and different from 1")
    for item in model.component_data_objects(Var, active=True):
        if item.fixed:
            continue
        current = value(item, exception=False)
        if current is None or abs(current) < 1e-14:
            continue
        candidate = current * factor
        if item.lb is not None:
            candidate = max(candidate, float(value(item.lb)) * 1.01)
        if item.ub is not None:
            candidate = min(candidate, float(value(item.ub)) * 0.99)
        item.set_value(candidate)


def _choose_solver(name: Optional[str]) -> str:
    candidates = (name,) if name else ("ipopt", "cyipopt")
    for candidate in candidates:
        if not candidate:
            continue
        try:
            if SolverFactory(candidate).available(exception_flag=False):
                return candidate
        except Exception:
            pass
    requested = name or "ipopt/cyipopt"
    raise IfpriDataError(f"No usable local NLP solver was found ({requested}).")


def _solve_label(model) -> str:
    """Return BASE or the attached scenario name for solver diagnostics."""
    scenario = getattr(model, "_ifpri_scenario", None)
    return getattr(scenario, "value", "BASE")


def _is_successful_termination(status, termination) -> bool:
    """Return whether a solver result is optimal enough for replication."""
    return (
        status in {SolverStatus.ok, SolverStatus.warning}
        and termination in _OPTIMAL_TERMINATIONS
    )


def _constraint_residual(data) -> float:
    """Return signed equality residual or signed bound violation."""
    body = float(value(data.body))
    if data.equality:
        return body - float(value(data.lower))

    if data.lower is not None:
        lower = float(value(data.lower))
        if body < lower:
            return body - lower
    if data.upper is not None:
        upper = float(value(data.upper))
        if body > upper:
            return body - upper
    return 0.0


def solve_ifpri_base(
    model,
    solver: Optional[str] = None,
    tee: bool = False,
) -> IfpriSolveReport:
    """Solve a closed IFPRI model and require an optimal termination."""
    if ifpri_degrees_of_freedom(model) != 0:
        raise IfpriDataError(
            "The IFPRI model must have zero degrees of freedom before solving."
        )
    label = _solve_label(model)
    solver_name = _choose_solver(solver)
    opt = SolverFactory(solver_name)
    if solver_name == "ipopt":
        opt.options["tol"] = 1e-10
        opt.options["constr_viol_tol"] = 1e-9
        opt.options["max_iter"] = 3000
    try:
        result = opt.solve(model, tee=tee)
    except Exception as exc:
        raise IfpriDataError(
            f"IFPRI {label} solve raised {type(exc).__name__}: {exc}"
        ) from exc

    status = result.solver.status
    termination = result.solver.termination_condition
    if not _is_successful_termination(status, termination):
        raise IfpriDataError(
            f"IFPRI {label} solve failed: "
            f"status={status}; termination={termination}."
        )

    residuals = {}
    for component in model.component_objects(Constraint, active=True):
        entries = (
            component.items()
            if component.is_indexed()
            else ((None, component),)
        )
        for index, data in entries:
            residuals[f"{component.name}[{index}]"] = _constraint_residual(data)
    max_residual = max((abs(v) for v in residuals.values()), default=0.0)
    return IfpriSolveReport(
        solver=solver_name,
        status=str(status),
        termination_condition=str(termination),
        degrees_of_freedom=ifpri_degrees_of_freedom(model),
        max_abs_equation_residual=max_residual,
    )


def load_ifpri_reference_targets(
    path: PathLike,
    solver: str = "NLP",
    scenario: str = "BASE",
) -> Dict[Tuple[str, Tuple[str, ...]], float]:
    targets: Dict[Tuple[str, Tuple[str, ...]], float] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row["solver"].upper() != solver.upper() or row["scenario"].upper() != scenario.upper():
                continue
            index = tuple(row[key] for key in ("index1", "index2", "index3") if row[key])
            targets[(row["symbol"], index)] = float(row["value"])
    if not targets:
        raise IfpriDataError(f"No {solver}/{scenario} targets were found in {path}.")
    return targets


def compare_ifpri_model_to_reference(model, targets) -> IfpriReferenceComparison:
    diffs: Dict[str, float] = {}
    rels: Dict[str, float] = {}
    for component in model.component_objects(Var, active=True):
        symbol = component.local_name.upper()
        entries = component.items() if component.is_indexed() else ((None, component),)
        for index, item in entries:
            if index is None:
                key_index: Tuple[str, ...] = ()
            elif isinstance(index, tuple):
                key_index = tuple(str(x) for x in index)
            else:
                key_index = (str(index),)
            key = (symbol, key_index)
            if key not in targets:
                continue
            actual = float(value(item))
            expected = targets[key]
            label = symbol + ("[" + ",".join(key_index) + "]" if key_index else "")
            diff = abs(actual - expected)
            diffs[label] = diff
            rels[label] = diff / max(1.0, abs(expected))
    if not diffs:
        raise IfpriDataError("No Pyomo variables matched the reference target table.")
    worst_abs = max(diffs, key=diffs.get)
    worst_rel = max(rels, key=rels.get)
    return IfpriReferenceComparison(
        compared_values=len(diffs),
        max_abs_difference=diffs[worst_abs],
        max_relative_difference=rels[worst_rel],
        worst_absolute=worst_abs,
        worst_relative=worst_rel,
        differences=MappingProxyType(diffs),
    )
