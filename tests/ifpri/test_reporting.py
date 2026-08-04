# -*- coding: utf-8 -*-
"""Public tests for IFPRI tabular result extraction and reporting."""
from __future__ import annotations

import math

import pytest

from cge_core.ifpri import (
    IFPRI_SCENARIO_DESCRIPTIONS,
    IfpriDataError,
    IfpriScenario,
    IfpriSolveReport,
    build_ifpri_base_solve_model,
    build_ifpri_scenario_model,
    compare_ifpri_models,
    compare_ifpri_scenarios,
    extract_ifpri_solution,
    summarize_ifpri_results,
)
from .synthetic import build_synthetic_ifpri_dataset

pytestmark = pytest.mark.public_ifpri


@pytest.fixture(scope="module")
def synthetic_dataset():
    return build_synthetic_ifpri_dataset()


@pytest.fixture(scope="module")
def base_model(synthetic_dataset):
    return build_ifpri_base_solve_model(synthetic_dataset)


@pytest.fixture(scope="module")
def devaluation_model(synthetic_dataset):
    return build_ifpri_scenario_model(synthetic_dataset, IfpriScenario.DEVAL)


def _report() -> IfpriSolveReport:
    return IfpriSolveReport(
        solver="ipopt",
        status="ok",
        termination_condition="optimal",
        degrees_of_freedom=0,
        max_abs_equation_residual=1e-10,
    )


def test_extract_solution_has_stable_long_form_schema(base_model):
    frame = extract_ifpri_solution(
        base_model,
        components=("EXR", "QA"),
    )
    assert list(frame.columns) == [
        "scenario",
        "component",
        "index_1",
        "index_2",
        "index_3",
        "value",
        "fixed",
    ]
    assert set(frame["scenario"]) == {"BASE"}
    assert set(frame["component"]) == {"EXR", "QA"}

    exr = frame.loc[frame["component"] == "EXR"].iloc[0]
    assert exr["index_1"] == ""
    assert exr["value"] == pytest.approx(1.0)
    assert not bool(exr["fixed"])


def test_extract_solution_rejects_unknown_component(base_model):
    with pytest.raises(IfpriDataError, match="Unknown IFPRI variable"):
        extract_ifpri_solution(base_model, components=("NOT_A_VARIABLE",))


def test_compare_models_reports_scenario_minus_base(
    base_model,
    devaluation_model,
):
    frame = compare_ifpri_models(
        base_model,
        devaluation_model,
        components=("EXR", "CPI"),
    )
    exr = frame.loc[frame["component"] == "EXR"].iloc[0]
    assert exr["scenario"] == "DEVAL"
    assert exr["base_value"] == pytest.approx(1.0)
    assert exr["scenario_value"] == pytest.approx(1.1)
    assert exr["difference"] == pytest.approx(0.1)
    assert exr["pct_change"] == pytest.approx(10.0)


def test_zero_base_value_has_undefined_percentage_change(
    base_model,
    devaluation_model,
):
    base_model.WALRAS.set_value(0.0)
    devaluation_model.WALRAS.set_value(0.0)
    frame = compare_ifpri_models(
        base_model,
        devaluation_model,
        components=("WALRAS",),
    )
    assert math.isnan(frame.iloc[0]["pct_change"])


def test_multi_scenario_comparison_and_summary(
    synthetic_dataset,
    base_model,
    devaluation_model,
):
    tariff_model = build_ifpri_scenario_model(
        synthetic_dataset,
        IfpriScenario.TARCUT1,
    )
    results = {
        IfpriScenario.TARCUT1: (tariff_model, _report()),
        IfpriScenario.DEVAL: (devaluation_model, _report()),
    }

    comparisons = compare_ifpri_scenarios(
        base_model,
        results,
        components=("EXR",),
    )
    assert set(comparisons["scenario"]) == {"TARCUT1", "DEVAL"}

    summary = summarize_ifpri_results(results)
    assert list(summary["scenario"]) == ["TARCUT1", "DEVAL"]
    deval = summary.loc[summary["scenario"] == "DEVAL"].iloc[0]
    assert deval["description"] == IFPRI_SCENARIO_DESCRIPTIONS[
        IfpriScenario.DEVAL
    ]
    assert deval["degrees_of_freedom"] == 0
    assert deval["max_abs_equation_residual"] == pytest.approx(1e-10)
