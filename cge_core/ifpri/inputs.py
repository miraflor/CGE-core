# -*- coding: utf-8 -*-
"""Parse the non-SAM inputs used to calibrate the IFPRI benchmark model."""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from .schema import (
    IfpriCalibrationInputs,
    IfpriElasticities,
    IfpriFactorQuantities,
    IfpriHomeConsumption,
    IfpriSam,
    IfpriSets,
    IfpriTaxData,
)
from .validation import IfpriDataError

_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?"


def _uniform_assignment(clean_text: str, name: str, domain: str) -> float:
    """Read an assignment such as ``PRODELAS(A) = 0.8;``."""
    match = re.search(
        rf"(?mi)^\s*{re.escape(name)}\s*\(\s*{re.escape(domain)}\s*\)"
        rf"\s*=\s*({_NUMBER})\s*;",
        clean_text,
    )
    if match is None:
        raise IfpriDataError(
            f"Required assignment {name}({domain}) was not found."
        )
    return float(match.group(1))


def _trade_elasticity(clean_text: str, elasticity_name: str) -> float:
    """Read the constant assigned to one conditional trade elasticity."""
    match = re.search(
        rf"(?mi)^\s*TRADELAS\s*\(\s*C\s*,\s*'{re.escape(elasticity_name)}'\s*\)"
        rf"[^=]*=\s*({_NUMBER})\s*;",
        clean_text,
    )
    if match is None:
        raise IfpriDataError(
            f"Required TRADELAS value {elasticity_name} was not found."
        )
    return float(match.group(1))


def _table_lines(clean_text: str, table_name: str) -> List[str]:
    """Return one GAMS table body, ending at ``;`` or the next comment block."""
    declaration = re.search(
        rf"(?mi)^\s*TABLE\s+{re.escape(table_name)}\s*\([^)]*\)[^\n]*\n",
        clean_text,
    )
    if declaration is None:
        raise IfpriDataError(f"Required table {table_name} was not found.")

    lines: List[str] = []
    data_started = False
    for line in clean_text[declaration.end():].splitlines():
        stripped = line.strip()
        if stripped == ";":
            break
        if data_started and line.startswith("*"):
            break
        if data_started and re.match(
                r"(?i)^\s*(?:TABLE|PARAMETERS?|SETS?|DISPLAY)\b", line):
            break
        if stripped:
            data_started = True
            lines.append(line)
    if not lines:
        raise IfpriDataError(f"Table {table_name} has no data rows.")
    return lines


def _dense_two_dimensional_table(
        clean_text: str, table_name: str
) -> Tuple[Tuple[str, ...], Dict[Tuple[str, str], float]]:
    """Parse a table with a simple row key and one value for every column."""
    lines = _table_lines(clean_text, table_name)
    headers = tuple(lines[0].split())
    values: Dict[Tuple[str, str], float] = {}
    for line in lines[1:]:
        tokens = line.split()
        if not tokens:
            continue
        row = tokens[0]
        numeric = tokens[1:]
        if len(numeric) != len(headers):
            raise IfpriDataError(
                f"Table {table_name} row {row} has {len(numeric)} values; "
                f"expected {len(headers)}."
            )
        for column, raw in zip(headers, numeric):
            try:
                values[(row, column)] = float(raw)
            except ValueError as exc:
                raise IfpriDataError(
                    f"Non-numeric value {raw!r} in table {table_name}."
                ) from exc
    return headers, values


def _home_share_table(
        clean_text: str, table_name: str
) -> Tuple[Tuple[str, ...], Dict[Tuple[str, str, str], float]]:
    """Parse ``SHRHOME`` whose row labels are ``activity.commodity`` pairs."""
    headers, two_dimensional = _dense_two_dimensional_table(clean_text, table_name)
    values: Dict[Tuple[str, str, str], float] = {}
    for (row, household), value in two_dimensional.items():
        if "." not in row:
            raise IfpriDataError(
                f"Table {table_name} row {row!r} is not activity.commodity."
            )
        activity, commodity = row.split(".", 1)
        values[(activity, commodity, household)] = value
    return headers, values


def _tax_sources(clean_text: str) -> Dict[str, Tuple[str, str]]:
    """Map each tax type to its SAM collection account and domain set."""
    pattern = re.compile(
        r"(?mi)^\s*TAXPAR\s*\(\s*'(?P<tax>[A-Z]+)'\s*,\s*(?P<domain>[A-Z]+)\s*\)"
        r"\s*=\s*SAM\s*\(\s*'(?P<source>[^']+)'\s*,\s*(?P=domain)\s*\)\s*;"
    )
    result = {
        match.group("tax"): (match.group("source"), match.group("domain"))
        for match in pattern.finditer(clean_text)
    }
    required = {"INSTAX", "FACTAX", "IMPTAX", "EXPTAX", "VATAX", "ACTTAX", "COMTAX"}
    missing = sorted(required - set(result))
    if missing:
        raise IfpriDataError(f"Missing TAXPAR mappings: {missing}")
    return result


def _domain_members(sets: IfpriSets, domain: str) -> Sequence[str]:
    domains: Mapping[str, Sequence[str]] = {
        "INSD": sets.domestic_institutions,
        "F": sets.factors,
        "C": sets.commodities,
        "A": sets.activities,
    }
    try:
        return domains[domain]
    except KeyError as exc:
        raise IfpriDataError(f"Unsupported TAXPAR domain {domain!r}.") from exc


def parse_calibration_inputs(
        clean_text: str, sets: IfpriSets, sam: IfpriSam
) -> IfpriCalibrationInputs:
    """Parse all exogenous inputs needed before algebraic calibration."""
    sigma_q = _trade_elasticity(clean_text, "SIGMAQ")
    sigma_t = _trade_elasticity(clean_text, "SIGMAT")
    factor_sigma = _uniform_assignment(clean_text, "PRODELAS", "A")
    top_sigma = _uniform_assignment(clean_text, "PRODELAS2", "A")
    output_sigma = _uniform_assignment(clean_text, "ELASAC", "C")
    frisch_value = _uniform_assignment(clean_text, "FRISCH", "H")
    home_elasticity = _uniform_assignment(clean_text, "LESELAS2", "A,C,H")
    factor_demand_default = _uniform_assignment(clean_text, "QFBASE", "F,A")

    les_headers, les_market = _dense_two_dimensional_table(clean_text, "LESELAS1")
    if set(les_headers) != set(sets.households):
        raise IfpriDataError(
            "LESELAS1 household columns do not match set H: "
            f"columns={list(les_headers)}, H={list(sets.households)}."
        )

    share_headers, share_values = _home_share_table(clean_text, "SHRHOME")
    if set(share_headers) != set(sets.households):
        raise IfpriDataError(
            "SHRHOME household columns do not match set H: "
            f"columns={list(share_headers)}, H={list(sets.households)}."
        )

    elasticities = IfpriElasticities(
        armington={
            commodity: sigma_q if sam.value("ROW", commodity) != 0.0 else 0.0
            for commodity in sets.commodities
        },
        transformation={
            commodity: sigma_t if sam.value(commodity, "ROW") != 0.0 else 0.0
            for commodity in sets.commodities
        },
        factor_substitution={activity: factor_sigma for activity in sets.activities},
        top_level_substitution={activity: top_sigma for activity in sets.activities},
        output_aggregation={commodity: output_sigma for commodity in sets.commodities},
        market_expenditure={
            (commodity, household): les_market[(commodity, household)]
            for commodity in sets.commodities
            for household in sets.households
        },
        home_expenditure={
            (activity, commodity, household): home_elasticity
            for activity in sets.activities
            for commodity in sets.commodities
            for household in sets.households
        },
        frisch={household: frisch_value for household in sets.households},
    )

    factor_quantities = IfpriFactorQuantities(
        supply={factor: 0.0 for factor in sets.factors},
        demand={
            (factor, activity): factor_demand_default
            for factor in sets.factors
            for activity in sets.activities
        },
    )
    home_consumption = IfpriHomeConsumption(value_shares=share_values)

    source_specs = _tax_sources(clean_text)
    source_accounts = {tax: source for tax, (source, _) in source_specs.items()}
    payments: Dict[Tuple[str, str], float] = {}
    for tax, (source, domain) in source_specs.items():
        for account in _domain_members(sets, domain):
            payments[(tax, account)] = sam.value(source, account)
    taxes = IfpriTaxData(source_accounts=source_accounts, payments=payments)

    return IfpriCalibrationInputs(
        elasticities=elasticities,
        factor_quantities=factor_quantities,
        home_consumption=home_consumption,
        taxes=taxes,
    )
