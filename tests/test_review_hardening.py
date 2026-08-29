"""Regression tests retained after the independent adversarial review."""
import pytest

import cge_core.solvers as solver_resolution
import tests._util as test_util
from cge_core.engine import DataValidationError, PyCGE, SolveError
from cge_core.examples.stdcge_model_def import StdModelDef


def test_model_instance_wraps_zero_division_as_data_error(monkeypatch):
    cge = PyCGE(StdModelDef())
    cge.data = object()

    def fail_calibration(self, *args, **kwargs):
        raise ZeroDivisionError("division by zero")

    monkeypatch.setattr(type(cge.m), "create_instance", fail_calibration)
    with pytest.raises(DataValidationError, match="benchmark flow"):
        cge.model_instance("pf", "LAB")
    assert cge.base is None


def test_cyipopt_probe_rejects_missing_scipy(monkeypatch):
    class ReportedAvailable:
        def available(self, exception_flag=False):
            return True

    monkeypatch.setattr(
        "pyomo.environ.SolverFactory", lambda name: ReportedAvailable()
    )
    real_find_spec = solver_resolution.importlib.util.find_spec

    def find_spec_without_scipy(name):
        if name == "scipy":
            return None
        return real_find_spec(name)

    monkeypatch.setattr(
        solver_resolution.importlib.util, "find_spec", find_spec_without_scipy
    )
    assert solver_resolution._probe("cyipopt") is False
    with pytest.raises(SolveError, match="cyipopt"):
        PyCGE._available_solver("cyipopt")


def test_test_suite_solver_probe_delegates_to_engine(monkeypatch):
    calls = []

    def available(preferred=None):
        calls.append(preferred)
        return "ipopt"

    monkeypatch.setattr(PyCGE, "_available_solver", staticmethod(available))
    assert test_util._available_solver() == "ipopt"
    assert calls == [None]

    def unavailable(preferred=None):
        raise SolveError("no usable solver")

    monkeypatch.setattr(PyCGE, "_available_solver", staticmethod(unavailable))
    assert test_util._available_solver() is None
