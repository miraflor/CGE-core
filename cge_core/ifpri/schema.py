# -*- coding: utf-8 -*-
"""Typed containers for the clean-room IFPRI data layer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Tuple


@dataclass(frozen=True)
class IfpriSets:
    """Account classifications declared in an IFPRI ``.dat`` file."""

    accounts: Tuple[str, ...]
    activities: Tuple[str, ...]
    agricultural_activities: Tuple[str, ...]
    commodities: Tuple[str, ...]
    agricultural_commodities: Tuple[str, ...]
    domestic_transaction_accounts: Tuple[str, ...]
    export_transaction_accounts: Tuple[str, ...]
    import_transaction_accounts: Tuple[str, ...]
    factors: Tuple[str, ...]
    labor_factors: Tuple[str, ...]
    land_factors: Tuple[str, ...]
    capital_factors: Tuple[str, ...]
    institutions: Tuple[str, ...]
    domestic_institutions: Tuple[str, ...]
    domestic_nongovernment_institutions: Tuple[str, ...]
    enterprises: Tuple[str, ...]
    households: Tuple[str, ...]


@dataclass(frozen=True)
class IfpriSam:
    """Parsed and scaled social accounting matrix."""

    table_name: str
    accounts: Tuple[str, ...]
    values: Mapping[Tuple[str, str], float]
    scale: float

    def value(self, row: str, column: str) -> float:
        """Return a SAM cell, treating an omitted GAMS table cell as zero."""
        return float(self.values.get((row, column), 0.0))

    def row_total(self, row: str) -> float:
        """Return the sum of ``row`` over active SAM accounts."""
        return sum(self.value(row, column) for column in self.accounts)

    def column_total(self, column: str) -> float:
        """Return the sum of ``column`` over active SAM accounts."""
        return sum(self.value(row, column) for row in self.accounts)

    def imbalance(self, account: str) -> float:
        """Return row total minus column total for one account."""
        return self.row_total(account) - self.column_total(account)

    def max_abs_imbalance(self) -> float:
        """Return the largest absolute account imbalance."""
        return max((abs(self.imbalance(a)) for a in self.accounts), default=0.0)


@dataclass(frozen=True)
class IfpriDataset:
    """Complete first-stage IFPRI dataset: sets plus benchmark SAM."""

    source_path: Path
    sets: IfpriSets
    sam: IfpriSam
