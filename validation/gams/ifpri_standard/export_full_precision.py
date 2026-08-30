#!/usr/bin/env python3
"""Generate full-precision IFPRI GAMS reference targets outside the source tree.

The official GPL-licensed model must be supplied separately through
``IFPRI_SOURCE_DIR`` or ``--source-dir``. This utility copies that source into
an external working directory, applies only the already documented modern-GAMS
solver-name compatibility change, runs all supplied simulations under MCP/PATH
and NLP/CONOPT, and writes compact numeric targets into this repository.

No official IFPRI source file is copied into the CGE-Core repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

EXPECTED_SCENARIOS = (
    "BASE",
    "TARCUT1",
    "TARCUT2",
    "FSAVINCR",
    "PWMINCR",
    "DEVAL",
)
EXPECTED_SOLVERS = ("MCP", "NLP")
WALRAS_ABSOLUTE_TOLERANCE = 1e-6
CSV_FIELDS = (
    "solver",
    "scenario",
    "symbol",
    "index1",
    "index2",
    "index3",
    "value",
)
REQUIRED_SOURCE_FILES = (
    "mod101.gms",
    "sim101.gms",
    "test.dat",
    "diagnostics.inc",
    "repbase.inc",
    "reploop.inc",
    "repperc.inc",
    "repsetup.inc",
    "repsum.inc",
    "varinit.inc",
)


class ExportError(RuntimeError):
    """Raised when the external GAMS reference export is incomplete or invalid."""


@dataclass(frozen=True)
class TargetRow:
    solver: str
    scenario: str
    symbol: str
    index1: str
    index2: str
    index3: str
    value: float

    @property
    def key(self) -> Tuple[str, str, str, str, str, str]:
        return (
            self.solver,
            self.scenario,
            self.symbol,
            self.index1,
            self.index2,
            self.index3,
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _replace_once(text: str, old: str, new: str, *, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ExportError(
            f"Expected exactly one {label} marker, found {count}: {old!r}"
        )
    return text.replace(old, new, 1)


def patch_mod_source(text: str) -> str:
    """Apply the documented GAMS-54 solver-name compatibility change."""
    return _replace_once(
        text,
        "MCP=PATH, NLP=CONOPT2",
        "MCP=PATH, NLP=CONOPT",
        label="CONOPT2 compatibility",
    )


def patch_sim_source(text: str, solver: str) -> str:
    """Select MCP or NLP for all simulations and append the CSV exporter."""
    solver = solver.upper()
    if solver not in EXPECTED_SOLVERS:
        raise ValueError(f"Unsupported solver mode: {solver}")

    old = "SIMMCP(SIM)     = YES;"
    new = old if solver == "MCP" else "SIMMCP(SIM)     = NO;"
    patched = _replace_once(text, old, new, label="SIMMCP switch")
    if "full_precision_export.inc" in patched:
        raise ExportError("sim101.gms already contains the full-precision exporter.")

    suffix = (
        "\n\n* CGE-Core full-precision reference export (external run copy only).\n"
        f"$setglobal CGECORE_EXPORT_SOLVER {solver}\n"
        f"$setglobal CGECORE_EXPORT_FILE cge_core_full_precision_{solver.lower()}.csv\n"
        "$include full_precision_export.inc\n"
    )
    return patched.rstrip() + suffix


def resolve_source_dir(value: str | os.PathLike[str] | None) -> Path:
    raw = value or os.environ.get("IFPRI_SOURCE_DIR")
    if not raw:
        raise ExportError(
            "IFPRI_SOURCE_DIR is not set. Point it to the external folder "
            "containing mod101.gms, sim101.gms, and test.dat."
        )
    source = Path(raw).expanduser().resolve()
    if not source.is_dir():
        raise ExportError(f"IFPRI source directory does not exist: {source}")
    missing = [name for name in REQUIRED_SOURCE_FILES if not (source / name).is_file()]
    if missing:
        raise ExportError(f"IFPRI source directory is missing: {missing}")
    return source


def resolve_gams_executable(value: str | None) -> str:
    candidate = value or "gams"
    resolved = shutil.which(candidate)
    if resolved is None:
        path = Path(candidate).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise ExportError(
            f"GAMS executable was not found: {candidate!r}. Add GAMS to PATH "
            "or pass --gams with the full path to gams.exe."
        )
    return resolved


def prepare_run_directory(
    source_dir: Path,
    run_dir: Path,
    exporter_include: Path,
    solver: str,
) -> None:
    """Create a disposable external run copy with narrowly scoped patches."""
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(source_dir, run_dir)
    shutil.copy2(exporter_include, run_dir / exporter_include.name)

    mod_path = run_dir / "mod101.gms"
    sim_path = run_dir / "sim101.gms"
    mod_text = mod_path.read_text(encoding="latin-1")
    sim_text = sim_path.read_text(encoding="latin-1")
    mod_path.write_text(patch_mod_source(mod_text), encoding="latin-1")
    sim_path.write_text(patch_sim_source(sim_text, solver), encoding="latin-1")
    (run_dir / "SAVE").mkdir(exist_ok=True)


def _run_command(command: Sequence[str], cwd: Path) -> None:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-40:])
        raise ExportError(
            f"Command failed with exit code {completed.returncode}:\n"
            f"  {' '.join(command)}\n"
            f"Working directory retained at: {cwd}\n"
            f"Last output lines:\n{tail}"
        )


def run_solver(gams: str, run_dir: Path, solver: str) -> Path:
    """Run the benchmark compile/save step and all official simulations."""
    solver_lower = solver.lower()
    save_stub = str(Path("SAVE") / "MOD101")
    _run_command(
        (
            gams,
            "mod101.gms",
            f"s={save_stub}",
            f"o=mod101_{solver_lower}.lst",
            "lo=2",
        ),
        run_dir,
    )
    _run_command(
        (
            gams,
            "sim101.gms",
            f"r={save_stub}",
            f"o=sim101_{solver_lower}.lst",
            "lo=2",
        ),
        run_dir,
    )
    target = run_dir / f"cge_core_full_precision_{solver_lower}.csv"
    if not target.is_file():
        raise ExportError(f"GAMS completed but did not create {target}")
    return target


def read_target_rows(path: Path) -> List[TargetRow]:
    rows: List[TargetRow] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ExportError(
                f"Unexpected columns in {path}: {reader.fieldnames}; "
                f"expected {list(CSV_FIELDS)}"
            )
        for line_number, raw in enumerate(reader, start=2):
            try:
                value = float(raw["value"])
            except (TypeError, ValueError) as exc:
                raise ExportError(
                    f"Non-numeric target at {path}:{line_number}: {raw['value']!r}"
                ) from exc
            if not math.isfinite(value):
                raise ExportError(
                    f"Non-finite target at {path}:{line_number}: {value}"
                )
            rows.append(
                TargetRow(
                    solver=raw["solver"].strip().upper(),
                    scenario=raw["scenario"].strip().upper(),
                    symbol=raw["symbol"].strip().upper(),
                    index1=raw["index1"].strip(),
                    index2=raw["index2"].strip(),
                    index3=raw["index3"].strip(),
                    value=value,
                )
            )
    if not rows:
        raise ExportError(f"No target rows were read from {path}")
    return rows


def _lookup(
    indexed: Mapping[Tuple[str, str, str, str, str, str], float],
    solver: str,
    scenario: str,
    symbol: str,
    index1: str = "",
    index2: str = "",
    index3: str = "",
) -> float:
    key = (solver, scenario, symbol, index1, index2, index3)
    try:
        return indexed[key]
    except KeyError as exc:
        raise ExportError(f"Missing required target row: {key}") from exc


def validate_target_rows(rows: Sequence[TargetRow]) -> Dict[str, object]:
    """Validate completeness, solve status, uniqueness, and Walras residuals."""
    indexed: Dict[Tuple[str, str, str, str, str, str], float] = {}
    for row in rows:
        if row.key in indexed:
            raise ExportError(f"Duplicate target key: {row.key}")
        indexed[row.key] = row.value

    solvers = {row.solver for row in rows}
    if solvers != set(EXPECTED_SOLVERS):
        raise ExportError(f"Expected solvers {EXPECTED_SOLVERS}, found {sorted(solvers)}")

    required_symbols = {"CPI", "EXR", "QA", "PQ", "QF", "TABS", "WALRAS"}
    max_walras = 0.0
    max_walras_solver = ""
    max_walras_scenario = ""
    for solver in EXPECTED_SOLVERS:
        scenarios = {row.scenario for row in rows if row.solver == solver}
        if scenarios != set(EXPECTED_SCENARIOS):
            raise ExportError(
                f"{solver} scenarios differ: expected {EXPECTED_SCENARIOS}, "
                f"found {sorted(scenarios)}"
            )
        for scenario in EXPECTED_SCENARIOS:
            symbols = {
                row.symbol
                for row in rows
                if row.solver == solver and row.scenario == scenario
            }
            missing_symbols = sorted(required_symbols - symbols)
            if missing_symbols:
                raise ExportError(
                    f"{solver}/{scenario} is missing symbols: {missing_symbols}"
                )
            expected_model_status = 1.0 if solver == "MCP" else 2.0
            model_status = _lookup(
                indexed, solver, scenario, "SOLVEREP", "MODEL-STATUS", solver
            )
            solver_status = _lookup(
                indexed, solver, scenario, "SOLVEREP", "SOLVER-STATUS", solver
            )
            redefined = _lookup(
                indexed, solver, scenario, "SOLVEREP", "NUM-REDEFEQ", solver
            )
            if model_status != expected_model_status:
                raise ExportError(
                    f"{solver}/{scenario} model status is {model_status}, "
                    f"expected {expected_model_status}."
                )
            if solver_status != 1.0:
                raise ExportError(
                    f"{solver}/{scenario} solver status is {solver_status}, expected 1."
                )
            if redefined != 0.0:
                raise ExportError(
                    f"{solver}/{scenario} has {redefined} redefined equations."
                )
            walras = abs(_lookup(indexed, solver, scenario, "WALRAS"))
            if walras > max_walras:
                max_walras = walras
                max_walras_solver = solver
                max_walras_scenario = scenario
    if max_walras > WALRAS_ABSOLUTE_TOLERANCE:
        raise ExportError(
            "Maximum absolute Walras residual is too large: "
            f"{max_walras} at {max_walras_solver}/{max_walras_scenario}; "
            f"tolerance is {WALRAS_ABSOLUTE_TOLERANCE}."
        )

    comparable: MutableMapping[
        Tuple[str, str, str, str, str], Dict[str, float]
    ] = {}
    for row in rows:
        if row.symbol == "SOLVEREP":
            continue
        base_key = (row.scenario, row.symbol, row.index1, row.index2, row.index3)
        comparable.setdefault(base_key, {})[row.solver] = row.value
    max_solver_abs_diff = 0.0
    compared = 0
    for values in comparable.values():
        if set(values) == set(EXPECTED_SOLVERS):
            compared += 1
            max_solver_abs_diff = max(
                max_solver_abs_diff, abs(values["MCP"] - values["NLP"])
            )

    return {
        "row_count": len(rows),
        "compared_mcp_nlp_rows": compared,
        "maximum_absolute_walras": max_walras,
        "maximum_absolute_walras_solver": max_walras_solver,
        "maximum_absolute_walras_scenario": max_walras_scenario,
        "walras_absolute_tolerance": WALRAS_ABSOLUTE_TOLERANCE,
        "maximum_absolute_mcp_nlp_difference": max_solver_abs_diff,
    }


def write_merged_targets(paths: Iterable[Path], destination: Path) -> Dict[str, object]:
    rows: List[TargetRow] = []
    for path in paths:
        rows.extend(read_target_rows(path))
    metrics = validate_target_rows(rows)
    rows.sort(key=lambda row: row.key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "solver": row.solver,
                    "scenario": row.scenario,
                    "symbol": row.symbol,
                    "index1": row.index1,
                    "index2": row.index2,
                    "index3": row.index3,
                    "value": format(row.value, ".17g"),
                }
            )
    return metrics


def _gams_banner(listing_path: Path) -> str:
    try:
        first = listing_path.read_text(encoding="latin-1").splitlines()[0].strip()
    except (OSError, IndexError):
        return "unknown"
    return first


def build_manifest(
    source_dir: Path,
    run_root: Path,
    targets_path: Path,
    metrics: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_directory_committed": False,
        "source_files": {
            name: _sha256(source_dir / name)
            for name in ("mod101.gms", "sim101.gms", "test.dat")
        },
        "gams_banners": {
            solver: _gams_banner(
                run_root / solver.lower() / f"mod101_{solver.lower()}.lst"
            )
            for solver in EXPECTED_SOLVERS
        },
        "solvers": list(EXPECTED_SOLVERS),
        "scenarios": list(EXPECTED_SCENARIOS),
        "targets_file": targets_path.name,
        "targets_sha256": _sha256(targets_path),
        "validation": dict(metrics),
        "compatibility_changes": [
            "NLP solver alias changed from CONOPT2 to CONOPT in external run copies.",
            "SIMMCP switched to NO only in the external NLP run copy.",
            "A CGE-Core-authored reporting include was appended only to external run copies.",
        ],
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", help="External official IFPRI source folder")
    parser.add_argument("--gams", help="GAMS executable name or full path")
    parser.add_argument(
        "--work-dir",
        help="External disposable run root; defaults beside the source folder",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help=(
            "Skip GAMS and validate/merge the existing MCP and NLP CSV files "
            "under the work directory."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(here / "reference"),
        help="Destination for compact targets and manifest",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        source_dir = resolve_source_dir(args.source_dir)
        gams = None if args.reuse_existing else resolve_gams_executable(args.gams)
        here = Path(__file__).resolve().parent
        exporter_include = here / "full_precision_export.inc"
        if not exporter_include.is_file():
            raise ExportError(f"Exporter include is missing: {exporter_include}")

        run_root = (
            Path(args.work_dir).expanduser().resolve()
            if args.work_dir
            else source_dir.parent / "runs" / "full_precision_export"
        )
        output_dir = Path(args.output_dir).expanduser().resolve()
        generated: List[Path] = []
        if args.reuse_existing:
            for solver in EXPECTED_SOLVERS:
                existing = (
                    run_root
                    / solver.lower()
                    / f"cge_core_full_precision_{solver.lower()}.csv"
                )
                if not existing.is_file():
                    raise ExportError(
                        f"Existing {solver} export was not found: {existing}"
                    )
                print(f"Reusing existing {solver} export: {existing}")
                generated.append(existing)
        else:
            for solver in EXPECTED_SOLVERS:
                run_dir = run_root / solver.lower()
                print(f"Preparing external {solver} run: {run_dir}")
                prepare_run_directory(source_dir, run_dir, exporter_include, solver)
                print(f"Running official benchmark and simulations with {solver}...")
                assert gams is not None
                generated.append(run_solver(gams, run_dir, solver))

        targets = output_dir / "full_precision_targets.csv"
        metrics = write_merged_targets(generated, targets)
        manifest = build_manifest(source_dir, run_root, targets, metrics)
        manifest_path = output_dir / "full_precision_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote: {targets}")
        print(f"Wrote: {manifest_path}")
        print(f"Rows: {metrics['row_count']}")
        print(
            "Maximum |Walras|: "
            f"{metrics['maximum_absolute_walras']:.6g} "
            f"at {metrics['maximum_absolute_walras_solver']}/"
            f"{metrics['maximum_absolute_walras_scenario']} "
            f"(tolerance {metrics['walras_absolute_tolerance']:.6g})"
        )
        print(
            "Maximum MCP-NLP absolute difference: "
            f"{metrics['maximum_absolute_mcp_nlp_difference']:.6g}"
        )
        return 0
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
