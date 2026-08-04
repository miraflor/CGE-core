# -*- coding: utf-8 -*-
"""Solve all five IFPRI policy simulations and compare with GAMS NLP targets."""
from pathlib import Path

from cge_core.ifpri import (
    IFPRI_POLICY_SCENARIOS,
    build_and_solve_ifpri_scenarios,
    compare_ifpri_model_to_reference,
    load_ifpri_reference_targets,
    load_ifpri_test_data,
)


def main() -> int:
    dataset = load_ifpri_test_data()
    reference = (
        Path(__file__).resolve().parents[2]
        / "validation"
        / "gams"
        / "ifpri_standard"
        / "reference"
        / "full_precision_targets.csv"
    )
    results = build_and_solve_ifpri_scenarios(dataset)

    for scenario in IFPRI_POLICY_SCENARIOS:
        model, report = results[scenario]
        comparison = compare_ifpri_model_to_reference(
            model,
            load_ifpri_reference_targets(reference, "NLP", scenario.value),
        )
        print(f"Scenario: {scenario.value}")
        print(f"  Solver: {report.solver}")
        print(f"  Termination: {report.termination_condition}")
        print(f"  Degrees of freedom: {report.degrees_of_freedom}")
        print(f"  Maximum equation residual: {report.max_abs_equation_residual:.12g}")
        print(f"  Compared GAMS values: {comparison.compared_values}")
        print(
            "  Maximum absolute GAMS difference: "
            f"{comparison.max_abs_difference:.12g} "
            f"({comparison.worst_absolute})"
        )
        print(
            "  Maximum relative GAMS difference: "
            f"{comparison.max_relative_difference:.12g} "
            f"({comparison.worst_relative})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
