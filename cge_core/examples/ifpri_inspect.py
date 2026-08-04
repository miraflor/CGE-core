# -*- coding: utf-8 -*-
"""Inspect the external IFPRI test dataset without solving a model."""
from __future__ import annotations

from cge_core.ifpri import (
    IfpriDataError,
    build_ifpri_benchmark_model,
    calibrate_ifpri_benchmark,
    load_ifpri_test_data,
    validate_ifpri_benchmark_model,
    validate_ifpri_calibration,
)


def main() -> int:
    try:
        dataset = load_ifpri_test_data()
    except IfpriDataError as exc:
        print(f"IFPRI data error: {exc}")
        return 1

    calibration = calibrate_ifpri_benchmark(dataset)
    validate_ifpri_calibration(dataset, calibration)
    model = build_ifpri_benchmark_model(dataset, calibration)
    residual_report = validate_ifpri_benchmark_model(model)

    sets = dataset.sets
    sam = dataset.sam
    print(f"Source: {dataset.source_path}")
    print(f"Activities ({len(sets.activities)}): {', '.join(sets.activities)}")
    print(f"Commodities ({len(sets.commodities)}): {', '.join(sets.commodities)}")
    print(f"Factors ({len(sets.factors)}): {', '.join(sets.factors)}")
    print(f"Households ({len(sets.households)}): {', '.join(sets.households)}")
    print(f"Active SAM accounts: {len(sam.accounts)}")
    print(f"SAM scale: {sam.scale:g}")
    print(f"Maximum absolute SAM imbalance: {sam.max_abs_imbalance():.12g}")
    print("Calibration inputs: trade, production, LES, home shares, factors, taxes")
    print("Benchmark calibration: algebraic identities passed (no solver)")
    print(f"Benchmark CPI: {calibration.system.consumer_price_index:.12g}")
    print(f"Benchmark absorption: {calibration.system.total_absorption:.12g}")
    print(f"Pyomo benchmark equations: {residual_report.equation_count}")
    print(
        "Maximum Pyomo benchmark residual: "
        f"{residual_report.max_abs_residual:.12g} "
        f"({residual_report.worst_equation})"
    )
    print("Pyomo benchmark: initialized equation system passed (no solver)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
