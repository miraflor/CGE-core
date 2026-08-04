# -*- coding: utf-8 -*-
"""Public regression tests for IFPRI validation and solver hardening."""
from __future__ import annotations

from dataclasses import replace
import math

import pytest
from pyomo.environ import ConcreteModel, Constraint, Var, inequality
from pyomo.opt import SolverStatus, TerminationCondition

from cge_core.ifpri import IfpriDataError, validate_inputs, validate_sam
from cge_core.ifpri.solve import (
    _constraint_residual,
    _is_successful_termination,
)
from .synthetic import build_synthetic_ifpri_dataset

pytestmark = pytest.mark.public_ifpri


@pytest.fixture(scope="module")
def synthetic_dataset():
    return build_synthetic_ifpri_dataset()


def _validate_replacement(dataset, **input_changes) -> None:
    inputs = replace(dataset.inputs, **input_changes)
    validate_inputs(inputs, dataset.sets, dataset.sam)


@pytest.mark.parametrize(
    ("field", "key", "bad_value", "message"),
    (
        ("armington", "C", -0.1, "nonnegative"),
        ("factor_substitution", "A", 0.0, "strictly positive"),
        (
            "home_expenditure",
            ("A", "C", "HH"),
            0.0,
            "strictly positive",
        ),
    ),
)
def test_invalid_elasticity_ranges_are_rejected(
    synthetic_dataset,
    field,
    key,
    bad_value,
    message,
):
    elasticities = synthetic_dataset.inputs.elasticities
    values = dict(getattr(elasticities, field))
    values[key] = bad_value
    invalid = replace(elasticities, **{field: values})

    with pytest.raises(IfpriDataError, match=message):
        _validate_replacement(synthetic_dataset, elasticities=invalid)


@pytest.mark.parametrize(
    ("bad_value", "message"),
    (
        (math.nan, "not finite"),
        (1.1, "between zero and one"),
    ),
)
def test_invalid_home_shares_are_rejected(
    synthetic_dataset,
    bad_value,
    message,
):
    home = replace(
        synthetic_dataset.inputs.home_consumption,
        value_shares={("A", "C", "HH"): bad_value},
    )

    with pytest.raises(IfpriDataError, match=message):
        _validate_replacement(synthetic_dataset, home_consumption=home)


@pytest.mark.parametrize(
    ("field", "key", "bad_value", "message"),
    (
        ("supply", "LAB", -1.0, "nonnegative"),
        ("demand", ("CAP", "A"), math.inf, "not finite"),
    ),
)
def test_invalid_factor_quantities_are_rejected(
    synthetic_dataset,
    field,
    key,
    bad_value,
    message,
):
    quantities = synthetic_dataset.inputs.factor_quantities
    values = dict(getattr(quantities, field))
    values[key] = bad_value
    invalid = replace(quantities, **{field: values})

    with pytest.raises(IfpriDataError, match=message):
        _validate_replacement(synthetic_dataset, factor_quantities=invalid)


def test_negative_validation_tolerances_are_rejected(synthetic_dataset):
    with pytest.raises(IfpriDataError, match="balance tolerance"):
        validate_sam(
            synthetic_dataset.sam,
            synthetic_dataset.sets.accounts,
            balance_tolerance=-1.0,
        )
    with pytest.raises(IfpriDataError, match="Input tolerance"):
        validate_inputs(
            synthetic_dataset.inputs,
            synthetic_dataset.sets,
            synthetic_dataset.sam,
            tolerance=-1.0,
        )


def test_constraint_residual_reports_only_actual_bound_violations():
    model = ConcreteModel()
    model.x = Var(initialize=2.0)
    model.equal = Constraint(expr=model.x == 2.0)
    model.lower = Constraint(expr=model.x >= 1.0)
    model.upper = Constraint(expr=model.x <= 3.0)
    model.ranged = Constraint(expr=inequality(0.0, model.x, 4.0))

    assert _constraint_residual(model.equal) == pytest.approx(0.0)
    assert _constraint_residual(model.lower) == pytest.approx(0.0)
    assert _constraint_residual(model.upper) == pytest.approx(0.0)
    assert _constraint_residual(model.ranged) == pytest.approx(0.0)

    model.x.set_value(5.0)
    assert _constraint_residual(model.equal) == pytest.approx(3.0)
    assert _constraint_residual(model.lower) == pytest.approx(0.0)
    assert _constraint_residual(model.upper) == pytest.approx(2.0)
    assert _constraint_residual(model.ranged) == pytest.approx(1.0)

    model.x.set_value(-1.0)
    assert _constraint_residual(model.equal) == pytest.approx(-3.0)
    assert _constraint_residual(model.lower) == pytest.approx(-2.0)
    assert _constraint_residual(model.upper) == pytest.approx(0.0)
    assert _constraint_residual(model.ranged) == pytest.approx(-1.0)


def test_merely_feasible_solver_termination_is_rejected():
    assert _is_successful_termination(
        SolverStatus.ok,
        TerminationCondition.optimal,
    )
    assert _is_successful_termination(
        SolverStatus.warning,
        TerminationCondition.locallyOptimal,
    )
    assert not _is_successful_termination(
        SolverStatus.ok,
        TerminationCondition.feasible,
    )
    assert not _is_successful_termination(
        SolverStatus.error,
        TerminationCondition.optimal,
    )
