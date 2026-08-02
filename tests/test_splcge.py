# -*- coding: utf-8 -*-
"""
Correctness tests for the simple CGE model (Hosoe Ch. 3-4).

splcge is a closed economy with Cobb-Douglas production and utility:
goods {BRD, MLK}, factors {CAP, LAB}. It carries the same Walras'-law
redundancy as stdcge, so it needs the same degree-of-freedom treatment.

These tests exist because splcge was modified in the v0.2.0 fork
(``np.prod`` replaced with Pyomo's ``prod`` in the production function,
the scale-parameter calibration, and the objective) but shipped with no
tests. The np.prod change in particular is silent when wrong -- NumPy's
``__mul__`` delegation can build an expression that looks fine and
solves to the wrong point -- so the SAM-reproduction test below is the
guard that matters.
"""
import pytest

from pyomo.environ import Constraint, Var, value

from ._util import (SOLVER, calibrated, dof, quiet, requires_solver,
                    spl_instance)

# The splcge SAM: household consumption X0 = (15, 35), factor endowments
# FF = (CAP 25, LAB 25). A correct calibration reproduces these exactly
# with all prices at unity.
EXPECTED_BASE = {
    ('X', 'BRD'): 15.0, ('X', 'MLK'): 35.0,
    ('Z', 'BRD'): 15.0, ('Z', 'MLK'): 35.0,
}
EXPECTED_PRICES = {
    ('px', 'BRD'): 1.0, ('px', 'MLK'): 1.0,
    ('pz', 'BRD'): 1.0, ('pz', 'MLK'): 1.0,
    ('pf', 'CAP'): 1.0, ('pf', 'LAB'): 1.0,
}


# ----------------------------------------------------------------------
# Structural tests (no solver required)
# ----------------------------------------------------------------------
def test_instance_builds():
    cge = spl_instance(drop_redundant=False)
    assert cge.base is not None
    n_con = sum(len(c) for c in cge.base.component_objects(Constraint))
    assert n_con == 14          # 6 constraint blocks expand to 14 scalars


def test_overdetermined_before_drop():
    """splcge carries the same Walras' law redundancy as stdcge."""
    cge = spl_instance(drop_redundant=False)
    assert dof(cge.base) == -1


def test_square_after_drop():
    cge = spl_instance(drop_redundant=True)
    assert dof(cge.base) == 0


def test_numeraire_is_fixed():
    cge = spl_instance(drop_redundant=False)
    assert cge.base.pf['LAB'].fixed is True


# ----------------------------------------------------------------------
# Solver tests
# ----------------------------------------------------------------------
@requires_solver
def test_base_reproduces_sam():
    """Quantities must return the SAM. Guards the np.prod -> prod change."""
    cge = calibrated(spl_instance)
    for (var, idx), target in EXPECTED_BASE.items():
        got = value(getattr(cge.base, var)[idx])
        assert got == pytest.approx(target, abs=1e-6), \
            "%s[%s] = %r, expected %r" % (var, idx, got, target)


@requires_solver
def test_base_prices_are_unity():
    """At the calibration point every price equals the numeraire."""
    cge = calibrated(spl_instance)
    for (var, idx), target in EXPECTED_PRICES.items():
        got = value(getattr(cge.base, var)[idx])
        assert got == pytest.approx(target, abs=1e-6), \
            "%s[%s] = %r, expected %r" % (var, idx, got, target)


@requires_solver
def test_solver_recovers_from_perturbation():
    """Perturb all free vars +50%; the solver must still find the SAM."""
    cge = spl_instance()
    for v in cge.base.component_objects(Var, active=True):
        for i in v:
            if v[i].value is not None and not v[i].fixed:
                v[i].value = v[i].value * 1.5
    with quiet():
        cge.model_calibrate(SOLVER)
    for (var, idx), target in EXPECTED_BASE.items():
        got = value(getattr(cge.base, var)[idx])
        assert got == pytest.approx(target, abs=1e-4), \
            "%s[%s] = %r, expected %r" % (var, idx, got, target)


@requires_solver
def test_walras_dropped_market_clears():
    """The deactivated labour market clears automatically at the solution."""
    cge = calibrated(spl_instance)
    b = cge.base
    supply = value(b.FF['LAB'])
    demand = sum(value(b.F['LAB', i]) for i in b.i)
    assert demand == pytest.approx(supply, abs=1e-6)


@requires_solver
def test_goods_markets_clear():
    """Supply equals demand for every good (X == Z)."""
    cge = calibrated(spl_instance)
    b = cge.base
    for i in b.i:
        assert value(b.X[i]) == pytest.approx(value(b.Z[i]), abs=1e-6)


@requires_solver
def test_factor_income_exhausts_output():
    """Zero profit: factor payments must exhaust the value of output."""
    cge = calibrated(spl_instance)
    b = cge.base
    output = sum(value(b.pz[i]) * value(b.Z[i]) for i in b.i)
    payments = sum(value(b.pf[h]) * value(b.F[h, i])
                   for h in b.h for i in b.i)
    assert payments == pytest.approx(output, abs=1e-6)


def test_bundled_simple_sam_is_balanced():
    import csv
    from ._util import SPL_DATA_DIR

    with open(SPL_DATA_DIR + '/param-sam-.csv', newline='') as handle:
        rows = list(csv.reader(handle))
    matrix = [[float(cell) for cell in row[1:]] for row in rows[1:]]
    row_totals = [sum(row) for row in matrix]
    col_totals = [sum(matrix[r][c] for r in range(len(matrix)))
                  for c in range(len(matrix))]
    assert row_totals == pytest.approx(col_totals)
    assert rows[-1] == ['HOH', '0', '0', '25', '25', '0']


def test_simple_variables_have_reference_lower_bound():
    cge = spl_instance(drop_redundant=False)
    for component in cge.base.component_objects(Var):
        for item in component.values():
            assert value(item.lb) == pytest.approx(1e-3)
