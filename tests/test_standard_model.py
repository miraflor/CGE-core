# -*- coding: utf-8 -*-
"""
Regression and correctness tests for the standard CGE model (Hosoe Ch. 6).

These tests encode the properties that must hold for the model to be a
faithful, correctly-solving implementation of Hosoe's stdcge:

  1. The abstract model builds and a concrete instance can be created.
  2. The assembled system is over-determined by exactly one equation
     (Walras' law) before the redundant equation is dropped.
  3. After dropping one market-clearing equation the system is square.
  4. The base case calibrates to the SAM-consistent equilibrium.
  5. The solver recovers that equilibrium from a perturbed starting point
     (i.e. it is genuinely solving, not echoing initial values).
  6. The dropped market clears automatically at the solution (Walras' law).
  7. Abolishing import tariffs raises welfare (the canonical Hosoe result),
     driven through the documented public API.

A local NLP solver is required. The tests auto-detect 'ipopt' (executable)
or 'cyipopt' (PyNumero) and skip if neither is available.
"""
import pytest

from pyomo.environ import Constraint, Var, value

from ._util import (SOLVER, calibrated, dof, quiet, requires_solver,
                    std_instance)

# SAM-consistent base equilibrium (from Hosoe's standard SAM)
EXPECTED_BASE = {
    ('Z', 'BRD'): 73.0, ('Z', 'MLK'): 72.0,
    ('Xp', 'BRD'): 20.0, ('Xp', 'MLK'): 30.0,
    ('M', 'BRD'): 13.0, ('M', 'MLK'): 11.0,
    ('E', 'BRD'): 8.0,  ('E', 'MLK'): 4.0,
}


# ----------------------------------------------------------------------
# Structural tests (no solver required)
# ----------------------------------------------------------------------
def test_instance_builds():
    cge = std_instance(drop_redundant=False)
    assert cge.base is not None
    n_con = sum(len(c) for c in cge.base.component_objects(Constraint))
    assert n_con == 48          # 24 constraint blocks expand to 48 scalars


def test_overdetermined_before_drop():
    """Before dropping a redundant equation, DOF must be exactly -1."""
    cge = std_instance(drop_redundant=False)
    assert dof(cge.base) == -1


def test_square_after_drop():
    """After dropping one market clearing, DOF must be 0."""
    cge = std_instance(drop_redundant=True)
    assert dof(cge.base) == 0


def test_numeraire_is_fixed():
    """model_instance must actually fix the numeraire it reports fixing."""
    cge = std_instance(drop_redundant=False)
    assert cge.base.pf['LAB'].fixed is True
    assert value(cge.base.pf['LAB']) == pytest.approx(1.0)


# ----------------------------------------------------------------------
# Solver tests
# ----------------------------------------------------------------------
@requires_solver
def test_base_reproduces_sam():
    cge = calibrated()
    for (var, idx), target in EXPECTED_BASE.items():
        got = value(getattr(cge.base, var)[idx])
        assert got == pytest.approx(target, abs=1e-4), \
            "%s[%s] = %r, expected %r" % (var, idx, got, target)


@requires_solver
def test_solver_recovers_from_perturbation():
    """Perturb all free vars +50%; solver must still recover the SAM."""
    cge = std_instance()
    for v in cge.base.component_objects(Var, active=True):
        for i in v:
            if v[i].value is not None and not v[i].fixed:
                v[i].value = v[i].value * 1.5
    with quiet():
        cge.model_calibrate(SOLVER)
    for (var, idx), target in EXPECTED_BASE.items():
        got = value(getattr(cge.base, var)[idx])
        assert got == pytest.approx(target, abs=1e-3), \
            "%s[%s] = %r, expected %r" % (var, idx, got, target)


@requires_solver
def test_walras_dropped_market_clears():
    """The deactivated labor market must clear automatically at solution."""
    cge = calibrated()
    b = cge.base
    supply = value(b.FF['LAB'])
    demand = sum(value(b.F['LAB', i]) for i in b.i)
    assert demand == pytest.approx(supply, abs=1e-6)


@requires_solver
def test_tariff_abolition_raises_welfare():
    """Canonical Hosoe result, driven through the documented public API.

    Deliberately uses model_sim/model_modify_sim/model_solve rather than
    reaching past them with deepcopy, so the workflow the README teaches
    is the workflow under test.
    """
    cge = calibrated()
    u_base = value(cge.base.obj)

    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_modify_sim('taum', 'MLK', 0)
        cge.model_solve(SOLVER)

    u_sim = value(cge.sim.obj)
    assert u_sim > u_base        # removing distortion improves welfare


@requires_solver
def test_sim_does_not_mutate_base():
    """Solving the counterfactual must leave the calibrated base intact."""
    cge = calibrated()
    base_before = {(str(v), i): value(v[i])
                   for v in cge.base.component_objects(Var, active=True)
                   for i in v}
    with quiet():
        cge.model_sim()
        cge.model_modify_sim('taum', 'BRD', 0)
        cge.model_solve(SOLVER)

    for (name, i), before in base_before.items():
        after = value(getattr(cge.base, name)[i])
        assert after == pytest.approx(before, abs=1e-9), \
            "base %s[%s] moved during the sim solve" % (name, i)


def test_standard_variables_have_reference_lower_bounds():
    cge = std_instance(drop_redundant=False)
    for component in cge.base.component_objects(Var):
        for item in component.values():
            if str(component) in {'Tz', 'Tm'}:
                assert value(item.lb) == pytest.approx(0.0)
            else:
                assert value(item.lb) == pytest.approx(1e-5)
