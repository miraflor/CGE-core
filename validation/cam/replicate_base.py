# -*- coding: utf-8 -*-
"""Replicate the published 1987 CAMCGE base solution through CGE-Core."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pyomo.environ import value

# This script is meant to be run directly from a source checkout, as
# `python validation/cam/replicate_base.py`, so the replication evidence can be
# regenerated without installing anything first.  Run that way, Python does not
# know where the repository root is, so it is added below.
#
# The project forbids this same adjustment inside the notebooks, and rightly so:
# a notebook opened from a link has no checkout to point at, and doing it there
# produced exactly the confusing failures the rule was written to prevent.  A
# checked-out script is the case where it is the correct thing to do.
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "cge_core" / "models" / "camcge" / "data"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cge_core._pycge import PyCGE  # noqa: E402
from cge_core.models.camcge.model import CamModelDef  # noqa: E402

I = [
    "ag-subsist", "ag-exp+ind", "sylvicult", "ind-alim", "biens-cons",
    "biens-int", "cim-int", "biens-cap", "construct", "services",
    "publiques",
]
IT = [sector for sector in I if sector not in ("construct", "publiques")]
LC = ["rural", "urban-unsk", "urban-skil"]

# Published 1987 solution-report levels (paper appendix, pp. 16-31).
PUB = {
    "omega": 191.7346,
    "x": [328.3537, 14.4263, 7.1890, 66.5307, 149.6435, 321.6279,
          73.2830, 141.1530, 174.0851, 608.6083, 163.9860],
    "xd": [330.4860, 131.4452, 29.5023, 72.0183, 118.4380, 284.3784,
           34.1676, 10.2961, 174.0851, 615.7901, 163.9860],
    "xxd": [325.8923, 6.3818, 7.1660, 48.5697, 112.5742, 183.0514,
            23.6672, 6.4588, 174.0851, 534.1664, 163.9860],
    "e": [4.5937, 125.0634, 22.3363, 23.4486, 5.8638, 101.3271,
          10.5004, 3.8374, 81.6238],
    "mq": [2.4615, 8.0444, 0.0230, 17.9610, 37.0693, 138.5765,
           49.6159, 134.6942, 74.4419],
    "pva": [0.9484, 0.3432, 0.6245, 0.2325, 0.3938, 0.3011,
            0.3820, 0.6876, 0.4507, 0.7242, 0.6513],
    "wa": [0.1100, 0.1568, 1.8658],
    "cd": [260.1309, 4.2183, 0, 53.0823, 133.6631, 168.1671,
           0, 0, 3.7926, 302.6213, 22.3546],
    "intm": [57.4782, 6.6992, 6.1640, 10.2586, 8.8791, 149.9666,
             73.2830, 27.3870, 32.1941, 305.9869, 6.6013],
    "idv": [6.7117, 0, 0, 0, 0, 0, 0, 113.3331, 138.0984, 0, 0],
}
LEVEL_GROUPS = (
    ("x", I), ("xd", I), ("xxd", I), ("e", IT), ("mq", IT),
    ("pva", I), ("wa", LC), ("cd", I), ("intm", I), ("idv", I),
)
PUBLISHED_LEVEL_COUNT = sum(len(index) for _, index in LEVEL_GROUPS)


def _levels(instance, variable_name, index):
    variable = getattr(instance, variable_name)
    return [value(variable[item]) for item in index]


def build_base(solver="cyipopt"):
    """Build, close, and solve the CAMCGE base model with CGE-Core."""
    cge = PyCGE(CamModelDef())
    cge.model_data(DATA_DIR)
    cge.model_instance("mps", None)  # savings-driven closure: fix mps
    dof_before = cge.degrees_of_freedom(cge.base)
    cge.model_drop_redundant("caeq")
    dof_after = cge.degrees_of_freedom(cge.base)
    cge.model_calibrate(solver)
    return cge, dof_before, dof_after


def base_metrics(cge, dof_before, dof_after):
    """Return structured comparison metrics for a calibrated base model."""
    base = cge.base
    mismatches = []
    worst = 0.0
    for name, index in LEVEL_GROUPS:
        for got, published, label in zip(_levels(base, name, index), PUB[name], index):
            difference = abs(got - published)
            worst = max(worst, difference)
            if difference > 5e-3:
                mismatches.append((name, label, got, published, difference))

    omega = value(base.obj)
    current_account_gap = (
        sum(value(base.pwm[i]) * value(base.mq[i]) for i in base.it)
        - sum(value(base.pwe[i]) * value(base.e[i]) for i in base.it)
        - value(base.fsav)
    )
    return {
        "dof_before": dof_before,
        "dof_after": dof_after,
        "omega": omega,
        "omega_difference": abs(omega - PUB["omega"]),
        "published_level_count": PUBLISHED_LEVEL_COUNT,
        "worst_level_difference": worst,
        "mismatches": mismatches,
        "pd_min": min(_levels(base, "pd", I)),
        "pd_max": max(_levels(base, "pd", I)),
        "pwe_min": min(_levels(base, "pwe", IT)),
        "pwe_max": max(_levels(base, "pwe", IT)),
        "current_account_gap": current_account_gap,
    }


def validate_base(metrics):
    """Raise AssertionError if the published benchmark is not reproduced."""
    assert metrics["dof_before"] == -1, metrics
    assert metrics["dof_after"] == 0, metrics
    assert metrics["omega_difference"] < 1e-3, metrics
    assert metrics["worst_level_difference"] < 5e-3, metrics
    assert not metrics["mismatches"], metrics["mismatches"]
    assert abs(metrics["current_account_gap"]) < 1e-8, metrics


def print_metrics(metrics):
    print(
        f"DOF before drop: {metrics['dof_before']}   "
        f"after: {metrics['dof_after']}"
    )
    print(
        f"omega: got {metrics['omega']:.4f}  published {PUB['omega']:.4f}  "
        f"diff {metrics['omega_difference']:.2e}"
    )
    print(
        f"pd range: [{metrics['pd_min']:.4f}, {metrics['pd_max']:.4f}]  "
        "(published ~1.0000-1.0004)"
    )
    print(
        f"pwe range: [{metrics['pwe_min']:.4f}, {metrics['pwe_max']:.4f}]  "
        "(published ~4.7619-4.7622)"
    )
    print(
        "max |level - published| across "
        f"{metrics['published_level_count']} reported variable levels: "
        f"{metrics['worst_level_difference']:.2e}"
    )
    if metrics["mismatches"]:
        print("levels off by > 5e-3:")
        for row in metrics["mismatches"]:
            print(
                "   %-6s %-11s got %10.4f pub %10.4f diff %.1e" % row
            )
    else:
        print("ALL reported levels match the 1987 published solution to < 5e-3")
    print(
        "current-account gap (dropped caeq): "
        f"{metrics['current_account_gap']:.2e}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--solver",
        default="cyipopt",
        help="Pyomo solver name (default: cyipopt; ipopt is also supported)",
    )
    args = parser.parse_args(argv)

    logging.disable(logging.CRITICAL)
    cge, dof_before, dof_after = build_base(args.solver)
    metrics = base_metrics(cge, dof_before, dof_after)
    print_metrics(metrics)
    validate_base(metrics)

    # The added cd guard must remain non-binding.
    assert all(
        value(cge.base.cd[i]) > 0.02
        for i in I
        if value(cge.base.cles[i]) > 0
    )


if __name__ == "__main__":
    main()
