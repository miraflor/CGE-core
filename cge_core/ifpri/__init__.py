# -*- coding: utf-8 -*-
"""Clean-room data and model support for the IFPRI Standard CGE model."""

from .calibration import calibrate_ifpri_benchmark, validate_ifpri_calibration
from .data import load_ifpri_test_data, parse_ifpri_test_dat, resolve_ifpri_source
from .model import (
    IfpriResidualReport,
    build_ifpri_benchmark_model,
    ifpri_benchmark_residuals,
    summarize_ifpri_benchmark_residuals,
    validate_ifpri_benchmark_model,
)
from .scenarios import (
    IFPRI_POLICY_SCENARIOS,
    IFPRI_SCENARIO_DESCRIPTIONS,
    IfpriScenario,
    apply_ifpri_scenario_closure,
    build_and_solve_ifpri_scenarios,
    build_ifpri_scenario_model,
    normalize_ifpri_scenario,
    solve_ifpri_scenario,
)
from .reporting import (
    compare_ifpri_models,
    compare_ifpri_scenarios,
    extract_ifpri_solution,
    summarize_ifpri_results,
)
from .solve import (
    IfpriReferenceComparison,
    IfpriSolveReport,
    apply_ifpri_base_closure,
    build_ifpri_base_solve_model,
    compare_ifpri_model_to_reference,
    ifpri_degrees_of_freedom,
    load_ifpri_reference_targets,
    perturb_ifpri_start,
    solve_ifpri_base,
)
from .schema import (
    IfpriBenchmarkCalibration,
    IfpriBenchmarkPrices,
    IfpriBenchmarkQuantities,
    IfpriCalibrationInputs,
    IfpriDataset,
    IfpriElasticities,
    IfpriFactorQuantities,
    IfpriHomeConsumption,
    IfpriInstitutionCalibration,
    IfpriLesCalibration,
    IfpriProductionCalibration,
    IfpriSystemCalibration,
    IfpriTaxCalibration,
    IfpriSam,
    IfpriSets,
    IfpriTaxData,
)
from .synthetic import build_synthetic_ifpri_dataset
from .validation import (
    IfpriDataError,
    validate_dataset,
    validate_inputs,
    validate_sam,
    validate_sets,
)

__all__ = [
    "IFPRI_POLICY_SCENARIOS", "IFPRI_SCENARIO_DESCRIPTIONS",
    "IfpriBenchmarkCalibration", "IfpriBenchmarkPrices", "IfpriBenchmarkQuantities",
    "IfpriCalibrationInputs", "IfpriDataError", "IfpriDataset", "IfpriElasticities",
    "IfpriFactorQuantities", "IfpriHomeConsumption", "IfpriInstitutionCalibration",
    "IfpriLesCalibration", "IfpriProductionCalibration", "IfpriResidualReport",
    "IfpriReferenceComparison", "IfpriScenario", "IfpriSolveReport",
    "IfpriSystemCalibration", "IfpriTaxCalibration", "IfpriSam", "IfpriSets",
    "IfpriTaxData", "apply_ifpri_base_closure", "apply_ifpri_scenario_closure",
    "build_and_solve_ifpri_scenarios", "build_ifpri_base_solve_model",
    "build_ifpri_benchmark_model", "build_ifpri_scenario_model",
    "build_synthetic_ifpri_dataset", "calibrate_ifpri_benchmark",
    "compare_ifpri_model_to_reference", "compare_ifpri_models",
    "compare_ifpri_scenarios", "extract_ifpri_solution", "ifpri_benchmark_residuals",
    "ifpri_degrees_of_freedom", "load_ifpri_reference_targets", "load_ifpri_test_data",
    "normalize_ifpri_scenario", "parse_ifpri_test_dat", "perturb_ifpri_start",
    "resolve_ifpri_source", "solve_ifpri_base", "solve_ifpri_scenario",
    "summarize_ifpri_benchmark_residuals", "summarize_ifpri_results",
    "validate_dataset", "validate_ifpri_benchmark_model", "validate_ifpri_calibration",
    "validate_inputs", "validate_sam", "validate_sets",
]
