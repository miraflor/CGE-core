# -*- coding: utf-8 -*-
"""Public IFPRI coverage that never requires the official source package."""
from __future__ import annotations

import pytest
from pyomo.environ import value

from cge_core.models.ifpri import (
    IFPRI_POLICY_SCENARIOS,
    IfpriScenario,
    build_ifpri_base_solve_model,
    build_ifpri_benchmark_model,
    build_ifpri_scenario_model,
    calibrate_ifpri_benchmark,
    ifpri_degrees_of_freedom,
    solve_ifpri_base,
    solve_ifpri_scenario,
    validate_dataset,
    validate_ifpri_benchmark_model,
    validate_ifpri_calibration,
)
from .._util import SOLVER, requires_solver
from .synthetic import build_synthetic_ifpri_dataset

pytestmark = pytest.mark.public_ifpri


@pytest.fixture(scope="module")
def synthetic_dataset():
    return build_synthetic_ifpri_dataset()


def test_synthetic_dataset_balances_and_calibrates(synthetic_dataset):
    validate_dataset(synthetic_dataset)
    assert synthetic_dataset.sam.max_abs_imbalance() == pytest.approx(0.0)

    calibration = calibrate_ifpri_benchmark(synthetic_dataset)
    validate_ifpri_calibration(synthetic_dataset, calibration)
    assert calibration.quantities.imports["C"] == pytest.approx(7.7)
    assert calibration.quantities.imports["CIMP"] == pytest.approx(15.0)
    assert calibration.quantities.domestic_sales["CIMP"] == pytest.approx(0.0)
    assert calibration.quantities.exports["C"] == pytest.approx(10.0)
    assert calibration.quantities.exports["CEXP"] == pytest.approx(10.0)
    assert calibration.quantities.domestic_sales["CEXP"] == pytest.approx(0.0)
    assert calibration.quantities.imports["CEXP"] == pytest.approx(0.0)
    assert calibration.taxes.import_["C"] == pytest.approx(0.1)
    assert calibration.system.foreign_saving == pytest.approx(2.0)
    assert calibration.institutions.government_saving == pytest.approx(0.7)


def test_synthetic_benchmark_starts_on_all_equations(synthetic_dataset):
    model = build_ifpri_benchmark_model(synthetic_dataset)
    report = validate_ifpri_benchmark_model(model)
    assert report.equation_count > 40
    assert report.max_abs_residual < 1e-8


def test_synthetic_base_closure_has_zero_degrees_of_freedom(synthetic_dataset):
    model = build_ifpri_base_solve_model(synthetic_dataset)
    assert ifpri_degrees_of_freedom(model) == 0
    assert model.CPI.fixed
    assert model.FSAV.fixed
    assert not model.WALRASSQR.fixed
    assert model.walras_objective.active


@pytest.mark.parametrize("scenario", IFPRI_POLICY_SCENARIOS)
def test_synthetic_policy_closures_have_zero_degrees_of_freedom(
    synthetic_dataset,
    scenario,
):
    model = build_ifpri_scenario_model(synthetic_dataset, scenario)
    assert ifpri_degrees_of_freedom(model) == 0
    assert model._ifpri_scenario is scenario


def test_synthetic_tariff_and_macro_shocks_are_nonzero(synthetic_dataset):
    tariff = build_ifpri_scenario_model(synthetic_dataset, IfpriScenario.TARCUT1)
    assert value(tariff.tm["C"]) == pytest.approx(0.05)

    foreign_saving = build_ifpri_scenario_model(
        synthetic_dataset, IfpriScenario.FSAVINCR
    )
    assert value(foreign_saving.FSAV) == pytest.approx(2.2)

    world_price = build_ifpri_scenario_model(
        synthetic_dataset, IfpriScenario.PWMINCR
    )
    base = world_price._ifpri_base_calibration
    assert value(world_price.pwm["C"]) == pytest.approx(
        1.1 * base.prices.world_import["C"]
    )


@requires_solver
@pytest.mark.public_ifpri_solver
def test_synthetic_base_solves_with_real_nlp_solver(synthetic_dataset):
    model = build_ifpri_base_solve_model(synthetic_dataset)
    report = solve_ifpri_base(model, SOLVER)
    assert report.degrees_of_freedom == 0
    assert report.termination_condition in {"optimal", "locallyOptimal"}
    assert report.max_abs_equation_residual < 1e-7
    assert abs(value(model.WALRAS)) < 1e-7


@requires_solver
@pytest.mark.public_ifpri_solver
def test_synthetic_tariff_cut_solves_with_real_nlp_solver(synthetic_dataset):
    model = build_ifpri_scenario_model(synthetic_dataset, IfpriScenario.TARCUT1)
    report = solve_ifpri_scenario(model, SOLVER)
    assert report.degrees_of_freedom == 0
    assert report.termination_condition in {"optimal", "locallyOptimal"}
    assert report.max_abs_equation_residual < 1e-6
    assert abs(value(model.WALRAS)) < 1e-6
