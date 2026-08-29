"""Published-solution and policy-experiment regression tests for CAMCGE."""
from __future__ import annotations

import pytest

from validation.cam.replicate_base import base_metrics, build_base, validate_base
from validation.cam.replicate_experiments import (
    experiment_1,
    experiment_2,
    experiment_3,
    snapshot,
)
from .._util import SOLVER, requires_solver


@pytest.fixture(scope="module")
def calibrated_cam():
    cge, dof_before, dof_after = build_base(SOLVER)
    return cge, dof_before, dof_after


@requires_solver
def test_base_reproduces_published_1987_solution(calibrated_cam):
    cge, dof_before, dof_after = calibrated_cam
    metrics = base_metrics(cge, dof_before, dof_after)
    validate_base(metrics)
    assert metrics["published_level_count"] == 98
    assert metrics["worst_level_difference"] < 5e-3
    assert abs(metrics["current_account_gap"]) < 1e-8


@requires_solver
def test_published_policy_experiments(calibrated_cam):
    cge, _, _ = calibrated_cam
    base = snapshot(cge.base)
    exp1 = experiment_1(cge, base, SOLVER)
    exp2 = experiment_2(cge, base, SOLVER)
    exp3 = experiment_3(cge, base, SOLVER)
    assert abs(exp1["gap"]) < 1e-8
    assert abs(exp2["gap"]) < 1e-8
    assert abs(exp3["gap"]) < 1e-8
