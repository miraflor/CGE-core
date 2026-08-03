# -*- coding: utf-8 -*-
"""Tests for IFPRI elasticities, home shares, factor data, and tax inputs."""
from __future__ import annotations

import pytest

from cge_core.ifpri import load_ifpri_test_data, validate_inputs


def test_trade_and_production_elasticities(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    e = dataset.inputs.elasticities

    assert e.armington["CAGR1"] == pytest.approx(0.8)
    assert e.armington["CAGR3-EX"] == 0.0
    assert e.transformation["CAGR3-EX"] == pytest.approx(1.6)
    assert e.transformation["CIMP"] == 0.0
    assert set(e.factor_substitution.values()) == {0.8}
    assert set(e.top_level_substitution.values()) == {0.6}
    assert set(e.output_aggregation.values()) == {6.0}


def test_household_demand_inputs(ifpri_source_dir):
    e = load_ifpri_test_data(ifpri_source_dir).inputs.elasticities

    assert e.market_expenditure[("CAGR1", "HURB")] == pytest.approx(1.10)
    assert e.market_expenditure[("CAGR1", "HRUR")] == pytest.approx(0.62)
    assert e.market_expenditure[("CIND", "HRUR")] == pytest.approx(1.35)
    assert set(e.frisch.values()) == {-2.0}
    assert set(e.home_expenditure.values()) == {1.0}


def test_home_consumption_value_shares(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    shares = dataset.inputs.home_consumption.value_shares

    assert shares[("AAGR1", "CAGR1", "HURB")] == pytest.approx(0.8)
    assert shares[("AAGR1", "CAGR2", "HURB")] == pytest.approx(0.2)
    assert shares[("AAGR1", "CAGR1", "HRUR")] == pytest.approx(0.2)
    assert shares[("AAGR1", "CAGR2", "HRUR")] == pytest.approx(0.8)
    assert shares[("AAGR2", "CAGR2", "HURB")] == pytest.approx(1.0)
    assert shares[("AIND", "CIND", "HRUR")] == pytest.approx(1.0)


def test_physical_factor_quantities_default_to_zero(ifpri_source_dir):
    q = load_ifpri_test_data(ifpri_source_dir).inputs.factor_quantities

    assert q.supply == {"LAB": 0.0, "CAP": 0.0}
    assert all(value == 0.0 for value in q.demand.values())
    assert len(q.demand) == 12


def test_tax_account_mapping_and_scaled_payments(ifpri_source_dir):
    taxes = load_ifpri_test_data(ifpri_source_dir).inputs.taxes

    assert taxes.source_accounts == {
        "INSTAX": "YTAX",
        "FACTAX": "YTAX",
        "IMPTAX": "TAR",
        "EXPTAX": "ETAX",
        "VATAX": "VATTAX",
        "ACTTAX": "ATAX",
        "COMTAX": "STAX",
    }
    assert taxes.payment("INSTAX", "HURB") == pytest.approx(0.199164269)
    assert taxes.payment("FACTAX", "LAB") == pytest.approx(0.034289066)
    assert taxes.payment("IMPTAX", "CIND") == pytest.approx(0.562985784)
    assert taxes.payment("EXPTAX", "CAGR1") == pytest.approx(0.051069114)
    assert taxes.payment("VATAX", "AAGR1") == pytest.approx(0.05090636)
    assert taxes.payment("ACTTAX", "AAGR1") == pytest.approx(-0.059695235)
    assert taxes.payment("COMTAX", "CIND") == pytest.approx(0.75755669)


def test_all_calibration_inputs_validate(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    validate_inputs(dataset.inputs, dataset.sets, dataset.sam)
