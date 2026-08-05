"""Solver-free structural tests for the CAMCGE replication package."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from cge_core.engine import PyCGE

from cam.cam_model_def import CamModelDef
from cam.make_data import DATA_DIR, I, LC, validate_source_tables, write_data


def _csv_rows(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_source_table_adding_up_checks():
    totals = validate_source_tables()
    assert totals["rural"] == pytest.approx(2270.04, abs=1e-9)
    assert totals["urban-unsk"] == pytest.approx(515.064, abs=1e-9)
    assert totals["urban-skil"] == pytest.approx(132.515, abs=1e-9)


def test_generated_csvs_match_committed_data(tmp_path):
    write_data(tmp_path)
    expected_names = sorted(path.name for path in DATA_DIR.glob("*.csv"))
    generated_names = sorted(path.name for path in tmp_path.glob("*.csv"))
    assert generated_names == expected_names
    for name in expected_names:
        assert _csv_rows(tmp_path / name) == _csv_rows(DATA_DIR / name), name


def test_set_headers_and_first_members_are_preserved(tmp_path):
    write_data(tmp_path)
    assert _csv_rows(tmp_path / "set-i-.csv")[:2] == [["i"], [I[0]]]
    assert _csv_rows(tmp_path / "set-lc-.csv")[:2] == [["lc"], [LC[0]]]
    assert _csv_rows(tmp_path / "set-zrow-.csv")[0] == ["zrow"]


def test_cam_model_metadata_declares_complete_boundary():
    definition = CamModelDef()
    assert definition.redundant_constraints == frozenset({"caeq"})
    assert definition.numeraire_variables == frozenset({"mps"})
    assert definition.required_data_files == frozenset(
        path.name for path in DATA_DIR.glob("*.csv")
    )


def test_cam_closure_is_square_after_walras_drop():
    cge = PyCGE(CamModelDef())
    cge.model_data(DATA_DIR)
    cge.model_instance("mps", None)
    assert cge.degrees_of_freedom(cge.base) == -1
    cge.model_drop_redundant("caeq")
    assert cge.degrees_of_freedom(cge.base) == 0
