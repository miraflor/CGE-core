"""Prepare a CGE-Core v0.6.0 checkout for the v0.7.0 overlay.

Usage after extracting this overlay over baseline commit
7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2::

    python release/prepare_release.py --check
    python release/prepare_release.py

``--check`` performs the complete preflight and computes every source change
without writing anything.  The normal invocation applies the already-
validated plan using atomic per-file replacements.  The script is idempotent
and intentionally remains in ``release/`` as release provenance/tooling.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "7d07cf80bd2d08cdbc7ca31e78e7a09d13768fd2"

STANDARD_BENCHMARK_ONLY = frozenset({
    "sam", "Td0", "Tz0", "Tm0", "F0", "Y0", "X0", "Z0", "M0",
    "Xp0", "Sp0", "Xg0", "Sg0", "Xv0", "E0", "Q0", "D0",
})
SIMPLE_BENCHMARK_ONLY = frozenset({"sam", "X0", "F0", "Z0"})
CAM_BENCHMARK_ONLY = frozenset({
    "gr0", "cdtot0", "wa0", "mps0", "tm0", "m0", "e0", "xd0",
    "pd0", "pm0", "pe0", "pwe0", "pva0", "xxd0", "dst0", "id0",
    "ls0", "x0", "int0", "y0",
})

OLD_NOTEBOOKS = (
    "00_start_here.ipynb", "01_your_first_cge.ipynb",
    "02_open_economy_cge.ipynb", "03_policy_experiments.ipynb",
    "04_bring_your_own_sam.ipynb", "05_ifpri_standard_cge.ipynb",
    "06_camcge_replication.ipynb", "07_under_the_hood.ipynb",
)
OLD_MIGRATION_TESTS = (
    "test_docs_v06.py", "test_notebooks_v06.py",
    "test_phase6_cleanup.py", "test_release_v060.py",
)


@dataclass
class ChangePlan:
    writes: Dict[Path, str] = field(default_factory=dict)
    deletes: Set[Path] = field(default_factory=set)

    def stage(self, path: Path, text: str) -> None:
        current = _read(path)
        if current != text:
            self.writes[path] = text

    def delete_if_present(self, path: Path) -> None:
        if path.exists():
            self.deletes.add(path)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _newline_style(path: Path) -> str:
    data = path.read_bytes() if path.exists() else b""
    return "\r\n" if b"\r\n" in data else "\n"


def _write_atomic(path: Path, text: str) -> None:
    newline = _newline_style(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline=newline) as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _replace_between(
    text: str,
    *,
    path: Path,
    start_marker: str,
    end_marker: str,
    replacement: str,
    sentinel: str,
) -> str:
    if sentinel in text:
        return text
    start = text.find(start_marker)
    end = text.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise SystemExit(f"Could not patch expected v0.6 anchors in {path}")
    return text[:start] + replacement + text[end:]


def _insert_before(
    text: str,
    *,
    path: Path,
    marker: str,
    insertion: str,
    sentinel: str,
) -> str:
    if sentinel in text:
        return text
    pos = text.find(marker)
    if pos < 0:
        raise SystemExit(f"Could not find metadata insertion anchor in {path}")
    return text[:pos] + insertion + text[pos:]


def _literal_frozenset(source: str, variable: str) -> frozenset[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id != variable:
            continue
        call = node.value
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            break
        if call.func.id != "frozenset" or len(call.args) != 1:
            break
        literal = ast.literal_eval(call.args[0])
        return frozenset(literal)
    raise SystemExit(f"Could not read explicit {variable} from cge_core/model_spec.py")


def _suffix_zero_components(source: str) -> frozenset[str]:
    pattern = re.compile(
        r"(?:self\.)?m\.([A-Za-z_][A-Za-z0-9_]*0)\s*=\s*(?:Param|Var)\b"
    )
    return frozenset(pattern.findall(source))


def _verify_explicit_protection_metadata() -> None:
    model_spec = _read(ROOT / "cge_core" / "model_spec.py")
    declared = {
        "standard": _literal_frozenset(model_spec, "_STANDARD_BENCHMARK_ONLY"),
        "simple": _literal_frozenset(model_spec, "_SIMPLE_BENCHMARK_ONLY"),
        "cam": _literal_frozenset(model_spec, "_CAM_BENCHMARK_ONLY"),
    }
    expected = {
        "standard": STANDARD_BENCHMARK_ONLY,
        "simple": SIMPLE_BENCHMARK_ONLY,
        "cam": CAM_BENCHMARK_ONLY,
    }
    for name in expected:
        if declared[name] != expected[name]:
            raise SystemExit(
                f"Explicit {name} benchmark metadata differs between the "
                "release script and cge_core/model_spec.py: "
                f"script={sorted(expected[name])}, spec={sorted(declared[name])}"
            )

    sources = {
        "standard": _read(ROOT / "cge_core" / "examples" / "stdcge_model_def.py"),
        "simple": _read(ROOT / "cge_core" / "examples" / "splcge_model_def.py"),
        "cam": _read(ROOT / "cam" / "cam_model_def.py"),
    }
    suffix_expected = {
        "standard": STANDARD_BENCHMARK_ONLY - {"sam"},
        "simple": SIMPLE_BENCHMARK_ONLY - {"sam"},
        "cam": CAM_BENCHMARK_ONLY,
    }
    for name, source in sources.items():
        actual = _suffix_zero_components(source)
        if actual != suffix_expected[name]:
            raise SystemExit(
                f"{name} explicit benchmark metadata does not exactly preserve "
                f"the v0.6 trailing-*0 guard: source={sorted(actual)}, "
                f"declared={sorted(suffix_expected[name])}"
            )
    for name in ("standard", "simple"):
        if not re.search(r"(?:self\.)?m\.sam\s*=\s*Param\b", sources[name]):
            raise SystemExit(f"Could not confirm v0.6 `{name}` SAM protection anchor.")


def _preflight_root() -> None:
    required = (
        ROOT / "pyproject.toml",
        ROOT / "README.md",
        ROOT / "cge_core" / "engine.py",
        ROOT / "cge_core" / "examples" / "stdcge_model_def.py",
        ROOT / "cge_core" / "examples" / "splcge_model_def.py",
        ROOT / "cge_core" / "ifpri" / "solve.py",
        ROOT / "cam" / "cam_model_def.py",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(
            "This overlay must be extracted over the CGE-Core v0.6.0 checkout. "
            f"Missing retained baseline files: {missing}"
        )
    if 'version = "0.7.0"' not in _read(ROOT / "pyproject.toml"):
        raise SystemExit("The v0.7.0 overlay does not appear to be extracted here.")


def build_plan() -> ChangePlan:
    """Compute and validate every migration edit without mutating the tree."""
    _preflight_root()
    _verify_explicit_protection_metadata()
    plan = ChangePlan()

    for name in OLD_NOTEBOOKS:
        plan.delete_if_present(ROOT / "notebooks" / name)
    for name in OLD_MIGRATION_TESTS:
        plan.delete_if_present(ROOT / "tests" / name)

    # Preserve the complete historical changelog and prepend the v0.7 fragment.
    fragment_path = ROOT / "release" / "CHANGELOG_v070.md"
    changelog = ROOT / "CHANGELOG.md"
    if not fragment_path.exists() or not changelog.exists():
        raise SystemExit("Missing CHANGELOG.md or release/CHANGELOG_v070.md")
    fragment = _read(fragment_path).strip()
    old = _read(changelog)
    if "## v0.7.0 (2026)" not in old:
        if old.startswith("# Changelog"):
            rest = old[len("# Changelog"):].lstrip("\n")
            plan.stage(changelog, f"# Changelog\n\n{fragment}\n\n{rest}")
        else:
            plan.stage(changelog, f"{fragment}\n\n{old}")

    citation = ROOT / "CITATION.cff"
    if not citation.exists():
        raise SystemExit("Missing retained CITATION.cff")
    text = _read(citation)
    updated = text.replace("version: 0.6.0", "version: 0.7.0")
    updated = updated.replace("version: '0.6.0'", "version: '0.7.0'")
    updated = updated.replace('version: "0.6.0"', 'version: "0.7.0"')
    if "0.7.0" not in updated:
        raise SystemExit("Could not update CITATION.cff version to 0.7.0")
    plan.stage(citation, updated)

    # Central solver resolution in retained low-level engine.
    engine_path = ROOT / "cge_core" / "engine.py"
    engine = _read(engine_path)
    engine = _replace_between(
        engine,
        path=engine_path,
        start_marker=(
            "    @staticmethod\n"
            "    def _available_solver(preferred: Optional[str] = None) -> str:\n"
        ),
        end_marker='    def _solve(self, instance, solver=None, mgr=""):\n',
        replacement='''    @staticmethod\n    def _available_solver(preferred: Optional[str] = None) -> str:\n        from cge_core.solvers import SolverResolutionError, resolve_solver\n        try:\n            return resolve_solver(preferred)\n        except SolverResolutionError as exc:\n            raise SolveError(str(exc)) from exc\n\n''',
        sentinel="from cge_core.solvers import SolverResolutionError, resolve_solver",
    )

    # Explicit metadata on legacy PyCGE, preserving old behavior without a
    # runtime spelling heuristic.
    metadata_sentinel = "self.benchmark_only_components = frozenset("
    if metadata_sentinel not in engine:
        anchor = '''        self.institutional_accounts = (\n            frozenset(accounts.values()) if accounts is not None else None\n        )\n        self.data = None'''
        replacement = '''        self.institutional_accounts = (\n            frozenset(accounts.values()) if accounts is not None else None\n        )\n        self.benchmark_only_components = frozenset(\n            getattr(model_def, "benchmark_only_components", ())\n        )\n        self.base_protected_components = frozenset(\n            getattr(model_def, "base_protected_components", ())\n        )\n        self.data = None'''
        if anchor not in engine:
            raise SystemExit("Could not patch PyCGE metadata initialization.")
        engine = engine.replace(anchor, replacement, 1)

    old_guard = '''        if name == "sam" or name.endswith("0") or (base and name == "FF"):\n            scope = "BASE" if base else "SIM"\n            raise ComponentError(\n                f"{scope} component '{name}' is benchmark calibration data "\n                "and cannot be modified in-place. Change the input CSV and "\n                "rebuild the instance instead.")'''
    new_guard = '''        if name in getattr(self, "benchmark_only_components", ()) or (\n                base and name in getattr(self, "base_protected_components", ())):\n            scope = "BASE" if base else "SIM"\n            raise ComponentError(\n                f"{scope} component '{name}' is explicitly declared benchmark "\n                "calibration data or protected base data and cannot be modified "\n                "in-place. Change the benchmark input or model metadata instead.")'''
    if old_guard in engine:
        engine = engine.replace(old_guard, new_guard, 1)
    elif 'name.endswith("0")' in engine:
        raise SystemExit("Could not replace legacy benchmark-name heuristic safely.")
    elif "benchmark_only_components" not in engine:
        raise SystemExit("Explicit benchmark protection is missing from engine.py")
    plan.stage(engine_path, engine)

    # Centralize IFPRI's retained direct solver path.
    ifpri_path = ROOT / "cge_core" / "ifpri" / "solve.py"
    ifpri = _read(ifpri_path)
    ifpri = _replace_between(
        ifpri,
        path=ifpri_path,
        start_marker="def _choose_solver(name: Optional[str]) -> str:\n",
        end_marker="def _solve_label(model) -> str:\n",
        replacement='''def _choose_solver(name: Optional[str]) -> str:\n    from cge_core.solvers import SolverResolutionError, resolve_solver\n    try:\n        return resolve_solver(name)\n    except SolverResolutionError as exc:\n        raise IfpriDataError(str(exc)) from exc\n\n\n''',
        sentinel="from cge_core.solvers import SolverResolutionError, resolve_solver",
    )
    plan.stage(ifpri_path, ifpri)

    # Explicit declarations on the retained model definitions.
    std_path = ROOT / "cge_core" / "examples" / "stdcge_model_def.py"
    std = _read(std_path)
    std = _insert_before(
        std,
        path=std_path,
        marker="    redundant_constraints = frozenset(",
        insertion='''    benchmark_only_components = frozenset({\n        "sam", "Td0", "Tz0", "Tm0", "F0", "Y0", "X0", "Z0", "M0",\n        "Xp0", "Xg0", "Xv0", "E0", "Q0", "D0", "Sp0", "Sg0",\n    })\n    base_protected_components = frozenset({"FF"})\n\n''',
        sentinel="benchmark_only_components = frozenset({",
    )
    plan.stage(std_path, std)

    spl_path = ROOT / "cge_core" / "examples" / "splcge_model_def.py"
    spl = _read(spl_path)
    spl = _insert_before(
        spl,
        path=spl_path,
        marker="    redundant_constraints = frozenset(",
        insertion='''    benchmark_only_components = frozenset({"sam", "X0", "F0", "Z0"})\n    base_protected_components = frozenset({"FF"})\n\n''',
        sentinel="benchmark_only_components = frozenset({",
    )
    plan.stage(spl_path, spl)

    cam_model_path = ROOT / "cam" / "cam_model_def.py"
    cam_model = _read(cam_model_path)
    cam_model = _insert_before(
        cam_model,
        path=cam_model_path,
        marker="    redundant_constraints = frozenset({'caeq'})",
        insertion='''    benchmark_only_components = frozenset({\n        "gr0", "cdtot0", "wa0", "mps0", "tm0", "m0", "e0", "xd0",\n        "pd0", "pm0", "pe0", "pwe0", "pva0", "xxd0", "dst0", "id0",\n        "ls0", "x0", "int0", "y0",\n    })\n    base_protected_components = frozenset()\n\n''',
        sentinel="benchmark_only_components = frozenset({",
    )
    plan.stage(cam_model_path, cam_model)

    # Retained regression test must probe the centralized resolver first.
    test_engine = ROOT / "tests" / "test_engine.py"
    if test_engine.exists():
        test_text = _read(test_engine)
        anchor = '''    monkeypatch.setattr(engine, 'SolverFactory', lambda name: BrokenSolver())\n    cge = std_instance()\n'''
        replacement = '''    import cge_core.solvers as solver_resolution\n    monkeypatch.setattr(solver_resolution, '_probe', lambda name: True)\n    monkeypatch.setattr(engine, 'SolverFactory', lambda name: BrokenSolver())\n    cge = std_instance()\n'''
        if anchor in test_text and "solver_resolution, '_probe'" not in test_text:
            test_text = test_text.replace(anchor, replacement, 1)
        plan.stage(test_engine, test_text)

    # Control Room public target version; retain generator compatibility.
    control_room = ROOT / "docs" / "microsites" / "control-room" / "assets" / "app.js"
    if not control_room.exists():
        raise SystemExit("Missing retained Control Room app.js")
    app = _read(control_room)
    old_version = "const CGE_CORE_TARGET_VERSION = '0.6.0';"
    new_version = "const CGE_CORE_TARGET_VERSION = '0.7.0';"
    if old_version in app:
        app = app.replace(old_version, new_version, 1)
    elif new_version not in app:
        raise SystemExit("Could not locate Control Room target-version constant.")
    for required_surface in (
        "build_and_solve_ifpri_scenarios",
        "from cam.replicate_experiments import (",
    ):
        if required_surface not in app:
            raise SystemExit(
                f"Retained Control Room is missing expected surface: {required_surface}"
            )
    plan.stage(control_room, app)

    fixture = ROOT / "tests" / "fixtures" / "control_room_stdcge_tariff.py.txt"
    if not fixture.exists():
        raise SystemExit("Missing retained Control Room generated-code fixture.")
    fixture_text = _read(fixture)
    for required_surface in (
        "from cge_core import CGE, example_data",
        "from cge_core.models import StdCGE",
        "benchmark = model.solve_benchmark(",
        'scenario = benchmark.scenario("control-room tariff abolition")',
        'scenario.set("taum", "BRD", 0.0)',
        "comparison = result.compare(benchmark)",
    ):
        if required_surface not in fixture_text:
            raise SystemExit(
                f"Control Room fixture lost expected compatibility surface: {required_surface}"
            )

    # CAM replication helpers default to automatic solver resolution.  Patch
    # only the two known validation scripts and only if content changes.
    for relative in ("cam/replicate_base.py", "cam/replicate_experiments.py"):
        path = ROOT / relative
        if not path.exists():
            raise SystemExit(f"Missing retained CAM validation script: {relative}")
        source = _read(path)
        updated = source.replace('solver="cyipopt"', 'solver=None')
        updated = updated.replace('default="cyipopt"', 'default=None')
        updated = updated.replace(
            "Pyomo solver name (default: cyipopt; ipopt is also supported)",
            "Pyomo solver name (default: automatic IPOPT/cyipopt resolution)",
        )
        plan.stage(path, updated)

    return plan


def apply_plan(plan: ChangePlan) -> None:
    for path in sorted(plan.writes, key=lambda item: str(item)):
        _write_atomic(path, plan.writes[path])
    for path in sorted(plan.deletes, key=lambda item: str(item)):
        path.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preflight/apply CGE-Core v0.7.0 overlay housekeeping."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate every retained-source anchor and planned edit without writing",
    )
    args = parser.parse_args(argv)

    plan = build_plan()
    if args.check:
        print(
            "CGE-Core v0.7.0 release preflight OK: "
            f"{len(plan.writes)} file update(s), {len(plan.deletes)} deletion(s) planned."
        )
        return 0

    apply_plan(plan)
    print(
        "CGE-Core v0.7.0 tree prepared: "
        f"{len(plan.writes)} file update(s), {len(plan.deletes)} deletion(s) applied."
    )
    print("Next: run tests/build checks, review `git diff`, commit, and tag v0.7.0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
