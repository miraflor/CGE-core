"""Small command-line entry point for diagnostics and .cge.md models."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _doctor(_args):
    from cge_core.solvers import solver_info
    print(json.dumps(solver_info().as_dict(), indent=2))
    return 0


def _install_solver(_args):
    from cge_core.solvers import install_solver
    selected = install_solver()
    print(f"Ready: {selected}")
    return 0


def _check(args):
    from cge_core.spec import parse_file, validate_document
    doc = validate_document(parse_file(args.path))
    count = sum(map(len, [doc.sets, doc.data, doc.parameters, doc.variables,
                          doc.equations, doc.fixes, doc.drops, doc.shockables]))
    print(f"OK: {args.path} ({count} executable declarations/statements)")
    return 0


def _solve(args):
    from pyomo.environ import Var, SolverFactory, value
    from pyomo.opt import check_optimal_termination
    from cge_core.solvers import resolve_solver
    from cge_core.spec import compile_document, parse_file

    path = Path(args.path)
    model = compile_document(parse_file(path), base_dir=path.parent)
    selected = resolve_solver(args.solver)
    result = SolverFactory(selected).solve(model)
    if not check_optimal_termination(result):
        from cge_core.solvers import SolverResolutionError
        solver_meta = getattr(result, "solver", None)
        status = getattr(solver_meta, "status", "unknown")
        termination = getattr(solver_meta, "termination_condition", "unknown")
        raise SolverResolutionError(f"Solver failed: {status}/{termination}")
    print(f"Solved {path.name} with {selected}")
    for component in model.component_objects(Var, active=True):
        if component.is_indexed():
            for index, item in component.items():
                print(f"{component.name}[{index}] = {float(value(item)):.8g}")
        else:
            print(f"{component.name} = {float(value(component)):.8g}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cge", description="CGE-Core utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="show solver/backend diagnostics")
    doctor.set_defaults(func=_doctor)
    installer = sub.add_parser("install-solver", help="install the default open-source NLP solver")
    installer.set_defaults(func=_install_solver)
    check = sub.add_parser("check", help="parse and validate a .cge.md file")
    check.add_argument("path")
    check.set_defaults(func=_check)
    solve = sub.add_parser("solve", help="compile and solve a .cge.md file")
    solve.add_argument("path")
    solve.add_argument("--solver", default=None)
    solve.set_defaults(func=_solve)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        from cge_core.solvers import SolverResolutionError
        from cge_core.spec import CGESpecError
        if isinstance(exc, (SolverResolutionError, CGESpecError)):
            parser.exit(1, f"error: {exc}\n")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
