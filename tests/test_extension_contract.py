"""Contract tests for downstream use of the v0.6 public CGE facade."""
from pathlib import Path

import pandas as pd

from cge_core import CGE, Equilibrium, Result, Scenario, example_data
from cge_core.models import StdCGE

from ._util import SOLVER, requires_solver

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DOC = ROOT / "docs" / "developer" / "extension-contract.md"


def test_extension_contract_is_documented_as_public_boundary():
    text = CONTRACT_DOC.read_text(encoding="utf-8")

    for public_name in (
        "cge_core.CGE",
        "cge_core.Equilibrium",
        "cge_core.Scenario",
        "cge_core.Result",
        "cge_core.models.SplCGE",
        "cge_core.models.StdCGE",
    ):
        assert public_name in text

    for excluded in (
        "cge_core.engine.PyCGE",
        "Equilibrium._engine",
        "Result._snapshot",
        "universal `Closure` object",
    ):
        assert excluded in text

    normalized = " ".join(text.split())
    assert "Repeated `set()` -> `solve()` cycles are part of the contract." in normalized
    assert "Previously returned `Result` objects remain unchanged." in normalized


def test_extension_contract_imports_are_available_from_public_namespaces():
    assert CGE is not None
    assert Equilibrium is not None
    assert Scenario is not None
    assert Result is not None
    assert callable(example_data)
    assert StdCGE is not None


@requires_solver
def test_downstream_lifecycle_supports_repeat_solve_and_immutable_results():
    model = CGE(model=StdCGE(), data=example_data("stdcge"))
    benchmark = model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=SOLVER,
    )

    assert isinstance(benchmark, Equilibrium)
    tariff_brd = benchmark.value("taum", "BRD")
    tariff_mlk = benchmark.value("taum", "MLK")

    scenario = benchmark.scenario("downstream contract")
    assert isinstance(scenario, Scenario)

    scenario.set("taum", "BRD", 0.0)
    first = scenario.solve(solver=SOLVER)
    assert isinstance(first, Result)
    assert first.value("taum", "BRD") == 0.0
    assert first.value("taum", "MLK") == tariff_mlk

    first_table = first.compare(benchmark)
    assert isinstance(first_table, pd.DataFrame)
    assert not first_table.empty
    assert {
        "component",
        "reference_value",
        "value",
        "difference",
        "pct_change",
    }.issubset(first_table.columns)
    assert "objective" in first_table.attrs

    scenario.set("taum", "MLK", 0.0)
    second = scenario.solve(solver=SOLVER)

    assert second.value("taum", "BRD") == 0.0
    assert second.value("taum", "MLK") == 0.0

    assert first.value("taum", "BRD") == 0.0
    assert first.value("taum", "MLK") == tariff_mlk
    assert benchmark.value("taum", "BRD") == tariff_brd
    assert benchmark.value("taum", "MLK") == tariff_mlk
