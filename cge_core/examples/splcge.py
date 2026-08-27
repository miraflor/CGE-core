# -*- coding: utf-8 -*-
"""
Simple CGE Example (Hosoe Ch. 3-4) -- closed economy benchmark solve.

Demonstrates the canonical CGE-Core v0.6 workflow:
    configure -> solve benchmark -> inspect values

Requires a local NLP solver ('ipopt' executable or 'cyipopt'); the
example detects whichever is available.

Run with:
    python -m cge_core.examples.splcge
"""
import logging

from cge_core import CGE, example_data
from cge_core.examples._solver import detect_solver
from cge_core.models import SplCGE

DATA_DIR = example_data("splcge")
GOODS = ("BRD", "MLK")


def main(solver=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solver = solver or detect_solver()
    print("Using solver: %s" % solver)

    model = CGE(model=SplCGE(), data=DATA_DIR)
    benchmark = model.solve_benchmark(
        numeraire=("pf", "LAB"),
        redundant=("eqpf", "LAB"),
        solver=solver,
    )

    print("\n=== BENCHMARK EQUILIBRIUM ===")
    for good in GOODS:
        print("  Z[%s]  = %7.4f" % (good, benchmark.value("Z", good)))
    for good in GOODS:
        print("  X[%s]  = %7.4f" % (good, benchmark.value("X", good)))
    print("  Utility = %7.4f" % benchmark.objective)
    return benchmark


if __name__ == "__main__":
    main()
