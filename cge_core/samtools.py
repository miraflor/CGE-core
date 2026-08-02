# -*- coding: utf-8 -*-
r"""Build CGE-Core datasets from a single social accounting matrix.

The bundled examples read a directory of four CSVs: ``param-sam-.csv``
plus ``set-i-.csv`` (goods), ``set-h-.csv`` (factors), and ``set-u-.csv``
(all SAM accounts). For a real-country SAM -- e.g. a Philippine SAM with
its own sector list -- writing the set files by hand is error-prone. This
module derives them from the SAM itself: the user names the factor
accounts and the institutional accounts, and every remaining account is a
good.

Combined with the ``accounts=`` mapping on the model-definition classes
(which relabels the institutional accounts the equations read, e.g.
``HOH`` -> ``HH``), this lets a balanced SAM with the standard-model
account *structure* -- activities, factors, one household, government,
an indirect-tax row, a tariff row, investment, and rest-of-world -- be
loaded without editing model code. The benchmark flows used in ratios,
CES/CET powers, and Cobb-Douglas calibration must also satisfy the
reference model's nonzero/positivity assumptions.

Example::

    from cge_core import PyCGE, samtools
    from cge_core.examples.stdcge_model_def import StdModelDef

    accounts = dict(hoh='HH', gov='GOVT', inv='SAV-INV',
                    ext='ROW', idt='ITAX', trf='TARIFF')
    samtools.build_dataset('ph_sam.csv', 'ph_data_dir',
                           factors=['CAP', 'LAB'],
                           institutions=accounts.values())
    cge = PyCGE(StdModelDef(accounts=accounts))
    cge.model_data('ph_data_dir')

Provenance: new in CGE-Core v0.3.0; written by James Matthew Miraflor
(2026) via an AI-assisted ("vibecoded") workflow directed and reviewed by
him. Not part of the original NIST PyCGE.
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple, Union

from cge_core.engine import DataValidationError, PyCGE

PathLike = Union[str, "Path"]


def read_sam(path: PathLike) -> Tuple[List[str], Dict[Tuple[str, str], float]]:
    r"""Read and validate a SAM CSV.

    The file is validated with the same structural checks the engine
    applies (square, unique labels, finite numeric cells, balanced row
    and column totals), then parsed.

    Args:
        path (str or Path): path to a SAM CSV whose first row and first
            column carry the account labels.

    Returns:
        (labels, cells) (tuple): ``labels`` is the account list in file
            order; ``cells`` maps ``(row_label, column_label)`` to the
            numeric value.

    Raises:
        DataValidationError: if the file fails structural validation.
    """
    path = Path(path)
    PyCGE._validate_sam_csv(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [row for row in csv.reader(handle)
                if any(cell.strip() for cell in row)]
    columns = [cell.strip() for cell in rows[0][1:]]
    cells: Dict[Tuple[str, str], float] = {}
    labels: List[str] = []
    for row in rows[1:]:
        row_name = row[0].strip()
        labels.append(row_name)
        for column_name, cell in zip(columns, row[1:]):
            cells[(row_name, column_name)] = float(cell)
    return labels, cells


def derive_sets(path: PathLike,
                factors: Sequence[str],
                institutions: Iterable[str]) -> Tuple[List[str], List[str]]:
    r"""Split a SAM's accounts into goods, factors, and institutions.

    Every account that is neither a factor nor an institution is a good
    (an activity/commodity in the standard model's one-to-one mapping).

    Args:
        path (str or Path): path to the SAM CSV.
        factors (sequence of str): labels of the factor accounts
            (e.g. ``['CAP', 'LAB']``).
        institutions (iterable of str): labels of the institutional
            accounts -- for the standard model, the household,
            government, investment, external, indirect-tax, and tariff
            accounts.

    Returns:
        (goods, factors) (tuple of list): goods in SAM order, and the
            factor list in SAM order.

    Raises:
        DataValidationError: if any named factor or institution is
            missing from the SAM, or no goods remain.
    """
    labels, _ = read_sam(path)
    label_set = set(labels)
    factors = list(factors)
    institutions = list(institutions)

    if len(set(factors)) != len(factors):
        raise DataValidationError("Factor account labels must be unique.")
    if len(set(institutions)) != len(institutions):
        raise DataValidationError(
            "Institutional account labels must be unique."
        )

    missing = [a for a in [*factors, *institutions] if a not in label_set]
    if missing:
        raise DataValidationError(
            f"Accounts named but not present in the SAM: {missing}. "
            f"SAM accounts are: {labels}.")
    overlap = set(factors) & set(institutions)
    if overlap:
        raise DataValidationError(
            f"Accounts listed as both factor and institution: "
            f"{sorted(overlap)}.")

    excluded = set(factors) | set(institutions)
    goods = [a for a in labels if a not in excluded]
    if not goods:
        raise DataValidationError(
            "No goods accounts remain after removing factors and "
            "institutions.")
    ordered_factors = [a for a in labels if a in set(factors)]
    return goods, ordered_factors


def _write_set(path: Path, name: str, members: Sequence[str]) -> None:
    """Write a one-column Pyomo set CSV: header ``name``, one row each."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([name])
        for member in members:
            writer.writerow([member])


def build_dataset(sam_path: PathLike,
                  out_dir: PathLike,
                  factors: Sequence[str],
                  institutions: Iterable[str]) -> Path:
    r"""Turn a single SAM CSV into a directory loadable by ``model_data``.

    Writes ``set-i-.csv`` (goods), ``set-h-.csv`` (factors),
    ``set-u-.csv`` (all accounts) and copies the SAM to
    ``param-sam-.csv`` in ``out_dir``.

    Args:
        sam_path (str or Path): path to the SAM CSV.
        out_dir (str or Path): destination directory (created if
            missing).
        factors (sequence of str): factor account labels.
        institutions (iterable of str): institutional account labels;
            for the standard model, pass the six values of the
            ``accounts`` mapping given to ``StdModelDef`` (household,
            government, investment, external, indirect tax, tariff).

    Returns:
        out_dir (Path): the populated directory.

    Raises:
        DataValidationError: from :func:`derive_sets` / SAM validation.
    """
    sam_path = Path(sam_path)
    out_dir = Path(out_dir)
    goods, ordered_factors = derive_sets(sam_path, factors, institutions)
    labels, _ = read_sam(sam_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_set(out_dir / "set-i-.csv", "i", goods)
    _write_set(out_dir / "set-h-.csv", "h", ordered_factors)
    _write_set(out_dir / "set-u-.csv", "u", labels)
    shutil.copyfile(sam_path, out_dir / "param-sam-.csv")
    return out_dir
