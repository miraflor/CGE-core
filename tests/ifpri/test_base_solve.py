# -*- coding: utf-8 -*-
from pathlib import Path

import pytest
from pyomo.environ import value

from cge_core.ifpri import (
    build_ifpri_base_solve_model,
    compare_ifpri_model_to_reference,
    ifpri_degrees_of_freedom,
    load_ifpri_reference_targets,
    load_ifpri_test_data,
    perturb_ifpri_start,
    solve_ifpri_base,
)
from .._util import SOLVER, requires_solver


@pytest.fixture
def closed_model(ifpri_source_dir):
    return build_ifpri_base_solve_model(load_ifpri_test_data(ifpri_source_dir))


def test_base_closure_is_square(closed_model):
    assert ifpri_degrees_of_freedom(closed_model) == 0
    assert closed_model.CPI.fixed
    assert closed_model.FSAV.fixed
    assert closed_model.IADJ.fixed
    assert closed_model.GADJ.fixed
    assert not closed_model.WALRAS.fixed
    assert not closed_model.WALRASSQR.fixed
    assert closed_model.walras_squared_definition.active
    assert closed_model.walras_objective.active
    assert closed_model.QFS["LAB"].fixed
    assert closed_model.WF["CAP"].fixed
    assert not closed_model.EXR.fixed
    assert not closed_model.DMPS.fixed


def test_structurally_absent_variables_are_fixed_at_zero(closed_model):
    assert closed_model.QD["CIMP"].fixed and value(closed_model.QD["CIMP"]) == 0
    assert closed_model.QM["CAGR3-EX"].fixed and value(closed_model.QM["CAGR3-EX"]) == 0
    assert closed_model.PM["CAGR3-EX"].fixed
    assert value(closed_model.PM["CAGR3-EX"]) == 1
    assert closed_model.QH["CIMP", "HURB"].fixed
    assert closed_model.QHA["AOSER", "COSER", "HURB"].fixed


def test_nlp_walras_objective_preserves_one_solver_degree(closed_model):
    from pyomo.environ import Constraint, Objective, Var

    free = sum(
        1 for item in closed_model.component_data_objects(Var, active=True)
        if not item.fixed
    )
    equations = sum(
        1 for _ in closed_model.component_data_objects(Constraint, active=True)
    )
    objectives = sum(
        1 for _ in closed_model.component_data_objects(Objective, active=True)
    )
    assert free - equations == 1
    assert objectives == 1
    assert ifpri_degrees_of_freedom(closed_model) == 0


def test_perturbation_moves_only_free_variables(closed_model):
    fixed_cpi = value(closed_model.CPI)
    old_exr = value(closed_model.EXR)
    perturb_ifpri_start(closed_model, 1.01)
    assert value(closed_model.CPI) == fixed_cpi
    assert value(closed_model.EXR) != old_exr


def test_reference_loader_reads_full_precision_base_targets():
    path = Path(__file__).resolve().parents[2] / "validation" / "gams" / "ifpri_standard" / "reference" / "full_precision_targets.csv"
    targets = load_ifpri_reference_targets(path, "NLP", "BASE")
    assert targets[("CPI", ())] == pytest.approx(1.3062011183426825)
    assert ("QA", ("AAGR1",)) in targets


@requires_solver
def test_ipopt_reproduces_gams_base_from_perturbed_start(closed_model):
    perturb_ifpri_start(closed_model, 1.02)
    report = solve_ifpri_base(closed_model, SOLVER)
    assert report.degrees_of_freedom == 0
    assert report.max_abs_equation_residual < 1e-6

    path = Path(__file__).resolve().parents[2] / "validation" / "gams" / "ifpri_standard" / "reference" / "full_precision_targets.csv"
    comparison = compare_ifpri_model_to_reference(
        closed_model, load_ifpri_reference_targets(path, "NLP", "BASE")
    )
    assert comparison.compared_values > 150
    assert comparison.max_abs_difference < 2e-5
    assert comparison.max_relative_difference < 2e-6
