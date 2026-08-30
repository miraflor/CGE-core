# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
from pyomo.environ import value

from cge_core.models.ifpri import (
    IFPRI_POLICY_SCENARIOS,
    IfpriScenario,
    build_ifpri_scenario_model,
    compare_ifpri_model_to_reference,
    ifpri_degrees_of_freedom,
    load_ifpri_reference_targets,
    load_ifpri_test_data,
    normalize_ifpri_scenario,
    perturb_ifpri_start,
    solve_ifpri_scenario,
)
from .._util import SOLVER, requires_solver


@pytest.fixture(scope="module")
def dataset(ifpri_source_dir):
    return load_ifpri_test_data(ifpri_source_dir)


def _reference_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "validation"
        / "gams"
        / "ifpri_standard"
        / "reference"
        / "full_precision_targets.csv"
    )


def test_policy_scenario_catalog_matches_reference_names():
    assert tuple(item.value for item in IFPRI_POLICY_SCENARIOS) == (
        "TARCUT1",
        "TARCUT2",
        "FSAVINCR",
        "PWMINCR",
        "DEVAL",
    )
    assert normalize_ifpri_scenario("tarcut1") is IfpriScenario.TARCUT1


@pytest.mark.parametrize("scenario", IFPRI_POLICY_SCENARIOS)
def test_each_policy_closure_has_zero_degrees_of_freedom(dataset, scenario):
    model = build_ifpri_scenario_model(dataset, scenario)
    assert ifpri_degrees_of_freedom(model) == 0
    assert not model.WALRASSQR.fixed
    assert model.walras_objective.active
    assert model.IADJ.fixed
    assert model.GADJ.fixed
    assert model.QFS["LAB"].fixed
    assert model.WF["CAP"].fixed


@pytest.mark.parametrize("scenario", (IfpriScenario.TARCUT1, IfpriScenario.TARCUT2))
def test_tariff_scenarios_cut_benchmark_import_tax_rates_in_half(dataset, scenario):
    model = build_ifpri_scenario_model(dataset, scenario)
    base = model._ifpri_base_calibration
    for commodity in model.C:
        assert value(model.tm[commodity]) == pytest.approx(
            0.5 * base.taxes.import_[commodity]
        )


def test_foreign_savings_scenario_fixes_ten_percent_increase(dataset):
    model = build_ifpri_scenario_model(dataset, IfpriScenario.FSAVINCR)
    base = model._ifpri_base_calibration
    assert model.FSAV.fixed
    assert value(model.FSAV) == pytest.approx(1.1 * base.system.foreign_saving)
    assert model.CPI.fixed
    assert not model.EXR.fixed


def test_world_import_price_scenario_scales_prices_by_ten_percent(dataset):
    model = build_ifpri_scenario_model(dataset, IfpriScenario.PWMINCR)
    base = model._ifpri_base_calibration
    for commodity in model.C:
        assert value(model.pwm[commodity]) == pytest.approx(
            1.1 * base.prices.world_import[commodity]
        )


def test_second_tariff_scenario_uses_direct_tax_adjustment(dataset):
    model = build_ifpri_scenario_model(dataset, IfpriScenario.TARCUT2)
    base = model._ifpri_base_calibration
    assert model.GSAV.fixed
    assert value(model.GSAV) == pytest.approx(base.institutions.government_saving)
    assert not model.DTINS.fixed
    assert not model.direct_tax_definition.active
    assert model.adjusted_direct_tax_definition.active


def test_devaluation_switches_numeraire_and_external_balance_closure(dataset):
    model = build_ifpri_scenario_model(dataset, IfpriScenario.DEVAL)
    base = model._ifpri_base_calibration
    assert model.EXR.fixed
    assert value(model.EXR) == pytest.approx(1.1 * base.prices.exchange_rate)
    assert model.DPI.fixed
    assert value(model.DPI) == pytest.approx(base.system.domestic_price_index)
    assert not model.CPI.fixed
    assert not model.FSAV.fixed


@requires_solver
@pytest.mark.parametrize("scenario", IFPRI_POLICY_SCENARIOS)
def test_ipopt_reproduces_full_precision_gams_policy_scenario(
    dataset,
    scenario,
):
    model = build_ifpri_scenario_model(dataset, scenario)
    perturb_ifpri_start(model, 1.01)
    report = solve_ifpri_scenario(model, SOLVER)
    assert report.degrees_of_freedom == 0
    assert report.max_abs_equation_residual < 1e-6

    comparison = compare_ifpri_model_to_reference(
        model,
        load_ifpri_reference_targets(_reference_path(), "NLP", scenario.value),
    )
    assert comparison.compared_values > 400
    assert comparison.max_abs_difference < 2e-5
    assert comparison.max_relative_difference < 2e-6
