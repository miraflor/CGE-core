# -*- coding: utf-8 -*-
"""Tests for algebraic IFPRI benchmark calibration without a solver."""
from __future__ import annotations

import pytest

from cge_core.ifpri import (
    calibrate_ifpri_benchmark,
    load_ifpri_test_data,
    validate_ifpri_calibration,
)


@pytest.fixture
def calibrated(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    return dataset, calibrate_ifpri_benchmark(dataset)


def test_normalized_prices_match_reference_benchmark(calibrated):
    _, result = calibrated
    p = result.prices

    assert set(p.activity.values()) == {1.0}
    assert all(value == pytest.approx(1.0) for value in p.factor.values())
    assert p.domestic_demand["CAGR1"] == pytest.approx(1.2698620300)
    assert p.domestic_demand["CAGR2"] == pytest.approx(2.4179191938)
    assert p.composite["CIND"] == pytest.approx(1.2375746418)
    assert p.world_export["CAGR1"] == pytest.approx(1.50265152547)
    assert p.world_import["CIND"] == pytest.approx(0.82229997316)


def test_benchmark_quantities_match_reference_benchmark(calibrated):
    _, result = calibrated
    q = result.quantities

    assert q.activity["AAGR1"] == pytest.approx(2.851056167)
    assert q.value_added["AAGR1"] == pytest.approx(2.387889277)
    assert q.marketed_output["CAGR1"] == pytest.approx(1.49424361)
    assert q.domestic_sales["CAGR1"] == pytest.approx(1.295088442)
    assert q.exports["CAGR1"] == pytest.approx(0.199155168)
    assert q.imports["CIND"] == pytest.approx(7.52306531545)
    assert q.factor_supply == pytest.approx({"LAB": 9.177279758, "CAP": 6.367268554})


def test_factor_quantity_fallback_and_wage_normalization(calibrated):
    dataset, result = calibrated
    q, p = result.quantities, result.prices

    for factor in dataset.sets.factors:
        for activity in dataset.sets.activities:
            assert q.factor_demand[(factor, activity)] == pytest.approx(
                dataset.sam.value(factor, activity)
            )
            if dataset.sam.value(factor, activity):
                assert p.factor_activity[(factor, activity)] == pytest.approx(1.0)
        assert p.factor[factor] == pytest.approx(1.0)


def test_tax_and_institution_calibration(calibrated):
    _, result = calibrated

    assert result.taxes.activity["AAGR1"] == pytest.approx(-0.0209379372)
    assert result.taxes.import_["CIND"] == pytest.approx(0.0910064807)
    assert result.taxes.export["CAGR1"] == pytest.approx(0.1706508540)
    assert result.taxes.factor["LAB"] == pytest.approx(0.0037362995)
    assert result.institutions.savings_rate == pytest.approx({
        "ENT": 0.0247283066,
        "HURB": 0.1272796105,
        "HRUR": 0.0387663141,
    })
    assert result.institutions.government_income == pytest.approx(4.596411364)


def test_production_and_trade_functions_reproduce_benchmark(calibrated):
    dataset, result = calibrated
    validate_ifpri_calibration(dataset, result)

    assert result.production.factor_exponent["AAGR1"] == pytest.approx(0.25)
    assert result.production.output_exponent["CAGR1"] == pytest.approx(-5.0 / 6.0)
    assert result.production.armington_exponent["CIND"] == pytest.approx(0.25)
    assert result.production.cet_exponent["CAGR1"] == pytest.approx(1.625)


def test_les_calibration_reproduces_frisch_and_expenditure(calibrated):
    dataset, result = calibrated
    les = result.les

    for household in dataset.sets.households:
        assert les.implied_frisch[household] == pytest.approx(-2.0)
        assert sum(
            les.market_budget_share[(commodity, household)]
            for commodity in dataset.sets.commodities
        ) + sum(
            les.home_budget_share[(activity, commodity, household)]
            for activity in dataset.sets.activities
            for commodity in dataset.sets.commodities
        ) == pytest.approx(1.0)


def test_price_indices_and_macro_aggregates(calibrated):
    _, result = calibrated
    system = result.system

    assert system.consumer_price_index == pytest.approx(1.3062011183)
    assert system.domestic_price_index == pytest.approx(1.0)
    assert system.foreign_saving == pytest.approx(2.47396433)
    assert system.total_absorption == pytest.approx(22.345808739)
    assert system.investment_share == pytest.approx(0.1478878650)
    assert system.government_share == pytest.approx(0.2290417893)
    assert system.walras_residual == 0.0
