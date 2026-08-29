# -*- coding: utf-8 -*-
"""Tabular extraction and comparison utilities for IFPRI model results."""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Optional, Tuple

import pandas as pd
from pyomo.environ import Var, value

from .scenarios import (
    IFPRI_SCENARIO_DESCRIPTIONS,
    ScenarioLike,
    normalize_ifpri_scenario,
)
from .solve import IfpriSolveReport
from .validation import IfpriDataError

_INDEX_COLUMNS = ("component", "index_1", "index_2", "index_3")
_SOLUTION_COLUMNS = ("scenario", *_INDEX_COLUMNS, "value", "fixed")
_COMPARISON_COLUMNS = (
    "scenario",
    *_INDEX_COLUMNS,
    "base_value",
    "scenario_value",
    "difference",
    "pct_change",
    "base_fixed",
    "scenario_fixed",
)
_SUMMARY_COLUMNS = (
    "scenario",
    "description",
    "solver",
    "status",
    "termination_condition",
    "degrees_of_freedom",
    "max_abs_equation_residual",
)


def _model_label(model, label: Optional[object] = None) -> str:
    """Return an explicit label or infer BASE/scenario from the model."""
    if label is None:
        scenario = getattr(model, "_ifpri_scenario", None)
        label = getattr(scenario, "value", "BASE")
    else:
        label = getattr(label, "value", label)
    text = str(label).strip().upper()
    if not text:
        raise IfpriDataError("An IFPRI solution label cannot be empty.")
    return text


def _selected_variables(model, components: Optional[Iterable[str]]):
    variables = list(model.component_objects(Var, active=True))
    by_name = {component.local_name.upper(): component for component in variables}
    if components is None:
        return variables

    requested = [components] if isinstance(components, str) else list(components)
    names = []
    for item in requested:
        name = str(item).strip().upper()
        if not name:
            raise IfpriDataError("IFPRI variable names cannot be empty.")
        if name not in names:
            names.append(name)
    if not names:
        raise IfpriDataError("Select at least one IFPRI variable component.")
    missing = [name for name in names if name not in by_name]
    if missing:
        raise IfpriDataError(f"Unknown IFPRI variable components: {missing}")
    return [by_name[name] for name in names]


def _index_parts(index) -> Tuple[str, str, str]:
    if index is None:
        parts = ()
    elif isinstance(index, tuple):
        parts = index
    else:
        parts = (index,)
    if len(parts) > 3:
        raise IfpriDataError(
            f"IFPRI reporting supports at most three indices, received {parts!r}."
        )
    text = tuple(str(item) for item in parts)
    return text + ("",) * (3 - len(text))


def extract_ifpri_solution(
    model,
    *,
    label: Optional[object] = None,
    components: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Return one long-form row for every selected active IFPRI variable.

    The returned columns are ``scenario``, ``component``, ``index_1`` through
    ``index_3``, ``value``, and ``fixed``. Scalar variables have blank index
    columns. All values must be initialized and finite so that an invalid solve
    missing or nonfinite model state cannot silently enter a report.
    """
    scenario = _model_label(model, label)
    rows = []
    for component in _selected_variables(model, components):
        entries = (
            component.items()
            if component.is_indexed()
            else ((None, component),)
        )
        for index, item in entries:
            raw = value(item, exception=False)
            if raw is None or not math.isfinite(float(raw)):
                raise IfpriDataError(
                    f"IFPRI variable {component.local_name}[{index}] "
                    f"has no finite reportable value: {raw!r}."
                )
            index_1, index_2, index_3 = _index_parts(index)
            rows.append(
                {
                    "scenario": scenario,
                    "component": component.local_name.upper(),
                    "index_1": index_1,
                    "index_2": index_2,
                    "index_3": index_3,
                    "value": float(raw),
                    "fixed": bool(item.fixed),
                }
            )

    frame = pd.DataFrame(rows, columns=_SOLUTION_COLUMNS)
    if not frame.empty:
        frame.sort_values(
            list(_INDEX_COLUMNS),
            kind="stable",
            inplace=True,
            ignore_index=True,
        )
    return frame


def compare_ifpri_models(
    base_model,
    scenario_model,
    *,
    scenario: Optional[object] = None,
    components: Optional[Iterable[str]] = None,
    zero_tolerance: float = 1e-12,
) -> pd.DataFrame:
    """Compare common variables as scenario minus BASE in a DataFrame.

    Percentage changes are undefined (``NaN``) where the absolute BASE value is
    no larger than ``zero_tolerance``. Variables that exist in only one model,
    such as a scenario-specific closure variable, remain available through
    :func:`extract_ifpri_solution` but are not included in this common-variable
    comparison.
    """
    if not math.isfinite(zero_tolerance) or zero_tolerance < 0.0:
        raise IfpriDataError(
            "IFPRI comparison zero_tolerance must be finite and nonnegative."
        )

    scenario_label = _model_label(scenario_model, scenario)
    base = extract_ifpri_solution(
        base_model,
        label="BASE",
        components=components,
    )
    counterfactual = extract_ifpri_solution(
        scenario_model,
        label=scenario_label,
        components=components,
    )

    left = base.drop(columns="scenario").rename(
        columns={"value": "base_value", "fixed": "base_fixed"}
    )
    right = counterfactual.drop(columns="scenario").rename(
        columns={"value": "scenario_value", "fixed": "scenario_fixed"}
    )
    frame = left.merge(
        right,
        on=list(_INDEX_COLUMNS),
        how="inner",
        validate="one_to_one",
    )
    if frame.empty:
        raise IfpriDataError(
            "The BASE and scenario models share no reportable variables."
        )

    frame.insert(0, "scenario", scenario_label)
    frame["difference"] = frame["scenario_value"] - frame["base_value"]
    frame["pct_change"] = float("nan")
    nonzero = frame["base_value"].abs() > zero_tolerance
    frame.loc[nonzero, "pct_change"] = (
        100.0
        * frame.loc[nonzero, "difference"]
        / frame.loc[nonzero, "base_value"]
    )
    return frame.loc[:, list(_COMPARISON_COLUMNS)]


def compare_ifpri_scenarios(
    base_model,
    results: Mapping[ScenarioLike, Tuple[object, IfpriSolveReport]],
    *,
    components: Optional[Iterable[str]] = None,
    zero_tolerance: float = 1e-12,
) -> pd.DataFrame:
    """Compare every result from ``build_and_solve_ifpri_scenarios`` to BASE."""
    frames = []
    for scenario, result in results.items():
        if not isinstance(result, tuple) or len(result) != 2:
            raise IfpriDataError(
                "Each IFPRI scenario result must be a (model, solve_report) tuple."
            )
        model, report = result
        if not isinstance(report, IfpriSolveReport):
            raise IfpriDataError(
                f"IFPRI scenario {scenario!r} has an invalid solve report."
            )
        frames.append(
            compare_ifpri_models(
                base_model,
                model,
                scenario=scenario,
                components=components,
                zero_tolerance=zero_tolerance,
            )
        )
    if not frames:
        return pd.DataFrame(columns=_COMPARISON_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def summarize_ifpri_results(
    results: Mapping[ScenarioLike, Tuple[object, IfpriSolveReport]],
) -> pd.DataFrame:
    """Return one solver-diagnostic row for every policy scenario result."""
    rows = []
    for scenario, result in results.items():
        selected = normalize_ifpri_scenario(scenario)
        if not isinstance(result, tuple) or len(result) != 2:
            raise IfpriDataError(
                "Each IFPRI scenario result must be a (model, solve_report) tuple."
            )
        _model, report = result
        if not isinstance(report, IfpriSolveReport):
            raise IfpriDataError(
                f"IFPRI scenario {selected.value} has an invalid solve report."
            )
        rows.append(
            {
                "scenario": selected.value,
                "description": IFPRI_SCENARIO_DESCRIPTIONS[selected],
                "solver": report.solver,
                "status": report.status,
                "termination_condition": report.termination_condition,
                "degrees_of_freedom": report.degrees_of_freedom,
                "max_abs_equation_residual": report.max_abs_equation_residual,
            }
        )
    return pd.DataFrame(rows, columns=_SUMMARY_COLUMNS)
