# -*- coding: utf-8 -*-
"""Execution guards for the canonical v0.6 Hosoe example scripts."""
import pytest

from cge_core.examples import splcge, stdcge

from ._util import SOLVER, quiet, requires_solver


@requires_solver
def test_simple_example_runs_through_v06_facade():
    with quiet():
        benchmark = splcge.main(SOLVER)

    assert benchmark.value("Z", "BRD") == pytest.approx(15.0, abs=1e-6)
    assert benchmark.value("Z", "MLK") == pytest.approx(35.0, abs=1e-6)


@requires_solver
def test_standard_example_runs_independent_v06_scenarios():
    with quiet():
        benchmark, tariff, production_tax = stdcge.main(SOLVER)

    assert tariff.objective is not None
    assert production_tax.objective is not None
    assert tariff.value("taum", "BRD") == pytest.approx(0.0)
    assert production_tax.value("tauz", "BRD") == pytest.approx(0.0)
    assert benchmark.value("taum", "BRD") > 0
    assert benchmark.value("tauz", "BRD") > 0
