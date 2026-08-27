# -*- coding: utf-8 -*-
"""Behavioral contract tests for the additive CGE-Core v0.6 facade.

These tests sit beside, rather than replace, the legacy PyCGE suite.  The old
workflow remains the numerical oracle for interface-translation parity while
the published benchmark tests remain the oracle for the shared engine itself.
"""
import copy
import math

import pytest
from pyomo.environ import Var, value

from cge_core import CGE, ComponentError, PyCGE, Result, WorkflowError
from cge_core.models import SplCGE, StdCGE

from ._util import (
    SOLVER, SPL_DATA_DIR, STD_DATA_DIR, calibrated, quiet, requires_solver,
)

# Separate nonlinear solves should agree extremely tightly, but the contract
# intentionally does not require cross-platform bit-for-bit identity.
FACADE_PARITY_REL = 1e-9
FACADE_PARITY_ABS = 1e-9


def _std_model():
    return CGE(model=StdCGE(), data=STD_DATA_DIR)


def _std_benchmark():
    return _std_model().solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )


def _spl_benchmark():
    return CGE(model=SplCGE(), data=SPL_DATA_DIR).solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )


def _result_value(result, component, index):
    if index is None:
        return result.value(component)
    if isinstance(index, tuple):
        return result.value(component, *index)
    return result.value(component, index)


def test_new_root_and_model_namespace_imports():
    assert CGE is not PyCGE
    assert Result.__name__ == "Result"
    # Import-facade aliases preserve the validated implementation classes.
    assert StdCGE.__name__ == "StdModelDef"
    assert SplCGE.__name__ == "SplModelDef"


@requires_solver
def test_benchmark_value_access_scalar_indexed_and_multidimensional():
    benchmark = _std_benchmark()
    assert benchmark.value("epsilon") == pytest.approx(1.0, abs=1e-8)
    assert benchmark.value("Z", "BRD") == pytest.approx(73.0, abs=1e-4)
    assert benchmark.value("F", "LAB", "BRD") > 0
    assert benchmark.value("taum", "BRD") > 0

    with pytest.raises(ComponentError):
        benchmark.value("does_not_exist")
    with pytest.raises(ComponentError):
        benchmark.value("Z")
    with pytest.raises(ComponentError):
        benchmark.value("Z", "NOT_A_GOOD")


@requires_solver
def test_cge_is_blueprint_repeated_benchmarks_do_not_overwrite_each_other():
    model = _std_model()
    first = model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )
    first_z = first.value("Z", "BRD")

    second = model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )

    assert first is not second
    assert first.value("Z", "BRD") == pytest.approx(first_z, abs=0.0)
    assert second.value("Z", "BRD") == pytest.approx(first_z, abs=1e-9)


@requires_solver
def test_benchmarks_with_different_numeraires_coexist_independently():
    model = _std_model()
    labor = model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )
    capital = model.solve_benchmark(
        numeraire=("pf", "CAP"),
        redundant=("eqpf", "CAP"),
        solver=SOLVER,
    )

    # Private-engine inspection is intentional here: this is an ownership
    # regression test for the closure state, not part of the public API.
    assert labor._engine.base.pf["LAB"].fixed is True
    assert labor._engine.base.pf["CAP"].fixed is False
    assert capital._engine.base.pf["CAP"].fixed is True
    assert capital._engine.base.pf["LAB"].fixed is False

    # Constructing the second benchmark must not rewrite the first one's
    # solved public snapshot or closure state.
    assert labor.value("pf", "LAB") == pytest.approx(1.0, abs=1e-9)
    assert capital.value("pf", "CAP") == pytest.approx(1.0, abs=1e-9)


@requires_solver
def test_whole_calibrated_engine_copy_is_independent_and_solvable():
    legacy = calibrated()
    copied = copy.deepcopy(legacy)

    with quiet():
        copied.model_sim()
        copied.model_modify_sim("taum", "BRD", 0)
        copied.model_modify_sim("taum", "MLK", 0)
        copied.model_solve(SOLVER)

        legacy.model_sim()
        legacy.model_modify_sim("taum", "BRD", 0)
        legacy.model_modify_sim("taum", "MLK", 0)
        legacy.model_solve(SOLVER)

    assert value(copied.base.taum["BRD"]) > 0
    assert value(legacy.base.taum["BRD"]) > 0
    assert value(copied.sim.taum["BRD"]) == pytest.approx(0.0)
    assert value(legacy.sim.taum["BRD"]) == pytest.approx(0.0)
    assert value(copied.sim.Z["BRD"]) == pytest.approx(
        value(legacy.sim.Z["BRD"]),
        rel=FACADE_PARITY_REL,
        abs=FACADE_PARITY_ABS,
    )


@requires_solver
def test_two_public_scenarios_are_independent_and_leave_benchmark_unchanged():
    benchmark = _std_benchmark()
    benchmark_tariff = benchmark.value("taum", "BRD")

    abolished = benchmark.scenario("abolished")
    partial = benchmark.scenario("partial")

    abolished.set("taum", "BRD", 0)
    partial.set("taum", "BRD", benchmark_tariff * 0.5)

    result_a = abolished.solve(solver=SOLVER)
    result_b = partial.solve(solver=SOLVER)

    assert result_a.value("taum", "BRD") == pytest.approx(0.0)
    assert result_b.value("taum", "BRD") == pytest.approx(
        benchmark_tariff * 0.5
    )
    assert benchmark.value("taum", "BRD") == pytest.approx(benchmark_tariff)
    assert result_a.value("Z", "BRD") != pytest.approx(
        result_b.value("Z", "BRD"), abs=1e-10
    )


@requires_solver
def test_three_scenarios_can_coexist():
    benchmark = _std_benchmark()
    original = benchmark.value("taum", "BRD")
    scenarios = [benchmark.scenario(name) for name in ("A", "B", "C")]
    targets = (0.0, original * 0.5, original)

    results = []
    for scenario, target in zip(scenarios, targets):
        scenario.set("taum", "BRD", target)
        results.append(scenario.solve(solver=SOLVER))

    assert [r.value("taum", "BRD") for r in results] == pytest.approx(targets)
    assert benchmark.value("taum", "BRD") == pytest.approx(original)


@requires_solver
def test_modify_solve_modify_solve_and_old_result_is_immutable():
    benchmark = _std_benchmark()
    scenario = benchmark.scenario("tariff sweep")

    scenario.set("taum", "BRD", 0.10)
    first = scenario.solve(solver=SOLVER)
    first_z = first.value("Z", "BRD")

    scenario.set("taum", "BRD", 0.00)
    second = scenario.solve(solver=SOLVER)

    assert first.value("Z", "BRD") == pytest.approx(first_z, abs=0.0)
    assert second.value("taum", "BRD") == pytest.approx(0.0)
    assert second.value("Z", "BRD") != pytest.approx(first_z, abs=1e-10)


@requires_solver
def test_unfix_contract_is_limited_to_variables_fixed_by_this_scenario():
    benchmark = _std_benchmark()
    scenario = benchmark.scenario("release test")

    with pytest.raises(ComponentError, match="exogenous as a parameter"):
        scenario.unfix("Sf")

    with pytest.raises(ComponentError, match="was not fixed by set"):
        scenario.unfix("epsilon")

    scenario.set("epsilon", None, 1.0)
    scenario.unfix("epsilon")
    # Returning epsilon to endogenous status restores the original square
    # benchmark closure, so the scenario can solve normally.
    result = scenario.solve(solver=SOLVER)
    assert result.value("epsilon") == pytest.approx(1.0, abs=1e-6)


@requires_solver
def test_incomplete_closure_fails_before_solver():
    benchmark = _std_benchmark()
    scenario = benchmark.scenario("bad closure")
    scenario.set("epsilon", None, 1.0)

    with pytest.raises(WorkflowError, match="degrees of freedom"):
        scenario.solve(solver=SOLVER)


@requires_solver
def test_new_facade_tariff_abolition_matches_legacy_numerically():
    legacy = calibrated()
    with quiet():
        legacy.model_sim()
        legacy.model_modify_sim("taum", "BRD", 0)
        legacy.model_modify_sim("taum", "MLK", 0)
        legacy.model_solve(SOLVER)

    benchmark = _std_benchmark()
    scenario = benchmark.scenario("tariff abolition")
    scenario.set("taum", "BRD", 0)
    scenario.set("taum", "MLK", 0)
    result = scenario.solve(solver=SOLVER)

    for component in legacy.sim.component_objects(Var, active=True):
        for index in component:
            expected = value(component[index])
            got = _result_value(result, str(component), index)
            assert got == pytest.approx(
                expected,
                rel=FACADE_PARITY_REL,
                abs=FACADE_PARITY_ABS,
            ), f"{component}[{index}] drifted through the facade"

    assert result.objective == pytest.approx(
        value(legacy.sim.obj),
        rel=FACADE_PARITY_REL,
        abs=FACADE_PARITY_ABS,
    )


@requires_solver
def test_compare_preserves_legacy_direction_and_objective_sign():
    benchmark = _std_benchmark()
    scenario = benchmark.scenario("tariff abolition")
    scenario.set("taum", "BRD", 0)
    scenario.set("taum", "MLK", 0)
    result = scenario.solve(solver=SOLVER)

    frame = result.compare(benchmark)
    brd = frame[(frame.component == "Z") & (frame.index_1 == "BRD")].iloc[0]
    expected_difference = result.value("Z", "BRD") - benchmark.value("Z", "BRD")
    assert brd["difference"] == pytest.approx(expected_difference)
    # Bracket access is required: pandas Series.pct_change is a method.
    assert brd["pct_change"] == pytest.approx(
        expected_difference / benchmark.value("Z", "BRD") * 100.0
    )
    assert frame.attrs["objective"]["difference"] == pytest.approx(
        result.objective - benchmark.objective
    )


@requires_solver
def test_compare_rejects_different_model_definitions():
    std_benchmark = _std_benchmark()
    std_result = std_benchmark.scenario("identity").solve(solver=SOLVER)
    spl_benchmark = _spl_benchmark()

    with pytest.raises(WorkflowError, match="different model definitions"):
        std_result.compare(spl_benchmark)


def test_compare_zero_reference_percentage_is_nan():
    # Narrow unit test of the documented comparison formula; construction of
    # Result remains non-public, but this avoids requiring a particular model
    # variable to happen to have a zero benchmark level.
    from types import MappingProxyType
    from cge_core.api import _Snapshot

    reference = Result(_snapshot=_Snapshot(
        model_id="test",
        label="benchmark",
        variables=MappingProxyType({("x", ()): 0.0}),
        parameters=MappingProxyType({}),
        objective=1.0,
        solver=MappingProxyType({}),
    ))
    current = Result(_snapshot=_Snapshot(
        model_id="test",
        label="scenario",
        variables=MappingProxyType({("x", ()): 1.0}),
        parameters=MappingProxyType({}),
        objective=2.0,
        solver=MappingProxyType({}),
    ))

    frame = current.compare(reference)
    assert math.isnan(frame.loc[0, "pct_change"])
