# -*- coding: utf-8 -*-
"""Solve the IFPRI BASE benchmark and compare it with full-precision GAMS."""
from pathlib import Path

from cge_core.ifpri import (
    build_ifpri_base_solve_model,
    compare_ifpri_model_to_reference,
    load_ifpri_reference_targets,
    load_ifpri_test_data,
    perturb_ifpri_start,
    solve_ifpri_base,
)


def main() -> int:
    dataset = load_ifpri_test_data()
    model = build_ifpri_base_solve_model(dataset)
    perturb_ifpri_start(model, 1.02)
    report = solve_ifpri_base(model)
    reference = Path(__file__).resolve().parents[2] / "validation" / "gams" / "ifpri_standard" / "reference" / "full_precision_targets.csv"
    comparison = compare_ifpri_model_to_reference(
        model, load_ifpri_reference_targets(reference, "NLP", "BASE")
    )
    print(f"Solver: {report.solver}")
    print(f"Termination: {report.termination_condition}")
    print(f"Degrees of freedom: {report.degrees_of_freedom}")
    print(f"Maximum equation residual: {report.max_abs_equation_residual:.12g}")
    print(f"Compared GAMS values: {comparison.compared_values}")
    print(f"Maximum absolute GAMS difference: {comparison.max_abs_difference:.12g} ({comparison.worst_absolute})")
    print(f"Maximum relative GAMS difference: {comparison.max_relative_difference:.12g} ({comparison.worst_relative})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
