# -*- coding: utf-8 -*-
"""
Shared helpers for the CGE-Core test suite.

Centralises local-solver detection, data-directory resolution, and the
instance-construction boilerplate so the individual test modules assert
behaviour rather than repeat setup.
"""
import contextlib
import io
import os

import pytest

DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'cge_core', 'data')
STD_DATA_DIR = os.path.join(DATA_ROOT, 'stdcge_data_dir')
SPL_DATA_DIR = os.path.join(DATA_ROOT, 'splcge_data_dir')


def _available_solver():
    """Return a solver this machine can run, or ``None`` if there is none.

    This gate decides whether the solver-dependent tests run or are skipped, so
    it has to ask the same question the product asks.  It previously used a
    narrower search that knew about only two of the four supported backends,
    which meant that on a machine relying on either of the other two the whole
    solver half of the suite skipped silently while the package itself worked.
    Continuous integration never showed this, because it installs a solver the
    narrow search does recognise.
    """
    from cge_core.solver import SolverResolutionError, resolve_solver

    try:
        return resolve_solver()
    except SolverResolutionError:
        return None


SOLVER = _available_solver()

requires_solver = pytest.mark.skipif(
    SOLVER is None, reason="no local NLP solver (ipopt/cyipopt) available")


@contextlib.contextmanager
def quiet():
    """Swallow explicitly requested stdout displays.

    As of v0.3.0 the engine reports progress via logging (silent under
    pytest by default), so this only matters around display calls such
    as ``model_compare('print')``; it is retained where harmless.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


def std_instance(drop_redundant=True, quiet_setup=True):
    """Build a stdcge PyCGE with the numeraire fixed (Hosoe: pf_LAB = 1)."""
    from cge_core._pycge import PyCGE
    from cge_core.models.standard.model import StdModelDef

    ctx = quiet() if quiet_setup else contextlib.nullcontext()
    with ctx:
        cge = PyCGE(StdModelDef())
        cge.model_data(STD_DATA_DIR)
        cge.model_instance('pf', 'LAB')
        if drop_redundant:
            cge.model_drop_redundant('eqpf', 'LAB')
    return cge


def spl_instance(drop_redundant=True, quiet_setup=True):
    """Build a splcge PyCGE with the numeraire fixed (pf_LAB = 1)."""
    from cge_core._pycge import PyCGE
    from cge_core.models.simple.model import SplModelDef

    ctx = quiet() if quiet_setup else contextlib.nullcontext()
    with ctx:
        cge = PyCGE(SplModelDef())
        cge.model_data(SPL_DATA_DIR)
        cge.model_instance('pf', 'LAB')
        if drop_redundant:
            cge.model_drop_redundant('eqpf', 'LAB')
    return cge


def calibrated(builder=std_instance):
    """Return a calibrated instance built by ``builder``."""
    cge = builder()
    with quiet():
        cge.model_calibrate(SOLVER)
    return cge


def dof(instance):
    """Degrees of freedom: free variables minus active equality constraints."""
    from pyomo.environ import Constraint, Var

    free = sum(1 for v in instance.component_data_objects(Var, active=True)
               if not v.fixed)
    con = sum(1 for _ in instance.component_data_objects(Constraint,
                                                         active=True))
    return free - con
