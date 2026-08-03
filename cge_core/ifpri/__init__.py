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
from .validation import (
    IfpriDataError,
    validate_dataset,
    validate_inputs,
    validate_sam,
    validate_sets,
)

__all__ = [
    "IfpriBenchmarkCalibration",
    "IfpriBenchmarkPrices",
    "IfpriBenchmarkQuantities",
    "IfpriCalibrationInputs",
    "IfpriDataError",
    "IfpriDataset",
    "IfpriElasticities",
    "IfpriFactorQuantities",
    "IfpriHomeConsumption",
    "IfpriInstitutionCalibration",
    "IfpriLesCalibration",
    "IfpriProductionCalibration",
    "IfpriResidualReport",
    "IfpriSystemCalibration",
    "IfpriTaxCalibration",
    "IfpriSam",
    "IfpriSets",
    "IfpriTaxData",
    "build_ifpri_benchmark_model",
    "calibrate_ifpri_benchmark",
    "ifpri_benchmark_residuals",
    "load_ifpri_test_data",
    "parse_ifpri_test_dat",
    "resolve_ifpri_source",
    "summarize_ifpri_benchmark_residuals",
    "validate_dataset",
    "validate_ifpri_benchmark_model",
    "validate_ifpri_calibration",
    "validate_inputs",
    "validate_sam",
    "validate_sets",
]
