# -*- coding: utf-8 -*-
"""
Standard CGE Example (Hosoe Ch. 6) -- tariff and tax abolition experiments.

Runs the full CGE-Core workflow end to end:
    load -> instance -> drop redundant eqn -> calibrate -> sim -> shock
    -> solve -> compare

Requires a local NLP solver ('ipopt' executable or 'cyipopt'); the example
detects whichever is available.

The redundant market-clearing equation (Walras' law) MUST be dropped before
solving with IPOPT; see PyCGE.model_drop_redundant for the full explanation.

Run with:
    python -m cge_core.examples.stdcge
"""
import logging

from pyomo.environ import prod, value

from cge_core import PyCGE, example_data
from cge_core.examples._solver import detect_solver
from cge_core.examples.stdcge_model_def import StdModelDef

DATA_DIR = example_data('stdcge')


def build_calibrated(solver):
    """Return a freshly calibrated base CGE object."""
    cge = PyCGE(StdModelDef())
    cge.model_data(DATA_DIR)

    # Fix the numeraire (matches Hosoe stdcge.gms: pf.fx("LAB") = 1)
    cge.model_instance('pf', 'LAB')

    # Drop one redundant market-clearing equation (Walras' law) so the
    # square system has DOF = 0 and IPOPT can solve it. The labor market
    # is a natural choice since labor is the numeraire factor.
    cge.model_drop_redundant('eqpf', 'LAB')

    cge.model_calibrate(solver)
    return cge


def run_experiment(solver, title, param, shocks):
    """Calibrate, apply a shock to `param` for each good, solve, compare."""
    print("\n=== %s ===" % title)
    cge = build_calibrated(solver)
    cge.model_sim()                      # clone calibrated base -> sim
    for good in shocks:
        cge.model_modify_sim(param, good, 0)
    cge.model_solve(solver)
    cge.model_postprocess('compare', 'print')
    return cge


def equivalent_variation(cge):
    """Hicksian EV: expenditure to reach the new utility at base prices.

    With Cobb-Douglas utility U = prod(Xp_i^alpha_i) and a unit price
    index at the base equilibrium, the expenditure function is linear in
    utility, so EV reduces to the difference in the utility aggregate
    evaluated through the base-price expenditure function.
    """
    denom = prod((value(cge.base.alpha[i])) ** value(cge.base.alpha[i])
                 for i in cge.base.i)
    ep0 = value(cge.base.obj) / denom
    ep1 = value(cge.sim.obj) / denom
    return ep1 - ep0


def main(solver=None):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    solver = solver or detect_solver()
    print("Using solver: %s" % solver)

    cge1 = run_experiment(solver, "EXPERIMENT 1: ABOLISH IMPORT TARIFFS",
                          'taum', ['BRD', 'MLK'])
    cge2 = run_experiment(solver, "EXPERIMENT 2: ABOLISH PRODUCTION TAXES",
                          'tauz', ['BRD', 'MLK'])

    print("\n=== WELFARE (Hicksian Equivalent Variation) ===")
    print("Abolish tariffs:          EV = %+.4f" % equivalent_variation(cge1))
    print("Abolish production taxes: EV = %+.4f" % equivalent_variation(cge2))
    return cge1, cge2


if __name__ == '__main__':
    main()
