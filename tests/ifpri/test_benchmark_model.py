# -*- coding: utf-8 -*-
"""Tests for the initialized Pyomo IFPRI benchmark equation system."""
from __future__ import annotations

import pytest
from pyomo.environ import Constraint, Var, value

from cge_core.ifpri import (
    IfpriDataError,
    build_ifpri_benchmark_model,
    calibrate_ifpri_benchmark,
    ifpri_benchmark_residuals,
    load_ifpri_test_data,
    summarize_ifpri_benchmark_residuals,
    validate_ifpri_benchmark_model,
)


@pytest.fixture
def benchmark_model(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    calibration = calibrate_ifpri_benchmark(dataset)
    return dataset, calibration, build_ifpri_benchmark_model(dataset, calibration)


def test_builder_creates_real_pyomo_variables_and_constraints(benchmark_model):
    _, _, model = benchmark_model

    assert isinstance(model.QA, Var)
    assert isinstance(model.pm_definition, Constraint)
    assert len(tuple(model.component_data_objects(Var))) > 0
    assert len(tuple(model.component_data_objects(Constraint, active=True))) == 213


def test_variables_start_at_the_algebraic_benchmark(benchmark_model):
    dataset, calibration, model = benchmark_model

    assert value(model.CPI) == pytest.approx(calibration.system.consumer_price_index)
    assert value(model.TABS) == pytest.approx(calibration.system.total_absorption)
    assert value(model.QA["AAGR1"]) == pytest.approx(
        calibration.quantities.activity["AAGR1"]
    )
    assert value(model.PQ["CIND"]) == pytest.approx(
        calibration.prices.composite["CIND"]
    )
    assert value(model.YI["HURB"]) == pytest.approx(
        calibration.institutions.institution_income["HURB"]
    )
    assert set(model.A) == set(dataset.sets.activities)


def test_all_initialized_equations_reproduce_benchmark(benchmark_model):
    _, _, model = benchmark_model
    report = validate_ifpri_benchmark_model(model)

    assert report.equation_count == 213
    assert report.max_abs_residual < 1e-8
    assert report.worst_equation
    assert set(report.group_max_abs_residual) == {
        "price", "production_trade", "institution", "system"
    }
    assert max(report.group_max_abs_residual.values()) < 1e-8


def test_residual_mapping_covers_every_active_constraint(benchmark_model):
    _, _, model = benchmark_model
    residuals = ifpri_benchmark_residuals(model)

    assert len(residuals) == 213
    assert "cpi_definition" in residuals
    assert "current_account_balance" in residuals
    assert any(name.startswith("ces_value_added_foc[") for name in residuals)
    assert any(name.startswith("market_household_demand[") for name in residuals)
    assert all(abs(residual) < 1e-8 for residual in residuals.values())


def test_residual_validator_detects_a_perturbed_variable(benchmark_model):
    _, _, model = benchmark_model
    model.QA["AAGR1"].set_value(value(model.QA["AAGR1"]) * 1.01)

    report = summarize_ifpri_benchmark_residuals(model)
    assert report.max_abs_residual > 1e-4
    with pytest.raises(IfpriDataError, match="residual is too large"):
        validate_ifpri_benchmark_model(model)


def test_builder_does_not_call_or_require_a_solver(benchmark_model):
    _, _, model = benchmark_model

    assert not hasattr(model, "solutions_loaded")
    report = validate_ifpri_benchmark_model(model)
    assert report.equation_count == 213
