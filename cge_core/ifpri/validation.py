# -*- coding: utf-8 -*-
"""Validation rules for the clean-room IFPRI data layer."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, Sequence

from .schema import IfpriDataset, IfpriSam, IfpriSets


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


def validate_dataset(dataset: IfpriDataset,
                     balance_tolerance: float = 1e-7) -> None:
    """Run all first-stage structural checks."""
    require_source_file(dataset.source_path)
    validate_sets(dataset.sets)
    validate_sam(dataset.sam, dataset.sets.accounts, balance_tolerance)
