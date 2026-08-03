# -*- coding: utf-8 -*-
"""Read the IFPRI Standard CGE test dataset without bundling its source.

The loader reads a user-supplied ``test.dat`` from ``IFPRI_SOURCE_DIR`` or
from an explicitly supplied directory. It extracts only the declared account
sets and the benchmark social accounting matrix needed for the first clean-room
implementation milestone. It does not execute GAMS and does not copy the IFPRI
source file into CGE-Core.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .schema import IfpriDataset, IfpriSam, IfpriSets
from .validation import IfpriDataError, require_source_file, validate_dataset

PathLike = Union[str, Path]

_SET_NAMES = (
    "AC", "A", "AAGR", "C", "CAGR", "CTD", "CTE", "CTM", "F",
    "FLAB", "FLND", "FCAP", "INS", "INSD", "INSDNG", "EN", "H",
)
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?")


def _strip_gams_comments(text: str) -> str:
    """Remove line comments and ``$ontext``/``$offtext`` blocks."""
    output: List[str] = []
    in_text_block = False
    for line in text.splitlines():
        marker = line.strip().lower()
        if marker.startswith("$ontext"):
            in_text_block = True
            continue
        if marker.startswith("$offtext"):
            in_text_block = False
            continue
        if in_text_block or line.lstrip().startswith("*"):
            continue
        output.append(line)
    return "\n".join(output)


def _extract_set(clean_text: str, name: str) -> Tuple[str, ...]:
    """Extract the members between the slash delimiters of one GAMS set."""
    pattern = re.compile(
        rf"(?ms)^\s*{re.escape(name)}(?:\([^)]*\))?\b"
        rf"[^\n]*?(?:\n\s*)?/\s*(.*?)\s*/"
    )
    match = pattern.search(clean_text)
    if match is None:
        raise IfpriDataError(f"Required set {name} was not found in the data file.")

    members: List[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped:
            members.append(stripped.split()[0])
    return tuple(members)


def _table_body(clean_text: str, table_name: str) -> str:
    declaration = re.search(
        rf"(?mi)^\s*TABLE\s+{re.escape(table_name)}\s*\([^)]*\)[^\n]*\n",
        clean_text,
    )
    if declaration is None:
        raise IfpriDataError(f"Required table {table_name} was not found.")
    remainder = clean_text[declaration.end():]
    terminator = re.search(r"(?m)^\s*;\s*$", remainder)
    if terminator is None:
        raise IfpriDataError(f"Table {table_name} has no terminating semicolon.")
    return remainder[:terminator.start()]


def _extract_gams_table(clean_text: str, table_name: str) -> Tuple[
        Tuple[str, ...], Tuple[str, ...], Dict[Tuple[str, str], float]]:
    """Parse a fixed-width, possibly multi-block GAMS ``TABLE``.

    GAMS aligns each numeric value's right edge with its column heading's
    right edge. Using those endpoints preserves blank cells without relying on
    a fixed field width.
    """
    body = _table_body(clean_text, table_name)
    current_columns: List[str] = []
    current_ends: List[int] = []
    rows: List[str] = []
    columns: List[str] = []
    values: Dict[Tuple[str, str], float] = {}

    for line in body.splitlines():
        if not line.strip():
            continue

        if line[0].isspace():
            tokens = [token for token in re.finditer(r"\S+", line)
                      if token.group() != "+"]
            if not tokens:
                continue
            current_columns = [token.group() for token in tokens]
            current_ends = [token.end() for token in tokens]
            for column in current_columns:
                if column not in columns:
                    columns.append(column)
            continue

        if not current_columns:
            raise IfpriDataError(
                f"Encountered a row in {table_name} before a column heading."
            )

        tokens = list(re.finditer(r"\S+", line))
        row = tokens[0].group()
        if row not in rows:
            rows.append(row)

        for token in tokens[1:]:
            raw_value = token.group()
            if _NUMBER.fullmatch(raw_value) is None:
                raise IfpriDataError(
                    f"Unexpected token {raw_value!r} in table {table_name}."
                )
            nearest = min(
                range(len(current_ends)),
                key=lambda index: abs(current_ends[index] - token.end()),
            )
            if abs(current_ends[nearest] - token.end()) > 2:
                raise IfpriDataError(
                    f"Could not align value {raw_value!r} in row {row} "
                    f"with a column of table {table_name}."
                )
            values[(row, current_columns[nearest])] = float(raw_value)

    if set(rows) != set(columns):
        missing_rows = sorted(set(columns) - set(rows))
        missing_columns = sorted(set(rows) - set(columns))
        raise IfpriDataError(
            f"Table {table_name} is not square. Missing rows={missing_rows}; "
            f"missing columns={missing_columns}."
        )
    return tuple(rows), tuple(columns), values


def _infer_sam_scale(clean_text: str, table_name: str) -> float:
    """Read a scalar assignment such as ``SAM = 0.1*TESTSAM``."""
    pattern = re.compile(
        rf"(?mi)^\s*SAM\s*\([^)]*\)\s*=\s*"
        rf"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s*\*\s*"
        rf"{re.escape(table_name)}\s*\([^)]*\)\s*;"
    )
    match = pattern.search(clean_text)
    return float(match.group(1)) if match else 1.0


def resolve_ifpri_source(source_dir: Optional[PathLike] = None,
                         filename: str = "test.dat") -> Path:
    """Resolve the external IFPRI data file from an argument or environment."""
    if source_dir is None:
        raw = os.environ.get("IFPRI_SOURCE_DIR")
        if not raw:
            raise IfpriDataError(
                "IFPRI_SOURCE_DIR is not set. Point it to the external folder "
                "containing test.dat, or pass source_dir explicitly."
            )
        source_dir = raw
    source_path = Path(source_dir).expanduser() / filename
    return require_source_file(source_path)


def parse_ifpri_test_dat(path: PathLike) -> IfpriDataset:
    """Parse the set definitions and benchmark SAM from ``test.dat``."""
    source_path = require_source_file(Path(path).expanduser())
    text = source_path.read_text(encoding="latin-1")
    clean_text = _strip_gams_comments(text)
    parsed_sets: Mapping[str, Tuple[str, ...]] = {
        name: _extract_set(clean_text, name) for name in _SET_NAMES
    }

    table_name = "TESTSAM"
    rows, columns, raw_values = _extract_gams_table(clean_text, table_name)
    scale = _infer_sam_scale(clean_text, table_name)

    total_label = "TOTAL"
    active_rows = tuple(row for row in rows if row != total_label)
    active_columns = tuple(column for column in columns if column != total_label)
    if set(active_rows) != set(active_columns):
        raise IfpriDataError(
            "The active SAM row and column memberships differ after removing TOTAL."
        )
    # GAMS row order may differ from column order across continuation blocks.
    # Use the declared table column order as the canonical square-SAM order.
    active_accounts = active_columns

    scaled_values = {
        (row, column): value * scale
        for (row, column), value in raw_values.items()
        if row != total_label and column != total_label
    }

    sets = IfpriSets(
        accounts=parsed_sets["AC"],
        activities=parsed_sets["A"],
        agricultural_activities=parsed_sets["AAGR"],
        commodities=parsed_sets["C"],
        agricultural_commodities=parsed_sets["CAGR"],
        domestic_transaction_accounts=parsed_sets["CTD"],
        export_transaction_accounts=parsed_sets["CTE"],
        import_transaction_accounts=parsed_sets["CTM"],
        factors=parsed_sets["F"],
        labor_factors=parsed_sets["FLAB"],
        land_factors=parsed_sets["FLND"],
        capital_factors=parsed_sets["FCAP"],
        institutions=parsed_sets["INS"],
        domestic_institutions=parsed_sets["INSD"],
        domestic_nongovernment_institutions=parsed_sets["INSDNG"],
        enterprises=parsed_sets["EN"],
        households=parsed_sets["H"],
    )
    sam = IfpriSam(
        table_name=table_name,
        accounts=active_accounts,
        values=scaled_values,
        scale=scale,
    )
    dataset = IfpriDataset(source_path=source_path, sets=sets, sam=sam)
    validate_dataset(dataset)
    return dataset


def load_ifpri_test_data(source_dir: Optional[PathLike] = None) -> IfpriDataset:
    """Load and validate the external IFPRI ``test.dat`` dataset."""
    return parse_ifpri_test_dat(resolve_ifpri_source(source_dir))
