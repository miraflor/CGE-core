# -*- coding: utf-8 -*-
"""Independently authored redistributable IFPRI-format test economy.

This fixture is not copied or derived from the official IFPRI test dataset.
It is a deliberately small balanced SAM constructed for public unit and CI
coverage of calibration, model construction, closures, and NLP solving.
"""
from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Mapping, TypeVar

from cge_core.ifpri import (
    IfpriCalibrationInputs,
    IfpriDataset,
    IfpriElasticities,
    IfpriFactorQuantities,
    IfpriHomeConsumption,
    IfpriSam,
    IfpriSets,
    IfpriTaxData,
    validate_dataset,
)

_K = TypeVar("_K")


def _frozen(values: Mapping[_K, float]) -> Mapping[_K, float]:
    return MappingProxyType(dict(values))


def build_synthetic_ifpri_dataset() -> IfpriDataset:
    """Return a compact balanced economy with trade, saving, and a tariff."""
    accounts = (
        "A",
        "C",
        "CIMP",
        "CEXP",
        "LAB",
        "CAP",
        "HH",
        "GOV",
        "S-I",
        "DSTK",
        "TAXM",
        "ROW",
    )
    sets = IfpriSets(
        accounts=accounts,
        activities=("A",),
        agricultural_activities=(),
        commodities=("C", "CIMP", "CEXP"),
        agricultural_commodities=(),
        domestic_transaction_accounts=(),
        export_transaction_accounts=(),
        import_transaction_accounts=(),
        factors=("LAB", "CAP"),
        labor_factors=("LAB",),
        land_factors=(),
        capital_factors=("CAP",),
        institutions=("HH", "GOV", "ROW"),
        domestic_institutions=("HH", "GOV"),
        domestic_nongovernment_institutions=("HH",),
        enterprises=(),
        households=("HH",),
    )

    # Rows receive and columns spend. Every account balances exactly.
    sam_values = _frozen({
        ("A", "C"): 90.0,
        ("A", "CEXP"): 10.0,
        ("C", "A"): 20.0,
        ("LAB", "A"): 40.0,
        ("CAP", "A"): 40.0,
        ("C", "HH"): 55.0,
        ("CIMP", "HH"): 5.0,
        ("S-I", "HH"): 10.0,
        ("HH", "LAB"): 35.0,
        ("GOV", "LAB"): 5.0,
        ("HH", "CAP"): 35.0,
        ("GOV", "CAP"): 5.0,
        ("C", "GOV"): 10.0,
        ("S-I", "GOV"): 0.7,
        ("GOV", "TAXM"): 0.7,
        ("TAXM", "C"): 0.7,
        ("ROW", "C"): 7.0,
        ("ROW", "CIMP"): 15.0,
        ("C", "ROW"): 10.0,
        ("CEXP", "ROW"): 10.0,
        ("S-I", "ROW"): 2.0,
        ("C", "S-I"): 2.7,
        ("CIMP", "S-I"): 10.0,
    })
    sam = IfpriSam(
        table_name="SYNTHETIC_SAM",
        accounts=accounts,
        values=sam_values,
        scale=1.0,
    )

    elasticities = IfpriElasticities(
        armington=_frozen({"C": 2.0, "CIMP": 2.0, "CEXP": 2.0}),
        transformation=_frozen({"C": 2.0, "CIMP": 2.0, "CEXP": 2.0}),
        factor_substitution=_frozen({"A": 2.0}),
        top_level_substitution=_frozen({"A": 1.0}),
        output_aggregation=_frozen({"C": 2.0, "CIMP": 2.0, "CEXP": 2.0}),
        market_expenditure=_frozen({
            ("C", "HH"): 1.0,
            ("CIMP", "HH"): 1.0,
            ("CEXP", "HH"): 1.0,
        }),
        home_expenditure=_frozen({
            ("A", "C", "HH"): 1.0,
            ("A", "CIMP", "HH"): 1.0,
            ("A", "CEXP", "HH"): 1.0,
        }),
        frisch=_frozen({"HH": -2.0}),
    )
    factor_quantities = IfpriFactorQuantities(
        supply=_frozen({"LAB": 0.0, "CAP": 0.0}),
        demand=_frozen({("LAB", "A"): 0.0, ("CAP", "A"): 0.0}),
    )
    home_consumption = IfpriHomeConsumption(value_shares=_frozen({}))
    taxes = IfpriTaxData(
        source_accounts=MappingProxyType({"IMPTAX": "TAXM"}),
        payments=_frozen({("IMPTAX", "C"): 0.7}),
    )
    inputs = IfpriCalibrationInputs(
        elasticities=elasticities,
        factor_quantities=factor_quantities,
        home_consumption=home_consumption,
        taxes=taxes,
    )
    dataset = IfpriDataset(
        source_path=Path(__file__).resolve(),
        sets=sets,
        sam=sam,
        inputs=inputs,
    )
    validate_dataset(dataset)
    return dataset
