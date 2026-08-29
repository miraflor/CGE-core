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
class IfpriElasticities:
    """Trade, production, and household-demand elasticities."""

    armington: Mapping[str, float]
    transformation: Mapping[str, float]
    factor_substitution: Mapping[str, float]
    top_level_substitution: Mapping[str, float]
    output_aggregation: Mapping[str, float]
    market_expenditure: Mapping[Tuple[str, str], float]
    home_expenditure: Mapping[Tuple[str, str, str], float]
    frisch: Mapping[str, float]


@dataclass(frozen=True)
class IfpriFactorQuantities:
    """Optional physical factor supply and activity-demand quantities."""

    supply: Mapping[str, float]
    demand: Mapping[Tuple[str, str], float]


@dataclass(frozen=True)
class IfpriHomeConsumption:
    """Commodity value shares for household home consumption."""

    value_shares: Mapping[Tuple[str, str, str], float]


@dataclass(frozen=True)
class IfpriTaxData:
    """Tax-account mapping and benchmark tax payments extracted from the SAM."""

    source_accounts: Mapping[str, str]
    payments: Mapping[Tuple[str, str], float]

    def payment(self, tax_type: str, account: str) -> float:
        """Return a benchmark tax payment, with omitted cells treated as zero."""
        return float(self.payments.get((tax_type, account), 0.0))


@dataclass(frozen=True)
class IfpriCalibrationInputs:
    """All non-SAM inputs needed by the benchmark calibration stage."""

    elasticities: IfpriElasticities
    factor_quantities: IfpriFactorQuantities
    home_consumption: IfpriHomeConsumption
    taxes: IfpriTaxData


@dataclass(frozen=True)
class IfpriDataset:
    """Parsed IFPRI benchmark data and calibration inputs."""

    source_path: Path
    sets: IfpriSets
    sam: IfpriSam
    inputs: IfpriCalibrationInputs


@dataclass(frozen=True)
class IfpriBenchmarkPrices:
    """Benchmark prices implied by the SAM normalization."""

    exchange_rate: float
    activity: Mapping[str, float]
    activity_commodity: Mapping[Tuple[str, str], float]
    value_added: Mapping[str, float]
    intermediate_aggregate: Mapping[str, float]
    marketed_output: Mapping[str, float]
    domestic_supply: Mapping[str, float]
    domestic_demand: Mapping[str, float]
    export: Mapping[str, float]
    import_: Mapping[str, float]
    composite: Mapping[str, float]
    world_export: Mapping[str, float]
    world_import: Mapping[str, float]
    factor: Mapping[str, float]
    factor_activity: Mapping[Tuple[str, str], float]


@dataclass(frozen=True)
class IfpriBenchmarkQuantities:
    """Benchmark quantities reconstructed from values and normalized prices."""

    activity: Mapping[str, float]
    value_added: Mapping[str, float]
    activity_commodity: Mapping[Tuple[str, str], float]
    home_consumption: Mapping[Tuple[str, str, str], float]
    marketed_output: Mapping[str, float]
    domestic_sales: Mapping[str, float]
    exports: Mapping[str, float]
    imports: Mapping[str, float]
    composite_supply: Mapping[str, float]
    factor_demand: Mapping[Tuple[str, str], float]
    factor_supply: Mapping[str, float]
    intermediate: Mapping[Tuple[str, str], float]
    intermediate_aggregate: Mapping[str, float]
    transaction_demand: Mapping[str, float]
    household_market: Mapping[Tuple[str, str], float]
    government: Mapping[str, float]
    investment: Mapping[str, float]
    stock_change: Mapping[str, float]


@dataclass(frozen=True)
class IfpriProductionCalibration:
    """Calibrated production, output-aggregation, and trade parameters."""

    value_added_coefficient: Mapping[str, float]
    intermediate_coefficient: Mapping[str, float]
    intermediate_shares: Mapping[Tuple[str, str], float]
    yield_coefficient: Mapping[Tuple[str, str], float]
    factor_exponent: Mapping[str, float]
    factor_shares: Mapping[Tuple[str, str], float]
    factor_scale: Mapping[str, float]
    output_exponent: Mapping[str, float]
    output_shares: Mapping[Tuple[str, str], float]
    output_scale: Mapping[str, float]
    armington_exponent: Mapping[str, float]
    armington_share: Mapping[str, float]
    armington_scale: Mapping[str, float]
    cet_exponent: Mapping[str, float]
    cet_share: Mapping[str, float]
    cet_scale: Mapping[str, float]
    transaction_domestic: Mapping[Tuple[str, str], float]
    transaction_import: Mapping[Tuple[str, str], float]
    transaction_export: Mapping[Tuple[str, str], float]


@dataclass(frozen=True)
class IfpriTaxCalibration:
    """Benchmark ad-valorem tax rates."""

    activity: Mapping[str, float]
    value_added: Mapping[str, float]
    commodity: Mapping[str, float]
    import_: Mapping[str, float]
    export: Mapping[str, float]
    factor: Mapping[str, float]
    institution: Mapping[str, float]


@dataclass(frozen=True)
class IfpriInstitutionCalibration:
    """Institutional benchmark incomes, shares, transfers, and savings."""

    institution_income: Mapping[str, float]
    factor_income: Mapping[str, float]
    institution_factor_income: Mapping[Tuple[str, str], float]
    factor_income_share: Mapping[Tuple[str, str], float]
    interinstitution_share: Mapping[Tuple[str, str], float]
    savings_rate: Mapping[str, float]
    household_expenditure: Mapping[str, float]
    government_income: float
    government_expenditure: float
    government_saving: float


@dataclass(frozen=True)
class IfpriLesCalibration:
    """Linear-expenditure-system benchmark parameters and checks."""

    market_budget_share: Mapping[Tuple[str, str], float]
    home_budget_share: Mapping[Tuple[str, str, str], float]
    normalized_market_elasticity: Mapping[Tuple[str, str], float]
    normalized_home_elasticity: Mapping[Tuple[str, str, str], float]
    market_marginal_share: Mapping[Tuple[str, str], float]
    home_marginal_share: Mapping[Tuple[str, str, str], float]
    market_subsistence: Mapping[Tuple[str, str], float]
    home_subsistence: Mapping[Tuple[str, str, str], float]
    supernumerary_income: Mapping[str, float]
    implied_frisch: Mapping[str, float]


@dataclass(frozen=True)
class IfpriSystemCalibration:
    """Savings-investment and price-index benchmark aggregates."""

    consumer_price_weights: Mapping[str, float]
    domestic_price_weights: Mapping[str, float]
    consumer_price_index: float
    domestic_price_index: float
    foreign_saving: float
    total_absorption: float
    investment_share: float
    government_share: float
    walras_residual: float


@dataclass(frozen=True)
class IfpriBenchmarkCalibration:
    """Complete algebraic calibration of the supplied benchmark, without solve."""

    prices: IfpriBenchmarkPrices
    quantities: IfpriBenchmarkQuantities
    production: IfpriProductionCalibration
    taxes: IfpriTaxCalibration
    institutions: IfpriInstitutionCalibration
    les: IfpriLesCalibration
    system: IfpriSystemCalibration
