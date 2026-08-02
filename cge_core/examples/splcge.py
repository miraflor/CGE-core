# -*- coding: utf-8 -*-
"""
Simple CGE Example (Hosoe Ch. 3-4) -- closed economy base calibration.

Demonstrates the minimal CGE-Core workflow:
    load -> instance -> drop redundant eqn -> calibrate -> inspect

Requires a local NLP solver ('ipopt' executable or 'cyipopt'); the
example detects whichever is available.

Run with:
    python -m cge_core.examples.splcge
"""
import logging

from pyomo.environ import value

from cge_core import PyCGE, example_data
from cge_core.examples._solver import detect_solver
from cge_core.examples.splcge_model_def import SplModelDef

DATA_DIR = example_data('splcge')


def main(solver=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solver = solver or detect_solver()
    print("Using solver: %s" % solver)

    cge = PyCGE(SplModelDef())
    cge.model_data(DATA_DIR)

    # Fix the numeraire.
    cge.model_instance('pf', 'LAB')

    # Drop one redundant market-clearing equation (Walras' law) -> DOF = 0.
    # See PyCGE.model_drop_redundant for the full explanation.
    cge.model_drop_redundant('eqpf', 'LAB')

    cge.model_calibrate(solver)

    print("\n=== BASE EQUILIBRIUM ===")
    for i in cge.base.i:
        print("  Z[%s]  = %7.4f" % (i, value(cge.base.Z[i])))
    for i in cge.base.i:
        print("  X[%s]  = %7.4f" % (i, value(cge.base.X[i])))
    print("  Utility = %7.4f" % value(cge.base.obj))
    return cge


if __name__ == '__main__':
    main()
