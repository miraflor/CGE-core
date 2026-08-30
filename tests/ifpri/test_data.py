# -*- coding: utf-8 -*-
"""Tests for the external IFPRI set and table parser."""
from __future__ import annotations

import pytest

from cge_core.models.ifpri import IfpriDataError, load_ifpri_test_data


def test_loads_external_test_dataset(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    assert dataset.source_path == ifpri_source_dir / "test.dat"
    assert dataset.sam.table_name == "TESTSAM"
    assert dataset.sam.scale == pytest.approx(0.1)


def test_detects_expected_account_classes(ifpri_source_dir):
    sets = load_ifpri_test_data(ifpri_source_dir).sets
    assert sets.activities == (
        "AAGR1", "AAGR2", "AAGR3-EX", "AIND", "ATTRA", "AOSER"
    )
    assert sets.commodities == (
        "CAGR1", "CAGR2", "CAGR3-EX", "CIND", "CTTRA", "COSER", "CIMP"
    )
    assert sets.factors == ("LAB", "CAP")
    assert sets.labor_factors == ("LAB",)
    assert sets.land_factors == ()
    assert sets.capital_factors == ("CAP",)
    assert sets.enterprises == ("ENT",)
    assert sets.households == ("HURB", "HRUR")


def test_detects_transaction_accounts(ifpri_source_dir):
    sets = load_ifpri_test_data(ifpri_source_dir).sets
    assert sets.domestic_transaction_accounts == ("TRNSC-D",)
    assert sets.export_transaction_accounts == ("TRNSC-E",)
    assert sets.import_transaction_accounts == ("TRNSC-M",)


def test_missing_source_directory_is_rejected(tmp_path):
    with pytest.raises(IfpriDataError, match="not found"):
        load_ifpri_test_data(tmp_path / "missing")
