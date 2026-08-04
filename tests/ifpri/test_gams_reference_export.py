"""Unit tests for the external IFPRI GAMS full-precision exporter.

These tests do not require GAMS or the GPL-licensed source package. They verify
only CGE-Core's patching, CSV validation, and deterministic merge logic.
"""
from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "validation"
    / "gams"
    / "ifpri_standard"
    / "export_full_precision.py"
)
SPEC = importlib.util.spec_from_file_location("ifpri_gams_export", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
export = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = export
SPEC.loader.exec_module(export)


def test_patch_mod_source_changes_only_obsolete_solver_alias():
    original = "OPTIONS MCP=PATH, NLP=CONOPT2 ;\nSOLVE STANDCGE USING MCP;\n"
    patched = export.patch_mod_source(original)
    assert "MCP=PATH, NLP=CONOPT ;" in patched
    assert "CONOPT2" not in patched
    assert "SOLVE STANDCGE USING MCP;" in patched


def test_patch_sim_source_selects_mode_and_appends_exporter():
    original = "SIMMCP(SIM)     = YES;\nDISPLAY SIMCUR;\n"
    mcp = export.patch_sim_source(original, "MCP")
    nlp = export.patch_sim_source(original, "NLP")
    assert "SIMMCP(SIM)     = YES;" in mcp
    assert "CGECORE_EXPORT_SOLVER MCP" in mcp
    assert "SIMMCP(SIM)     = NO;" in nlp
    assert "CGECORE_EXPORT_SOLVER NLP" in nlp
    assert mcp.count("full_precision_export.inc") == 1
    assert nlp.count("full_precision_export.inc") == 1


def _synthetic_rows():
    rows = []
    for solver in export.EXPECTED_SOLVERS:
        for scenario in export.EXPECTED_SCENARIOS:
            core = {
                "CPI": 1.0,
                "EXR": 1.0,
                "TABS": 22.0,
                "WALRAS": 0.0,
            }
            for symbol, value in core.items():
                rows.append(export.TargetRow(solver, scenario, symbol, "", "", "", value))
            rows.extend(
                [
                    export.TargetRow(solver, scenario, "QA", "A1", "", "", 10.0),
                    export.TargetRow(solver, scenario, "PQ", "C1", "", "", 1.0),
                    export.TargetRow(solver, scenario, "QF", "LAB", "A1", "", 3.0),
                ]
            )
            model_status = 1.0 if solver == "MCP" else 2.0
            for indicator, value in (
                ("MODEL-STATUS", model_status),
                ("SOLVER-STATUS", 1.0),
                ("NUM-REDEFEQ", 0.0),
            ):
                rows.append(
                    export.TargetRow(
                        solver,
                        scenario,
                        "SOLVEREP",
                        indicator,
                        solver,
                        "",
                        value,
                    )
                )
    return rows


def test_validate_target_rows_accepts_complete_two_solver_record():
    metrics = export.validate_target_rows(_synthetic_rows())
    assert metrics["row_count"] == 120
    assert metrics["maximum_absolute_walras"] == 0.0
    assert metrics["maximum_absolute_mcp_nlp_difference"] == 0.0



def _replace_walras(rows, solver, scenario, value):
    replaced = []
    for row in rows:
        if (
            row.solver == solver
            and row.scenario == scenario
            and row.symbol == "WALRAS"
        ):
            row = export.TargetRow(
                row.solver,
                row.scenario,
                row.symbol,
                row.index1,
                row.index2,
                row.index3,
                value,
            )
        replaced.append(row)
    return replaced


def test_validate_target_rows_accepts_small_path_residual_and_records_location():
    rows = _replace_walras(_synthetic_rows(), "MCP", "TARCUT2", 3.752891628572286e-7)
    metrics = export.validate_target_rows(rows)
    assert metrics["maximum_absolute_walras"] == pytest.approx(
        3.752891628572286e-7
    )
    assert metrics["maximum_absolute_walras_solver"] == "MCP"
    assert metrics["maximum_absolute_walras_scenario"] == "TARCUT2"
    assert metrics["walras_absolute_tolerance"] == 1e-6


def test_validate_target_rows_rejects_walras_above_tolerance_with_location():
    rows = _replace_walras(_synthetic_rows(), "MCP", "TARCUT2", 1.1e-6)
    with pytest.raises(export.ExportError, match=r"MCP/TARCUT2.*tolerance"):
        export.validate_target_rows(rows)

def test_validate_target_rows_rejects_duplicate_key():
    rows = _synthetic_rows()
    rows.append(rows[0])
    with pytest.raises(export.ExportError, match="Duplicate target key"):
        export.validate_target_rows(rows)


def test_write_merged_targets_is_sorted_and_round_trippable(tmp_path):
    rows = _synthetic_rows()
    source_paths = []
    for solver in reversed(export.EXPECTED_SOLVERS):
        path = tmp_path / f"{solver.lower()}.csv"
        source_paths.append(path)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=export.CSV_FIELDS)
            writer.writeheader()
            for row in reversed([row for row in rows if row.solver == solver]):
                writer.writerow(
                    {
                        "solver": row.solver,
                        "scenario": row.scenario,
                        "symbol": row.symbol,
                        "index1": row.index1,
                        "index2": row.index2,
                        "index3": row.index3,
                        "value": row.value,
                    }
                )
    destination = tmp_path / "merged.csv"
    metrics = export.write_merged_targets(source_paths, destination)
    reread = export.read_target_rows(destination)
    assert metrics["row_count"] == len(reread) == len(rows)
    assert [row.key for row in reread] == sorted(row.key for row in rows)
