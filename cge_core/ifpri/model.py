# -*- coding: utf-8 -*-
"""Build the IFPRI test economy as an initialized Pyomo equation system.

The first model milestone deliberately stops before numerical solution.  It
turns the independently calibrated benchmark into Pyomo variables,
parameters, and constraints, then permits every active equation to be checked
at the benchmark point.  The supplied IFPRI test economy uses a Leontief top
production nest; CES value added, output aggregation, Armington import
aggregation, CET export transformation, institutions, LES demand, and macro
balances are represented below.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

from pyomo.environ import (
    ConcreteModel,
    Constraint,
    Param,
    Set,
    Var,
    value,
)

from .calibration import calibrate_ifpri_benchmark
from .schema import IfpriBenchmarkCalibration, IfpriDataset
from .validation import IfpriDataError

_TINY = 1e-14


@dataclass(frozen=True)
class IfpriResidualReport:
    """Summary of equation residuals at the current Pyomo variable values."""

    equation_count: int
    max_abs_residual: float
    worst_equation: str
    group_max_abs_residual: Mapping[str, float]


def _active(value_: float) -> bool:
    return abs(float(value_)) > _TINY


def build_ifpri_benchmark_model(
    dataset: IfpriDataset,
    calibration: Optional[IfpriBenchmarkCalibration] = None,
) -> ConcreteModel:
    """Create the initialized Pyomo benchmark model without calling a solver.

    Args:
        dataset: Parsed IFPRI test dataset.
        calibration: Optional precomputed algebraic calibration.

    Returns:
        A :class:`pyomo.environ.ConcreteModel` whose active equations reproduce
        the benchmark at their initialized values.

    Raises:
        IfpriDataError: if the benchmark is incompatible with this milestone.
    """
    cal = calibration or calibrate_ifpri_benchmark(dataset)
    s = dataset.sets
    sam = dataset.sam
    p = cal.prices
    q = cal.quantities
    prod = cal.production
    tax = cal.taxes
    inst = cal.institutions
    les = cal.les
    sys = cal.system

    # TEST.DAT assigns every activity to the fixed-coefficient top nest.  Keep
    # that restriction explicit until the alternative CES top nest is added.
    if any(abs(dataset.inputs.elasticities.top_level_substitution[a]) <= _TINY
           for a in s.activities):
        raise IfpriDataError("Top-level substitution elasticities must be nonzero.")

    A = tuple(s.activities)
    C = tuple(s.commodities)
    F = tuple(s.factors)
    H = tuple(s.households)
    INSD = tuple(s.domestic_institutions)
    INSDNG = tuple(s.domestic_nongovernment_institutions)

    cm = tuple(c for c in C if _active(q.imports[c]))
    ce = tuple(c for c in C if _active(q.exports[c]))
    cd = tuple(c for c in C if _active(q.domestic_sales[c]))
    cx = tuple(c for c in C if _active(q.marketed_output[c]))
    ct = tuple(c for c in C if _active(q.transaction_demand[c]))
    both_trade = tuple(c for c in C if c in cm and c in cd)
    one_trade = tuple(c for c in C if (c in cm) ^ (c in cd))
    both_transform = tuple(c for c in C if c in ce and c in cd)
    one_transform = tuple(c for c in C if (c in ce) ^ (c in cd))

    qf_active = tuple((f, a) for f in F for a in A
                      if _active(q.factor_demand[(f, a)]))
    qint_active = tuple((c, a) for c in C for a in A
                        if _active(prod.intermediate_shares[(c, a)]))
    production_active = tuple((a, c) for a in A for c in C
                              if _active(prod.yield_coefficient[(a, c)]))
    qxac_active = tuple((a, c) for a in A for c in C
                        if _active(q.activity_commodity[(a, c)]))
    qh_active = tuple((c, h) for c in C for h in H
                      if _active(les.market_marginal_share[(c, h)]))
    qha_active = tuple((a, c, h) for a in A for c in C for h in H
                       if _active(les.home_marginal_share[(a, c, h)]))
    qinv_active = tuple(c for c in C if _active(q.investment[c]))
    qg_active = tuple(c for c in C if _active(q.government[c]))
    yif_active = tuple((i, f) for i in INSD for f in F
                       if _active(inst.factor_income_share[(i, f)]))
    trii_active = tuple((i, ip) for i in INSDNG for ip in INSDNG
                        if _active(inst.interinstitution_share[(i, ip)]))

    model = ConcreteModel(name="IFPRI Standard CGE benchmark")
    model.A = Set(initialize=A, ordered=True)
    model.C = Set(initialize=C, ordered=True)
    model.F = Set(initialize=F, ordered=True)
    model.H = Set(initialize=H, ordered=True)
    model.INSD = Set(initialize=INSD, ordered=True)
    model.INSDNG = Set(initialize=INSDNG, ordered=True)
    model.CM = Set(initialize=cm, ordered=True)
    model.CE = Set(initialize=ce, ordered=True)
    model.CD = Set(initialize=cd, ordered=True)
    model.CX = Set(initialize=cx, ordered=True)
    model.CT = Set(initialize=ct, ordered=True)
    model.CMD = Set(initialize=both_trade, ordered=True)
    model.CM_OR_CD = Set(initialize=one_trade, ordered=True)
    model.CQ = Set(initialize=tuple(c for c in C if c in cd or c in cm), ordered=True)
    model.CED = Set(initialize=both_transform, ordered=True)
    model.CE_OR_CD = Set(initialize=one_transform, ordered=True)
    model.QF_ACTIVE = Set(dimen=2, initialize=qf_active, ordered=True)
    model.QINT_ACTIVE = Set(dimen=2, initialize=qint_active, ordered=True)
    model.PRODUCTION_ACTIVE = Set(dimen=2, initialize=production_active, ordered=True)
    model.QXAC_ACTIVE = Set(dimen=2, initialize=qxac_active, ordered=True)
    model.QH_ACTIVE = Set(dimen=2, initialize=qh_active, ordered=True)
    model.QHA_ACTIVE = Set(dimen=3, initialize=qha_active, ordered=True)
    model.QINV_ACTIVE = Set(initialize=qinv_active, ordered=True)
    model.QG_ACTIVE = Set(initialize=qg_active, ordered=True)
    model.YIF_ACTIVE = Set(dimen=2, initialize=yif_active, ordered=True)
    model.TRII_ACTIVE = Set(dimen=2, initialize=trii_active, ordered=True)

    # Calibrated parameters.
    model.pwm = Param(model.C, initialize=p.world_import, default=0.0)
    model.pwe = Param(model.C, initialize=p.world_export, default=0.0)
    model.tm = Param(model.C, initialize=tax.import_, default=0.0)
    model.te = Param(model.C, initialize=tax.export, default=0.0)
    model.tq = Param(model.C, initialize=tax.commodity, default=0.0)
    model.ta = Param(model.A, initialize=tax.activity, default=0.0)
    model.tva = Param(model.A, initialize=tax.value_added, default=0.0)
    model.tf = Param(model.F, initialize=tax.factor, default=0.0)
    model.theta = Param(model.A, model.C, initialize=prod.yield_coefficient,
                        default=0.0)
    model.ica = Param(model.C, model.A, initialize=prod.intermediate_shares,
                      default=0.0)
    model.iva = Param(model.A, initialize=prod.value_added_coefficient)
    model.inta = Param(model.A, initialize=prod.intermediate_coefficient)
    model.rhova = Param(model.A, initialize=prod.factor_exponent)
    model.deltava = Param(model.F, model.A, initialize=prod.factor_shares,
                          default=0.0)
    model.alphava = Param(model.A, initialize=prod.factor_scale)
    model.rhoac = Param(model.C, initialize=prod.output_exponent, default=0.0)
    model.deltaac = Param(model.A, model.C, initialize=prod.output_shares,
                          default=0.0)
    model.alphaac = Param(model.C, initialize=prod.output_scale, default=0.0)
    model.rhoq = Param(model.C, initialize=prod.armington_exponent, default=0.0)
    model.deltaq = Param(model.C, initialize=prod.armington_share, default=0.0)
    model.alphaq = Param(model.C, initialize=prod.armington_scale, default=0.0)
    model.rhot = Param(model.C, initialize=prod.cet_exponent, default=0.0)
    model.deltat = Param(model.C, initialize=prod.cet_share, default=0.0)
    model.alphat = Param(model.C, initialize=prod.cet_scale, default=0.0)
    model.icd = Param(model.C, model.C, initialize=prod.transaction_domestic,
                      default=0.0)
    model.icm = Param(model.C, model.C, initialize=prod.transaction_import,
                      default=0.0)
    model.ice = Param(model.C, model.C, initialize=prod.transaction_export,
                      default=0.0)
    model.cwts = Param(model.C, initialize=sys.consumer_price_weights)
    model.dwts = Param(model.C, initialize=sys.domestic_price_weights)
    model.shif = Param(model.INSD, model.F, initialize=inst.factor_income_share,
                       default=0.0)
    model.shii = Param(model.INSDNG, model.INSDNG,
                       initialize=inst.interinstitution_share, default=0.0)
    model.betam = Param(model.C, model.H, initialize=les.market_marginal_share,
                        default=0.0)
    model.betah = Param(model.A, model.C, model.H,
                        initialize=les.home_marginal_share, default=0.0)
    model.gammam = Param(model.C, model.H, initialize=les.market_subsistence,
                         default=0.0)
    model.gammah = Param(model.A, model.C, model.H,
                         initialize=les.home_subsistence, default=0.0)
    model.qbarinv = Param(model.C, initialize=q.investment, default=0.0)
    model.qbarg = Param(model.C, initialize=q.government, default=0.0)
    model.qdst = Param(model.C, initialize=q.stock_change, default=0.0)
    model.tinsbar = Param(model.INSDNG, initialize=tax.institution, default=0.0)
    model.mpsbar = Param(model.INSDNG, initialize=inst.savings_rate, default=0.0)
    # The official BASE closure allows a uniform rate-point change in the
    # marginal propensity to save for all domestic nongovernment institutions.
    model.mps01 = Param(model.INSDNG, initialize={i: 1.0 for i in INSDNG})

    tr_row_f = {f: sam.value("ROW", f) / p.exchange_rate for f in F}
    tr_i_row = {i: sam.value(i, "ROW") / p.exchange_rate for i in INSD}
    tr_i_gov = {
        i: sam.value(i, "GOV") / sys.consumer_price_index for i in INSD
    }
    tr_gov_row = sam.value("GOV", "ROW") / p.exchange_rate
    model.tr_row_f = Param(model.F, initialize=tr_row_f, default=0.0)
    model.tr_i_row = Param(model.INSD, initialize=tr_i_row, default=0.0)
    model.tr_i_gov = Param(model.INSD, initialize=tr_i_gov, default=0.0)
    model.tr_gov_row = Param(initialize=tr_gov_row)

    # Variables initialized exactly at the algebraically calibrated benchmark.
    model.EXR = Var(initialize=p.exchange_rate)
    model.PA = Var(model.A, initialize=p.activity)
    model.PXAC = Var(model.A, model.C, initialize=p.activity_commodity)
    model.PVA = Var(model.A, initialize=p.value_added)
    model.PINTA = Var(model.A, initialize=p.intermediate_aggregate)
    model.PX = Var(model.C, initialize=p.marketed_output)
    model.PDS = Var(model.C, initialize=p.domestic_supply)
    model.PDD = Var(model.C, initialize=p.domestic_demand)
    model.PE = Var(model.C, initialize=p.export)
    model.PM = Var(model.C, initialize=p.import_)
    model.PQ = Var(model.C, initialize=p.composite)
    model.WF = Var(model.F, initialize=p.factor)
    model.WFDIST = Var(model.F, model.A, initialize=p.factor_activity)
    model.CPI = Var(initialize=sys.consumer_price_index)
    model.DPI = Var(initialize=sys.domestic_price_index)

    model.QA = Var(model.A, initialize=q.activity)
    model.QVA = Var(model.A, initialize=q.value_added)
    model.QINTA = Var(model.A, initialize=q.intermediate_aggregate)
    model.QXAC = Var(model.A, model.C, initialize=q.activity_commodity)
    model.QHA = Var(model.A, model.C, model.H, initialize=q.home_consumption)
    model.QX = Var(model.C, initialize=q.marketed_output)
    model.QD = Var(model.C, initialize=q.domestic_sales)
    model.QE = Var(model.C, initialize=q.exports)
    model.QM = Var(model.C, initialize=q.imports)
    model.QQ = Var(model.C, initialize=q.composite_supply)
    model.QF = Var(model.F, model.A, initialize=q.factor_demand)
    model.QFS = Var(model.F, initialize=q.factor_supply)
    model.QINT = Var(model.C, model.A, initialize=q.intermediate)
    model.QT = Var(model.C, initialize=q.transaction_demand)
    model.QH = Var(model.C, model.H, initialize=q.household_market)
    model.QG = Var(model.C, initialize=q.government)
    model.QINV = Var(model.C, initialize=q.investment)

    model.YF = Var(model.F, initialize=inst.factor_income)
    model.YIF = Var(model.INSD, model.F, initialize=inst.institution_factor_income)
    model.YI = Var(model.INSDNG, initialize=inst.institution_income)
    model.TRII = Var(
        model.INSDNG, model.INSDNG,
        initialize={(i, ip): sam.value(i, ip) for i in INSDNG for ip in INSDNG},
    )
    model.EH = Var(model.H, initialize=inst.household_expenditure)
    model.YG = Var(initialize=inst.government_income)
    model.EG = Var(initialize=inst.government_expenditure)
    model.TINS = Var(model.INSDNG, initialize=tax.institution)
    model.MPS = Var(model.INSDNG, initialize=inst.savings_rate)
    model.DMPS = Var(initialize=0.0)

    model.IADJ = Var(initialize=1.0)
    model.GADJ = Var(initialize=1.0)
    model.FSAV = Var(initialize=sys.foreign_saving)
    model.GSAV = Var(initialize=inst.government_saving)
    model.WALRAS = Var(initialize=sys.walras_residual)
    model.TABS = Var(initialize=sys.total_absorption)
    model.INVSHR = Var(initialize=sys.investment_share)
    model.GOVSHR = Var(initialize=sys.government_share)

    # Price equations.
    def pm_rule(m, c):
        return m.PM[c] == m.pwm[c] * (1.0 + m.tm[c]) * m.EXR + sum(
            m.PQ[ct_] * m.icm[ct_, c] for ct_ in m.C
        )
    model.pm_definition = Constraint(model.CM, rule=pm_rule)

    def pe_rule(m, c):
        return m.PE[c] == m.pwe[c] * (1.0 - m.te[c]) * m.EXR - sum(
            m.PQ[ct_] * m.ice[ct_, c] for ct_ in m.C
        )
    model.pe_definition = Constraint(model.CE, rule=pe_rule)

    def pdd_rule(m, c):
        return m.PDD[c] == m.PDS[c] + sum(
            m.PQ[ct_] * m.icd[ct_, c] for ct_ in m.C
        )
    model.pdd_definition = Constraint(model.CD, rule=pdd_rule)

    def pq_rule(m, c):
        return m.PQ[c] * (1.0 - m.tq[c]) * m.QQ[c] == (
            m.PDD[c] * m.QD[c] + m.PM[c] * m.QM[c]
        )
    model.pq_definition = Constraint(model.CQ, rule=pq_rule)

    def px_rule(m, c):
        return m.PX[c] * m.QX[c] == m.PDS[c] * m.QD[c] + m.PE[c] * m.QE[c]
    model.px_definition = Constraint(model.CX, rule=px_rule)

    def pa_rule(m, a):
        return m.PA[a] == sum(m.PXAC[a, c] * m.theta[a, c] for c in m.C)
    model.pa_definition = Constraint(model.A, rule=pa_rule)

    def pinta_rule(m, a):
        return m.PINTA[a] == sum(m.PQ[c] * m.ica[c, a] for c in m.C)
    model.pinta_definition = Constraint(model.A, rule=pinta_rule)

    def pva_rule(m, a):
        return m.PA[a] * (1.0 - m.ta[a]) * m.QA[a] == (
            m.PVA[a] * m.QVA[a] + m.PINTA[a] * m.QINTA[a]
        )
    model.pva_definition = Constraint(model.A, rule=pva_rule)

    model.cpi_definition = Constraint(
        expr=model.CPI == sum(model.cwts[c] * model.PQ[c] for c in model.C)
    )
    model.dpi_definition = Constraint(
        expr=model.DPI == sum(model.dwts[c] * model.PDS[c] for c in model.CD)
    )

    # Production and trade equations.  The benchmark test data use the
    # fixed-coefficient top nest.
    model.leontief_intermediate = Constraint(
        model.A, rule=lambda m, a: m.QINTA[a] == m.inta[a] * m.QA[a]
    )
    model.leontief_value_added = Constraint(
        model.A, rule=lambda m, a: m.QVA[a] == m.iva[a] * m.QA[a]
    )

    def ces_va_rule(m, a):
        aggregate = sum(
            m.deltava[f, a] * m.QF[f, a] ** (-m.rhova[a])
            for f in m.F if _active(value(m.deltava[f, a]))
        )
        return m.QVA[a] == m.alphava[a] * aggregate ** (-1.0 / m.rhova[a])
    model.ces_value_added = Constraint(model.A, rule=ces_va_rule)

    def ces_va_foc_rule(m, f, a):
        aggregate = sum(
            m.deltava[fp, a] * m.QF[fp, a] ** (-m.rhova[a])
            for fp in m.F if _active(value(m.deltava[fp, a]))
        )
        return m.WF[f] * m.WFDIST[f, a] == (
            m.PVA[a] * (1.0 - m.tva[a]) * m.QVA[a]
            * aggregate ** (-1.0)
            * m.deltava[f, a]
            * m.QF[f, a] ** (-m.rhova[a] - 1.0)
        )
    model.ces_value_added_foc = Constraint(model.QF_ACTIVE, rule=ces_va_foc_rule)

    model.intermediate_demand = Constraint(
        model.QINT_ACTIVE,
        rule=lambda m, c, a: m.QINT[c, a] == m.ica[c, a] * m.QINTA[a],
    )

    def commodity_production_rule(m, a, c):
        return m.QXAC[a, c] + sum(m.QHA[a, c, h] for h in m.H) == (
            m.theta[a, c] * m.QA[a]
        )
    model.commodity_production = Constraint(
        model.PRODUCTION_ACTIVE, rule=commodity_production_rule
    )

    def output_aggregation_rule(m, c):
        aggregate = sum(
            m.deltaac[a, c] * m.QXAC[a, c] ** (-m.rhoac[c])
            for a in m.A if _active(value(m.deltaac[a, c]))
        )
        return m.QX[c] == m.alphaac[c] * aggregate ** (-1.0 / m.rhoac[c])
    model.output_aggregation = Constraint(model.CX, rule=output_aggregation_rule)

    def output_foc_rule(m, a, c):
        aggregate = sum(
            m.deltaac[ap, c] * m.QXAC[ap, c] ** (-m.rhoac[c])
            for ap in m.A if _active(value(m.deltaac[ap, c]))
        )
        return m.PXAC[a, c] == (
            m.PX[c] * m.QX[c] * aggregate ** (-1.0)
            * m.deltaac[a, c]
            * m.QXAC[a, c] ** (-m.rhoac[c] - 1.0)
        )
    model.output_aggregation_foc = Constraint(
        model.QXAC_ACTIVE, rule=output_foc_rule
    )

    def cet_rule(m, c):
        return m.QX[c] == m.alphat[c] * (
            m.deltat[c] * m.QE[c] ** m.rhot[c]
            + (1.0 - m.deltat[c]) * m.QD[c] ** m.rhot[c]
        ) ** (1.0 / m.rhot[c])
    model.cet_transformation = Constraint(model.CED, rule=cet_rule)

    def export_supply_rule(m, c):
        return m.QE[c] == m.QD[c] * (
            (m.PE[c] / m.PDS[c]) * ((1.0 - m.deltat[c]) / m.deltat[c])
        ) ** (1.0 / (m.rhot[c] - 1.0))
    model.export_supply = Constraint(model.CED, rule=export_supply_rule)
    model.cet_single_destination = Constraint(
        model.CE_OR_CD, rule=lambda m, c: m.QX[c] == m.QD[c] + m.QE[c]
    )

    def armington_rule(m, c):
        return m.QQ[c] == m.alphaq[c] * (
            m.deltaq[c] * m.QM[c] ** (-m.rhoq[c])
            + (1.0 - m.deltaq[c]) * m.QD[c] ** (-m.rhoq[c])
        ) ** (-1.0 / m.rhoq[c])
    model.armington_aggregation = Constraint(model.CMD, rule=armington_rule)

    def import_cost_min_rule(m, c):
        return m.QM[c] == m.QD[c] * (
            (m.PDD[c] / m.PM[c]) * (m.deltaq[c] / (1.0 - m.deltaq[c]))
        ) ** (1.0 / (1.0 + m.rhoq[c]))
    model.armington_cost_minimization = Constraint(model.CMD, rule=import_cost_min_rule)
    model.armington_single_source = Constraint(
        model.CM_OR_CD, rule=lambda m, c: m.QQ[c] == m.QD[c] + m.QM[c]
    )

    def transaction_demand_rule(m, ct_):
        return m.QT[ct_] == sum(
            m.icm[ct_, c] * m.QM[c]
            + m.ice[ct_, c] * m.QE[c]
            + m.icd[ct_, c] * m.QD[c]
            for c in m.C
        )
    model.transaction_demand = Constraint(model.CT, rule=transaction_demand_rule)

    # Institutions and final demand.
    model.factor_income_definition = Constraint(
        model.F,
        rule=lambda m, f: m.YF[f] == sum(
            m.WF[f] * m.WFDIST[f, a] * m.QF[f, a] for a in m.A
        ),
    )

    def institution_factor_income_rule(m, i, f):
        return m.YIF[i, f] == m.shif[i, f] * (
            (1.0 - m.tf[f]) * m.YF[f] - m.tr_row_f[f] * m.EXR
        )
    model.institution_factor_income_definition = Constraint(
        model.YIF_ACTIVE, rule=institution_factor_income_rule
    )

    def institution_income_rule(m, i):
        return m.YI[i] == (
            sum(m.YIF[i, f] for f in m.F)
            + sum(m.TRII[i, ip] for ip in m.INSDNG)
            + m.tr_i_gov[i] * m.CPI
            + m.tr_i_row[i] * m.EXR
        )
    model.institution_income_definition = Constraint(
        model.INSDNG, rule=institution_income_rule
    )

    def interinstitution_transfer_rule(m, i, ip):
        return m.TRII[i, ip] == m.shii[i, ip] * (
            1.0 - m.MPS[ip]
        ) * (1.0 - m.TINS[ip]) * m.YI[ip]
    model.interinstitution_transfer_definition = Constraint(
        model.TRII_ACTIVE, rule=interinstitution_transfer_rule
    )

    def household_expenditure_rule(m, h):
        return m.EH[h] == (
            1.0 - sum(m.shii[i, h] for i in m.INSDNG)
        ) * (1.0 - m.MPS[h]) * (1.0 - m.TINS[h]) * m.YI[h]
    model.household_expenditure_definition = Constraint(
        model.H, rule=household_expenditure_rule
    )

    def market_household_demand_rule(m, c, h):
        supernumerary = m.EH[h] - sum(
            m.PQ[cp] * m.gammam[cp, h] for cp in m.C
        ) - sum(
            m.PXAC[a, cp] * m.gammah[a, cp, h]
            for a in m.A for cp in m.C
        )
        return m.PQ[c] * m.QH[c, h] == (
            m.PQ[c] * m.gammam[c, h] + m.betam[c, h] * supernumerary
        )
    model.market_household_demand = Constraint(
        model.QH_ACTIVE, rule=market_household_demand_rule
    )

    def home_household_demand_rule(m, a, c, h):
        supernumerary = m.EH[h] - sum(
            m.PQ[cp] * m.gammam[cp, h] for cp in m.C
        ) - sum(
            m.PXAC[ap, cp] * m.gammah[ap, cp, h]
            for ap in m.A for cp in m.C
        )
        return m.PXAC[a, c] * m.QHA[a, c, h] == (
            m.PXAC[a, c] * m.gammah[a, c, h]
            + m.betah[a, c, h] * supernumerary
        )
    model.home_household_demand = Constraint(
        model.QHA_ACTIVE, rule=home_household_demand_rule
    )

    model.investment_demand = Constraint(
        model.QINV_ACTIVE,
        rule=lambda m, c: m.QINV[c] == m.IADJ * m.qbarinv[c],
    )
    model.government_demand = Constraint(
        model.QG_ACTIVE,
        rule=lambda m, c: m.QG[c] == m.GADJ * m.qbarg[c],
    )

    def government_income_rule(m):
        return m.YG == (
            sum(m.TINS[i] * m.YI[i] for i in m.INSDNG)
            + sum(m.tf[f] * m.YF[f] for f in m.F)
            + sum(m.tva[a] * m.PVA[a] * m.QVA[a] for a in m.A)
            + sum(m.ta[a] * m.PA[a] * m.QA[a] for a in m.A)
            + sum(m.tm[c] * m.pwm[c] * m.QM[c] for c in m.C) * m.EXR
            + sum(m.te[c] * m.pwe[c] * m.QE[c] for c in m.C) * m.EXR
            + sum(m.tq[c] * m.PQ[c] * m.QQ[c] for c in m.C)
            + sum(m.YIF["GOV", f] for f in m.F)
            + m.tr_gov_row * m.EXR
        )
    model.government_income_definition = Constraint(rule=government_income_rule)

    model.government_expenditure_definition = Constraint(
        expr=model.EG == sum(model.PQ[c] * model.QG[c] for c in model.C)
        + sum(model.tr_i_gov[i] for i in model.INSDNG) * model.CPI
    )

    # Markets and macro balances.
    model.factor_market_equilibrium = Constraint(
        model.F,
        rule=lambda m, f: sum(m.QF[f, a] for a in m.A) == m.QFS[f],
    )

    def commodity_market_rule(m, c):
        return m.QQ[c] == (
            sum(m.QINT[c, a] for a in m.A)
            + sum(m.QH[c, h] for h in m.H)
            + m.QG[c] + m.QINV[c] + m.qdst[c] + m.QT[c]
        )
    model.commodity_market_equilibrium = Constraint(
        model.CQ, rule=commodity_market_rule
    )

    model.current_account_balance = Constraint(
        expr=sum(model.pwm[c] * model.QM[c] for c in model.C)
        + sum(model.tr_row_f[f] for f in model.F)
        == sum(model.pwe[c] * model.QE[c] for c in model.C)
        + sum(model.tr_i_row[i] for i in model.INSD)
        + model.FSAV
    )
    model.government_balance = Constraint(expr=model.YG == model.EG + model.GSAV)
    model.direct_tax_definition = Constraint(
        model.INSDNG, rule=lambda m, i: m.TINS[i] == m.tinsbar[i]
    )
    model.savings_rate_definition = Constraint(
        model.INSDNG,
        rule=lambda m, i: m.MPS[i] == m.mpsbar[i] + m.DMPS * m.mps01[i],
    )

    model.savings_investment_balance = Constraint(
        expr=sum(
            model.MPS[i] * (1.0 - model.TINS[i]) * model.YI[i]
            for i in model.INSDNG
        ) + model.GSAV + model.FSAV * model.EXR
        == sum(model.PQ[c] * model.QINV[c] for c in model.C)
        + sum(model.PQ[c] * model.qdst[c] for c in model.C)
        + model.WALRAS
    )

    absorption = (
        sum(model.PQ[c] * model.QH[c, h] for c in model.C for h in model.H)
        + sum(model.PXAC[a, c] * model.QHA[a, c, h]
              for a in model.A for c in model.C for h in model.H)
        + sum(model.PQ[c] * model.QG[c] for c in model.C)
        + sum(model.PQ[c] * model.QINV[c] for c in model.C)
        + sum(model.PQ[c] * model.qdst[c] for c in model.C)
    )
    model.total_absorption_definition = Constraint(expr=model.TABS == absorption)
    model.investment_absorption_share = Constraint(
        expr=model.INVSHR * model.TABS
        == sum(model.PQ[c] * model.QINV[c] for c in model.C)
        + sum(model.PQ[c] * model.qdst[c] for c in model.C)
    )
    model.government_absorption_share = Constraint(
        expr=model.GOVSHR * model.TABS
        == sum(model.PQ[c] * model.QG[c] for c in model.C)
    )

    object.__setattr__(model, "_ifpri_dataset", dataset)
    object.__setattr__(model, "_ifpri_calibration", cal)
    object.__setattr__(model, "_ifpri_equation_groups", MappingProxyType({
        "price": (
            "pm_definition", "pe_definition", "pdd_definition",
            "pq_definition", "px_definition", "pa_definition",
            "pinta_definition", "pva_definition", "cpi_definition",
            "dpi_definition",
        ),
        "production_trade": (
            "leontief_intermediate", "leontief_value_added",
            "ces_value_added", "ces_value_added_foc",
            "intermediate_demand", "commodity_production",
            "output_aggregation", "output_aggregation_foc",
            "cet_transformation", "export_supply",
            "cet_single_destination", "armington_aggregation",
            "armington_cost_minimization", "armington_single_source",
            "transaction_demand",
        ),
        "institution": (
            "factor_income_definition", "institution_factor_income_definition",
            "institution_income_definition",
            "interinstitution_transfer_definition",
            "household_expenditure_definition", "market_household_demand",
            "home_household_demand", "investment_demand",
            "government_demand", "government_income_definition",
            "government_expenditure_definition",
        ),
        "system": (
            "factor_market_equilibrium", "commodity_market_equilibrium",
            "current_account_balance", "government_balance",
            "direct_tax_definition", "savings_rate_definition",
            "savings_investment_balance", "total_absorption_definition",
            "investment_absorption_share", "government_absorption_share",
        ),
    }))
    return model


def _constraint_residual(data) -> float:
    body = float(value(data.body))
    lower = None if data.lower is None else float(value(data.lower))
    upper = None if data.upper is None else float(value(data.upper))
    if data.equality:
        assert lower is not None
        return body - lower
    if lower is not None and body < lower:
        return body - lower
    if upper is not None and body > upper:
        return body - upper
    return 0.0


def ifpri_benchmark_residuals(model: ConcreteModel) -> Dict[str, float]:
    """Return one signed residual for every active benchmark equation."""
    residuals: Dict[str, float] = {}
    groups = getattr(model, "_ifpri_equation_groups", {})
    for names in groups.values():
        for component_name in names:
            component = getattr(model, component_name)
            if component.is_indexed():
                for index, data in component.items():
                    label = f"{component_name}[{index!r}]"
                    residuals[label] = _constraint_residual(data)
            else:
                residuals[component_name] = _constraint_residual(component)
    return residuals


def summarize_ifpri_benchmark_residuals(model: ConcreteModel) -> IfpriResidualReport:
    """Summarize current benchmark equation residuals by equation group."""
    residuals = ifpri_benchmark_residuals(model)
    if not residuals:
        return IfpriResidualReport(0, 0.0, "", MappingProxyType({}))

    worst = max(residuals, key=lambda name: abs(residuals[name]))
    group_max: Dict[str, float] = {}
    for group, component_names in model._ifpri_equation_groups.items():
        prefixes = tuple(component_names)
        values = [
            abs(residual) for name, residual in residuals.items()
            if any(name == prefix or name.startswith(prefix + "[")
                   for prefix in prefixes)
        ]
        group_max[group] = max(values, default=0.0)
    return IfpriResidualReport(
        equation_count=len(residuals),
        max_abs_residual=abs(residuals[worst]),
        worst_equation=worst,
        group_max_abs_residual=MappingProxyType(group_max),
    )


def validate_ifpri_benchmark_model(
    model: ConcreteModel,
    tolerance: float = 1e-8,
) -> IfpriResidualReport:
    """Raise when an initialized benchmark equation exceeds ``tolerance``."""
    report = summarize_ifpri_benchmark_residuals(model)
    if not math.isfinite(report.max_abs_residual):
        raise IfpriDataError("The Pyomo benchmark contains a non-finite residual.")
    if report.max_abs_residual > tolerance:
        raise IfpriDataError(
            "Pyomo benchmark equation residual is too large: "
            f"{report.worst_equation}={report.max_abs_residual:.12g}; "
            f"tolerance={tolerance:.12g}."
        )
    return report
