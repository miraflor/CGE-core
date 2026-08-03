# -*- coding: utf-8 -*-
"""Validation rules for the clean-room IFPRI data layer."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .schema import (
    IfpriCalibrationInputs,
    IfpriDataset,
    IfpriSam,
    IfpriSets,
)


class IfpriDataError(ValueError):
    """Raised when an IFPRI source file is missing or structurally invalid."""


def require_source_file(path: Path) -> Path:
    """Validate that ``path`` is an existing regular file."""
    if not path.exists():
        raise IfpriDataError(f"IFPRI data file not found: {path}")
    if not path.is_file():
        raise IfpriDataError(f"IFPRI data path is not a file: {path}")
    return path


def _require_unique(name: str, members: Sequence[str]) -> None:
    duplicates = sorted({member for member in members if members.count(member) > 1})
    if duplicates:
        raise IfpriDataError(f"Set {name} contains duplicate members: {duplicates}")


def _require_subset(name: str, members: Iterable[str], parent_name: str,
                    parent: Iterable[str]) -> None:
    parent_set = set(parent)
    missing = sorted(set(members) - parent_set)
    if missing:
        raise IfpriDataError(
            f"Set {name} contains members not present in {parent_name}: {missing}"
        )


def validate_sets(sets: IfpriSets) -> None:
    """Validate uniqueness and the key IFPRI set-subset relationships."""
    fields = {
        "AC": sets.accounts,
        "A": sets.activities,
        "AAGR": sets.agricultural_activities,
        "C": sets.commodities,
        "CAGR": sets.agricultural_commodities,
        "CTD": sets.domestic_transaction_accounts,
        "CTE": sets.export_transaction_accounts,
        "CTM": sets.import_transaction_accounts,
        "F": sets.factors,
        "FLAB": sets.labor_factors,
        "FLND": sets.land_factors,
        "FCAP": sets.capital_factors,
        "INS": sets.institutions,
        "INSD": sets.domestic_institutions,
        "INSDNG": sets.domestic_nongovernment_institutions,
        "EN": sets.enterprises,
        "H": sets.households,
    }
    for name, members in fields.items():
        _require_unique(name, members)

    if not sets.accounts:
        raise IfpriDataError("Set AC is empty.")
    if not sets.activities:
        raise IfpriDataError("Set A is empty.")
    if not sets.commodities:
        raise IfpriDataError("Set C is empty.")
    if not sets.factors:
        raise IfpriDataError("Set F is empty.")

    _require_subset("A", sets.activities, "AC", sets.accounts)
    _require_subset("AAGR", sets.agricultural_activities, "A", sets.activities)
    _require_subset("C", sets.commodities, "AC", sets.accounts)
    _require_subset("CAGR", sets.agricultural_commodities, "C", sets.commodities)
    _require_subset("CTD", sets.domestic_transaction_accounts, "AC", sets.accounts)
    _require_subset("CTE", sets.export_transaction_accounts, "AC", sets.accounts)
    _require_subset("CTM", sets.import_transaction_accounts, "AC", sets.accounts)
    _require_subset("F", sets.factors, "AC", sets.accounts)
    _require_subset("FLAB", sets.labor_factors, "F", sets.factors)
    _require_subset("FLND", sets.land_factors, "F", sets.factors)
    _require_subset("FCAP", sets.capital_factors, "F", sets.factors)
    _require_subset("INS", sets.institutions, "AC", sets.accounts)
    _require_subset("INSD", sets.domestic_institutions, "INS", sets.institutions)
    _require_subset(
        "INSDNG",
        sets.domestic_nongovernment_institutions,
        "INSD",
        sets.domestic_institutions,
    )
    _require_subset(
        "EN", sets.enterprises, "INSDNG", sets.domestic_nongovernment_institutions
    )
    _require_subset(
        "H", sets.households, "INSDNG", sets.domestic_nongovernment_institutions
    )


def validate_sam(sam: IfpriSam, declared_accounts: Iterable[str],
                 balance_tolerance: float = 1e-7) -> None:
    """Validate SAM dimensions, numeric cells, account membership and balance."""
    if not sam.accounts:
        raise IfpriDataError("The parsed SAM has no active accounts.")
    if len(set(sam.accounts)) != len(sam.accounts):
        raise IfpriDataError("The parsed SAM account list contains duplicates.")

    undeclared = sorted(set(sam.accounts) - set(declared_accounts))
    if undeclared:
        raise IfpriDataError(
            f"SAM accounts not declared in set AC: {undeclared}"
        )

    account_set = set(sam.accounts)
    for (row, column), value in sam.values.items():
        if row not in account_set or column not in account_set:
            raise IfpriDataError(
                f"SAM cell ({row}, {column}) lies outside the active SAM accounts."
            )
        if not math.isfinite(value):
            raise IfpriDataError(
                f"SAM cell ({row}, {column}) is not finite: {value!r}"
            )

    max_gap = sam.max_abs_imbalance()
    if max_gap > balance_tolerance:
        raise IfpriDataError(
            "SAM is not balanced within tolerance: "
            f"max absolute imbalance={max_gap:.12g}, "
            f"tolerance={balance_tolerance:.12g}."
        )


def _require_finite_mapping(name: str, values: Mapping[object, float]) -> None:
    for key, value in values.items():
        if not math.isfinite(value):
            raise IfpriDataError(f"{name}{key!r} is not finite: {value!r}")


def validate_inputs(inputs: IfpriCalibrationInputs, sets: IfpriSets,
                    sam: IfpriSam, tolerance: float = 1e-10) -> None:
    """Validate calibration-input coverage, ranges, shares, and tax mappings."""
    e = inputs.elasticities
    expected_c = set(sets.commodities)
    expected_a = set(sets.activities)
    expected_h = set(sets.households)

    for name, mapping, expected in (
        ("armington", e.armington, expected_c),
        ("transformation", e.transformation, expected_c),
        ("factor_substitution", e.factor_substitution, expected_a),
        ("top_level_substitution", e.top_level_substitution, expected_a),
        ("output_aggregation", e.output_aggregation, expected_c),
        ("frisch", e.frisch, expected_h),
    ):
        if set(mapping) != expected:
            raise IfpriDataError(f"{name} coverage does not match its declared set.")
        _require_finite_mapping(name, mapping)

    expected_market = {(c, h) for c in sets.commodities for h in sets.households}
    if set(e.market_expenditure) != expected_market:
        raise IfpriDataError("Market LES elasticity coverage is incomplete.")
    expected_home = {
        (a, c, h)
        for a in sets.activities
        for c in sets.commodities
        for h in sets.households
    }
    if set(e.home_expenditure) != expected_home:
        raise IfpriDataError("Home LES elasticity coverage is incomplete.")
    _require_finite_mapping("market_expenditure", e.market_expenditure)
    _require_finite_mapping("home_expenditure", e.home_expenditure)

    if any(value <= 0.0 for value in e.market_expenditure.values()):
        raise IfpriDataError("Market expenditure elasticities must be positive.")
    if any(value >= 0.0 for value in e.frisch.values()):
        raise IfpriDataError("Frisch parameters must be negative.")

    for activity in sets.activities:
        for household in sets.households:
            home_value = sam.value(activity, household)
            shares = sum(
                inputs.home_consumption.value_shares.get(
                    (activity, commodity, household), 0.0
                )
                for commodity in sets.commodities
            )
            if home_value != 0.0 and abs(shares - 1.0) > tolerance:
                raise IfpriDataError(
                    f"SHRHOME shares for ({activity}, {household}) sum to "
                    f"{shares:.12g}, not one."
                )
            if home_value == 0.0 and abs(shares) > tolerance:
                raise IfpriDataError(
                    f"SHRHOME has shares for inactive pair ({activity}, {household})."
                )

    expected_supply = set(sets.factors)
    if set(inputs.factor_quantities.supply) != expected_supply:
        raise IfpriDataError("Physical factor-supply coverage is incomplete.")
    expected_demand = {(f, a) for f in sets.factors for a in sets.activities}
    if set(inputs.factor_quantities.demand) != expected_demand:
        raise IfpriDataError("Physical factor-demand coverage is incomplete.")

    for tax_type, source in inputs.taxes.source_accounts.items():
        if source not in sam.accounts:
            raise IfpriDataError(
                f"Tax type {tax_type} refers to missing SAM account {source}."
            )
    _require_finite_mapping("tax_payment", inputs.taxes.payments)


def validate_dataset(dataset: IfpriDataset,
                     balance_tolerance: float = 1e-7) -> None:
    """Run all structural, accounting, and calibration-input checks."""
    require_source_file(dataset.source_path)
    validate_sets(dataset.sets)
    validate_sam(dataset.sam, dataset.sets.accounts, balance_tolerance)
    validate_inputs(dataset.inputs, dataset.sets, dataset.sam)
