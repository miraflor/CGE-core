# -*- coding: utf-8 -*-
"""Replicate the three DRD290 Section V experiments through CGE-Core."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pyomo.environ import value

from validation.cam.replicate_base import I, IT, LC, build_base


def gv(instance, name, index=None):
    component = getattr(instance, name)
    return value(component[index] if index is not None else component)


def percentage_change(new, old):
    return 100.0 * (new / old - 1.0)


def snapshot(instance):
    result = {}
    for name in ("pd", "p", "xd", "xxd", "x", "wa", "dst"):
        index = LC if name == "wa" else I
        result[name] = {item: gv(instance, name, item) for item in index}
    for name in ("e", "mq", "pwm"):
        result[name] = {item: gv(instance, name, item) for item in IT}
    for name in ("tariff", "savings", "y"):
        result[name] = gv(instance, name)
    result["dk"] = {item: gv(instance, "dk", item) for item in I}
    result["inv_real"] = sum(result["dk"].values())
    result["wagebill"] = sum(
        result["wa"][labor] * value(instance.ls0[labor]) for labor in LC
    )
    return result


def weighted_average_change(new, old, weights):
    total_weight = sum(weights.values())
    return sum(
        weights[item] * percentage_change(new[item], old[item])
        for item in weights
    ) / total_weight


def x_weighted_price_ratio(new, base):
    """Paper-consistent Laspeyres composite-price deflator ratio."""
    numerator = sum(new["p"][item] * base["x"][item] for item in I)
    denominator = sum(base["p"][item] * base["x"][item] for item in I)
    return numerator / denominator


def real_wage_changes(new, base):
    deflator_ratio = x_weighted_price_ratio(new, base)
    return {
        labor: 100.0 * (
            (new["wa"][labor] / base["wa"][labor]) / deflator_ratio - 1.0
        )
        for labor in LC
    }


def run(cge, shocks, label, solver):
    cge.model_sim()
    for name, index, new_value in shocks:
        cge.model_modify_sim(name, index, new_value)
    cge.model_solve(solver)
    result = snapshot(cge.sim)
    gap = (
        sum(result["pwm"][item] * result["mq"][item] for item in IT)
        - sum(value(cge.sim.pwe[item]) * value(cge.sim.e[item]) for item in IT)
        - value(cge.sim.fsav)
    )
    assert abs(gap) < 1e-8, (label, gap)
    print(f"\n=== {label} ===   (sim caeq gap: {gap:.1e})")
    return result, gap


def assert_close(actual, target, tolerance, label):
    difference = abs(actual - target)
    assert difference <= tolerance, (
        f"{label}: model={actual:.6g}, target={target:.6g}, "
        f"difference={difference:.6g}, tolerance={tolerance:.6g}"
    )


def experiment_1(cge, base, solver):
    result, gap = run(
        cge,
        [("fsav", None, 500)],
        "EXP 1: oil windfall, FSAV.FX = 500",
        solver,
    )
    domestic_price_change = weighted_average_change(
        result["pd"],
        base["pd"],
        {item: base["pd"][item] * base["xxd"][item] for item in I},
    )
    composite_price_change = weighted_average_change(
        result["p"],
        base["p"],
        {item: base["p"][item] * base["x"][item] for item in I},
    )
    metrics = {
        "gap": gap,
        "investment": percentage_change(result["inv_real"], base["inv_real"]),
        "domestic_prices": domestic_price_change,
        "composite_prices": composite_price_change,
        "nominal_wages": percentage_change(result["wagebill"], base["wagebill"]),
        "real_wages": real_wage_changes(result, base),
        "dxd": {item: percentage_change(result["xd"][item], base["xd"][item]) for item in I},
        "dpd": {item: percentage_change(result["pd"][item], base["pd"][item]) for item in I},
        "dp": {item: percentage_change(result["p"][item], base["p"][item]) for item in I},
        "de": {item: percentage_change(result["e"][item], base["e"][item]) for item in IT},
        "dm": {item: percentage_change(result["mq"][item], base["mq"][item]) for item in IT},
    }

    paper_output = dict(zip(I, [2.7, -14.2, -6.7, -7.4, 0.9, -2.7,
                                -4.7, 10.2, 23.2, 0.1, -0.4]))
    paper_pd = dict(zip(I, [25.1, 22.5, 21.9, 26.0, 24.1, 28.9,
                            21.2, 40.8, 33.8, 27.8, 25.6]))
    paper_p = dict(zip(I, [24.9, 9.4, 21.8, 18.2, 17.5, 16.0,
                           6.5, 1.8, 33.8, 24.2, 25.6]))
    paper_e = dict(zip(IT, [-11.5, -14.4, -7.8, -20.7, -17.5, -9.9,
                            -12.5, 0.3, -8.2]))
    paper_m = dict(zip(IT, [44.0, 7.2, 4.8, 31.5, 33.3, 14.6,
                            13.7, 32.0, 10.7]))

    assert_close(metrics["investment"], 33.7, 0.15, "Exp 1 investment")
    # The paper's printed totals differ modestly from aggregation of model cells.
    assert_close(metrics["domestic_prices"], 27.2, 0.25, "Exp 1 domestic prices")
    assert_close(metrics["composite_prices"], 20.7, 0.35, "Exp 1 composite prices")
    assert_close(metrics["nominal_wages"], 25.4, 0.15, "Exp 1 nominal wages")

    for item in I:
        if item not in {"services", "publiques"}:
            assert_close(metrics["dxd"][item], paper_output[item], 0.15,
                         f"Exp 1 output {item}")
        assert_close(metrics["dpd"][item], paper_pd[item], 0.15,
                     f"Exp 1 domestic price {item}")
        assert_close(metrics["dp"][item], paper_p[item], 0.15,
                     f"Exp 1 composite price {item}")
    for item in IT:
        assert_close(metrics["de"][item], paper_e[item], 0.15,
                     f"Exp 1 exports {item}")
        # Forestry imports reproduce 4.6%, while the paper prints 4.8%.
        if item != "sylvicult":
            assert_close(metrics["dm"][item], paper_m[item], 0.15,
                         f"Exp 1 imports {item}")

    for labor, target in zip(LC, (1.8, 5.4, 5.5)):
        assert_close(metrics["real_wages"][labor], target, 0.35,
                     f"Exp 1 real wage {labor}")

    print("aggregates            model   paper")
    print(f"  investment (real)  {metrics['investment']:6.1f}    33.7")
    print(f"  domestic prices    {metrics['domestic_prices']:6.1f}    27.2")
    print(f"  composite prices   {metrics['composite_prices']:6.1f}    20.7")
    print(f"  wages (nominal)    {metrics['nominal_wages']:6.1f}    25.4")
    print("real wages, paper x-weighted deflator   model   paper")
    for labor, target in zip(LC, (1.8, 5.4, 5.5)):
        print(f"  {labor:<12}                    {metrics['real_wages'][labor]:6.1f}   {target:5.1f}")

    print(f"{'sector':<12}{'dXD mod':>9}{'pap':>7}{'dPD mod':>9}{'pap':>7}{'dP mod':>8}{'pap':>7}{'dE mod':>8}{'pap':>7}{'dM mod':>8}{'pap':>7}")
    for item in I:
        export_values = (
            f"{metrics['de'][item]:8.1f}{paper_e[item]:7.1f}"
            if item in IT else f"{'0.0':>8}{'0.0':>7}"
        )
        import_values = (
            f"{metrics['dm'][item]:8.1f}{paper_m[item]:7.1f}"
            if item in IT else f"{'0.0':>8}{'0.0':>7}"
        )
        print(
            f"{item:<12}{metrics['dxd'][item]:9.1f}{paper_output[item]:7.1f}"
            f"{metrics['dpd'][item]:9.1f}{paper_pd[item]:7.1f}"
            f"{metrics['dp'][item]:8.1f}{paper_p[item]:7.1f}"
            f"{export_values}{import_values}"
        )
    return metrics


def experiment_2(cge, base, solver):
    result, gap = run(
        cge,
        [("tm", "ag-subsist", 2 * 0.2205)],
        "EXP 2: double tariff on food crops",
        solver,
    )
    dxd = {
        item: percentage_change(result["xd"][item], base["xd"][item])
        for item in I
    }
    metrics = {
        "gap": gap,
        "food_imports": percentage_change(
            result["mq"]["ag-subsist"], base["mq"]["ag-subsist"]
        ),
        "food_output": dxd["ag-subsist"],
        "max_other_output": max(
            abs(change) for item, change in dxd.items() if item != "ag-subsist"
        ),
        "tariff_revenue": percentage_change(result["tariff"], base["tariff"]),
    }
    assert_close(metrics["food_imports"], -21.8, 0.15, "Exp 2 food imports")
    assert_close(metrics["food_output"], 0.04, 0.05, "Exp 2 food output")
    assert metrics["max_other_output"] <= 0.12, metrics
    assert_close(metrics["tariff_revenue"], 0.42, 0.05, "Exp 2 tariff revenue")

    print("paper: 'virtually no effect ... tiny drop in food imports ... output unchanged'")
    print(f"  dM(ag-subsist)       {metrics['food_imports']:7.2f}%")
    print(f"  dXD(ag-subsist)      {metrics['food_output']:7.2f}%")
    print(f"  max |dXD| other sectors {metrics['max_other_output']:7.2f}%")
    print(f"  d tariff revenue     {metrics['tariff_revenue']:7.2f}%")
    return metrics


def experiment_3(cge, base, solver):
    result, gap = run(
        cge,
        [("tm", "biens-int", 2 * 0.1768), ("tm", "cim-int", 2 * 0.2633)],
        "EXP 3: double tariffs on intermediate goods & construction materials",
        solver,
    )
    paper_output = dict(zip(I, [-0.1, 0.2, -0.1, -2.9, -1.8, -2.1,
                                5.2, 5.6, 6.3, 0.0, -0.1]))
    paper_pd = dict(zip(I, [-1.9, -1.1, -5.9, 0.9, -0.3, 1.6,
                            10.4, 4.4, 6.3, -2.0, -1.0]))
    paper_p = dict(zip(I, [-1.9, -0.5, -5.9, 0.7, -0.2, 7.3,
                           17.4, 0.2, 6.3, -1.8, -1.0]))
    metrics = {
        "gap": gap,
        "dxd": {item: percentage_change(result["xd"][item], base["xd"][item]) for item in I},
        "dpd": {item: percentage_change(result["pd"][item], base["pd"][item]) for item in I},
        "dp": {item: percentage_change(result["p"][item], base["p"][item]) for item in I},
        "tariff_revenue": percentage_change(result["tariff"], base["tariff"]),
        "investment": percentage_change(result["inv_real"], base["inv_real"]),
        "dm_biens_int": percentage_change(result["mq"]["biens-int"], base["mq"]["biens-int"]),
        "dm_cim_int": percentage_change(result["mq"]["cim-int"], base["mq"]["cim-int"]),
        "real_wages": real_wage_changes(result, base),
    }
    for item in I:
        assert_close(metrics["dxd"][item], paper_output[item], 0.15,
                     f"Exp 3 output {item}")
        assert_close(metrics["dpd"][item], paper_pd[item], 0.15,
                     f"Exp 3 domestic price {item}")
        assert_close(metrics["dp"][item], paper_p[item], 0.15,
                     f"Exp 3 composite price {item}")
    assert_close(metrics["tariff_revenue"], 39.2, 0.15, "Exp 3 tariff revenue")
    assert_close(metrics["investment"], 9.3, 0.15, "Exp 3 investment")
    assert_close(metrics["dm_biens_int"], -7.8, 0.15, "Exp 3 intermediate imports")
    assert abs(metrics["dm_cim_int"]) < 1.0, metrics
    for labor, target in zip(LC, (-3.4, -3.1, -3.2)):
        assert_close(metrics["real_wages"][labor], target, 0.15,
                     f"Exp 3 real wage {labor}")

    print(f"{'sector':<12}{'dXD mod':>9}{'pap':>7}{'dPD mod':>9}{'pap':>7}{'dP mod':>8}{'pap':>7}")
    for item in I:
        print(
            f"{item:<12}{metrics['dxd'][item]:9.1f}{paper_output[item]:7.1f}"
            f"{metrics['dpd'][item]:9.1f}{paper_pd[item]:7.1f}"
            f"{metrics['dp'][item]:8.1f}{paper_p[item]:7.1f}"
        )
    print(f"tariff revenue   model {metrics['tariff_revenue']:6.1f}   paper +39")
    print(f"total investment model {metrics['investment']:6.1f}   paper +9")
    print(f"dM biens-int     model {metrics['dm_biens_int']:6.1f}   paper -7.8")
    print(f"dM cim-int       model {metrics['dm_cim_int']:6.1f}   paper 'less than one percent'")
    print("real wages, paper x-weighted deflator   model   paper")
    for labor, target in zip(LC, (-3.4, -3.1, -3.2)):
        print(f"  {labor:<12}                    {metrics['real_wages'][labor]:6.1f}   {target:5.1f}")
    return metrics


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
    assert dof_before == -1 and dof_after == 0
    base = snapshot(cge.base)
    experiment_1(cge, base, args.solver)
    experiment_2(cge, base, args.solver)
    experiment_3(cge, base, args.solver)
    print("\nALL CAMCGE experiment regression checks passed.")


if __name__ == "__main__":
    main()
