# -*- coding: utf-8 -*-
"""
Standard CGE Example (Hosoe Ch. 6) -- tariff and tax abolition experiments.

Demonstrates the canonical CGE-Core v0.6 lifecycle:
    configure -> solve benchmark -> create isolated scenarios -> set shocks
    -> solve -> compare

Requires a local NLP solver ('ipopt' executable or 'cyipopt'); the example
detects whichever is available.

Run with:
    python -m cge_core.examples.stdcge
"""
import logging
from math import prod

from cge_core import CGE, example_data
from cge_core.examples._solver import detect_solver
from cge_core.models import StdCGE

DATA_DIR = example_data("stdcge")
GOODS = ("BRD", "MLK")


def build_benchmark(solver):
    """Return the solved Hosoe standard-model benchmark equilibrium."""
    model = CGE(model=StdCGE(), data=DATA_DIR)
    return model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=solver,
    )


def zero_shock_scenario(benchmark, name, parameter):
    """Create a scenario that sets ``parameter`` to zero for both goods."""
    scenario = benchmark.scenario(name)
    for good in GOODS:
        scenario.set(parameter, good, 0)
    return scenario


def print_comparison(title, result, benchmark):
    """Print the standard long-form comparison table for one scenario."""
    print("\n=== %s ===" % title)
    print(result.compare(benchmark).to_string(index=False))


def equivalent_variation(benchmark, result):
    """Hicksian EV for the bundled Cobb-Douglas Hosoe standard model.

    With Cobb-Douglas utility U = prod(Xp_i^alpha_i) and a unit price
    index at the benchmark equilibrium, the expenditure function is linear
    in utility. EV therefore reduces to the change in the expenditure
    required to attain the solved scenario utility at benchmark prices.
    """
    denom = prod(
        benchmark.value("alpha", good) ** benchmark.value("alpha", good)
        for good in GOODS
    )
    ep0 = benchmark.objective / denom
    ep1 = result.objective / denom
    return ep1 - ep0


def main(solver=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solver = solver or detect_solver()
    print("Using solver: %s" % solver)

    benchmark = build_benchmark(solver)

    # These Scenario objects coexist independently and share no mutable sim state.
    tariff = zero_shock_scenario(
        benchmark, "abolish import tariffs", "taum"
    )
    production_tax = zero_shock_scenario(
        benchmark, "abolish production taxes", "tauz"
    )

    tariff_result = tariff.solve(solver=solver)
    production_tax_result = production_tax.solve(solver=solver)

    print_comparison(
        "EXPERIMENT 1: ABOLISH IMPORT TARIFFS", tariff_result, benchmark
    )
    print_comparison(
        "EXPERIMENT 2: ABOLISH PRODUCTION TAXES",
        production_tax_result,
        benchmark,
    )

    print("\n=== WELFARE (Hicksian Equivalent Variation) ===")
    print(
        "Abolish tariffs:          EV = %+.4f"
        % equivalent_variation(benchmark, tariff_result)
    )
    print(
        "Abolish production taxes: EV = %+.4f"
        % equivalent_variation(benchmark, production_tax_result)
    )
    return benchmark, tariff_result, production_tax_result


if __name__ == "__main__":
    main()
