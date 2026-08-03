# -*- coding: utf-8 -*-
"""Structural and accounting tests for the parsed IFPRI benchmark SAM."""
from __future__ import annotations

import pytest

from cge_core.ifpri import load_ifpri_test_data, validate_dataset


def test_sam_is_square_and_has_expected_size(ifpri_source_dir):
    sam = load_ifpri_test_data(ifpri_source_dir).sam
    assert len(sam.accounts) == 30
    assert "TOTAL" not in sam.accounts
    assert set(row for row, _ in sam.values) <= set(sam.accounts)
    assert set(column for _, column in sam.values) <= set(sam.accounts)


def test_selected_scaled_cells_match_source(ifpri_source_dir):
    sam = load_ifpri_test_data(ifpri_source_dir).sam
    assert sam.value("CAGR1", "AAGR1") == pytest.approx(0.065313567)
    assert sam.value("LAB", "AAGR1") == pytest.approx(2.013177894)
    assert sam.value("GOV", "YTAX") == pytest.approx(0.617104362)
    assert sam.value("CAGR3-EX", "ROW") == pytest.approx(0.557952599)
    assert sam.value("AAGR1", "AAGR1") == 0.0


def test_sam_balances_within_source_precision(ifpri_source_dir):
    sam = load_ifpri_test_data(ifpri_source_dir).sam
    assert sam.max_abs_imbalance() <= 3e-9


def test_dataset_passes_full_first_stage_validation(ifpri_source_dir):
    dataset = load_ifpri_test_data(ifpri_source_dir)
    validate_dataset(dataset, balance_tolerance=3e-9)
