# -*- coding: utf-8 -*-
"""Algebraically calibrate the IFPRI benchmark without building a solver model.

This module reconstructs the normalized benchmark prices and quantities from
an :class:`~cge_core.models.ifpri.schema.IfpriDataset`, then computes the share,
scale, tax, institutional, LES, and savings-investment parameters that make
that benchmark satisfy the model identities.  No Pyomo objects are created and
no nonlinear solver is called.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Tuple

from .schema import (
    IfpriBenchmarkCalibration,
    IfpriBenchmarkPrices,
    IfpriBenchmarkQuantities,
    IfpriDataset,
    IfpriInstitutionCalibration,
    IfpriLesCalibration,
    IfpriProductionCalibration,
    IfpriSystemCalibration,
    IfpriTaxCalibration,
)
from .validation import IfpriDataError

_TOL = 1e-14


def _ratio(numerator: float, denominator: float, *, label: str) -> float:
    if abs(denominator) <= _TOL:
        if abs(numerator) <= _TOL:
            return 0.0
        raise IfpriDataError(
            f"Cannot calibrate {label}: numerator={numerator:.12g}, "
            f"denominator={denominator:.12g}."
        )
    return numerator / denominator


def _ces_scale(output: float, terms: Iterable[Tuple[float, float]], rho: float,
               *, label: str) -> float:
    """Return the scale in ``output = alpha*(sum delta*x^-rho)^(-1/rho)``."""
    active = [(share, quantity) for share, quantity in terms
              if share > 0.0 and quantity > 0.0]
    if not active or output == 0.0:
        return 0.0
    if abs(rho) <= _TOL:
        raise IfpriDataError(f"Cobb-Douglas limit is not implemented for {label}.")
    aggregate = sum(share * quantity ** (-rho) for share, quantity in active)
    return output / aggregate ** (-1.0 / rho)


def _cet_scale(output: float, export: float, domestic: float, share: float,
               rho: float, *, label: str) -> float:
    if output == 0.0:
        return 0.0
    aggregate = share * export ** rho + (1.0 - share) * domestic ** rho
    if aggregate <= 0.0:
        raise IfpriDataError(f"Non-positive CET aggregate for {label}.")
    return output / aggregate ** (1.0 / rho)


def calibrate_ifpri_benchmark(dataset: IfpriDataset) -> IfpriBenchmarkCalibration:
    """Calibrate the supplied IFPRI benchmark entirely by algebra.

    The normalization follows the documented test data convention: activity,
    producer, export, and activity-commodity supply prices start at one, as
    does the exchange rate.  All other prices and quantities are then implied
    by the SAM and the parsed exogenous inputs.
    """
    s = dataset.sets
    sam = dataset.sam
    inputs = dataset.inputs
    taxes = inputs.taxes

    A, C, F = s.activities, s.commodities, s.factors
    H = s.households
    INSD = s.domestic_institutions
    INSDNG = s.domestic_nongovernment_institutions
    CTD = s.domestic_transaction_accounts
    CTE = s.export_transaction_accounts
    CTM = s.import_transaction_accounts

    # --- Normalized supply-side prices and core benchmark quantities ---
    pa = {a: 1.0 for a in A}
    exr = 1.0
    qa = {a: sam.column_total(a) for a in A}
    qva = {
        a: sum(sam.value(f, a) for f in F) + taxes.payment("VATAX", a)
        for a in A
    }
    pva = {a: 1.0 if qva[a] != 0.0 else 0.0 for a in A}

    pxac = {(a, c): (1.0 if sam.value(a, c) != 0.0 else 0.0)
            for a in A for c in C}
    qxac = {(a, c): sam.value(a, c) for a in A for c in C}
    qha = {
        (a, c, h): inputs.home_consumption.value_shares.get((a, c, h), 0.0)
        * sam.value(a, h)
        for a in A for c in C for h in H
    }

    qx = {c: sum(sam.value(a, c) for a in A) for c in C}
    px = {c: (1.0 if qx[c] != 0.0 else 0.0) for c in C}
    pe = {c: (1.0 if sam.value(c, "ROW") != 0.0 else 0.0) for c in C}
    qe = {
        c: (sam.value(c, "ROW") - taxes.payment("EXPTAX", c)
            - sum(sam.value(cte, c) for cte in CTE))
        if pe[c] else 0.0
        for c in C
    }
    pwe = {
        c: _ratio(sam.value(c, "ROW") / exr, qe[c], label=f"PWE[{c}]")
        if qe[c] else 0.0
        for c in C
    }
    qd = {c: max(0.0, qx[c] - qe[c]) for c in C}
    pds = {c: (1.0 if qd[c] != 0.0 else 0.0) for c in C}
    pdd = {
        c: _ratio(pds[c] * qd[c] + sum(sam.value(ctd, c) for ctd in CTD),
                  qd[c], label=f"PDD[{c}]") if qd[c] else 0.0
        for c in C
    }
    pm = {c: (pdd[c] if qd[c] else 1.0) for c in C}
    qm = {
        c: _ratio(sam.value("ROW", c) + taxes.payment("IMPTAX", c)
                  + sum(sam.value(ctm, c) for ctm in CTM),
                  pm[c], label=f"QM[{c}]")
        if sam.value("ROW", c) != 0.0 else 0.0
        for c in C
    }
    pwm = {
        c: _ratio(sam.value("ROW", c) / exr, qm[c], label=f"PWM[{c}]")
        if qm[c] else 0.0
        for c in C
    }
    qq = {c: qd[c] + qm[c] for c in C}
    pq = {
        c: _ratio(sam.row_total(c) - sam.value(c, "ROW"), qq[c],
                  label=f"PQ[{c}]") if qq[c] else 0.0
        for c in C
    }

    qinta = {a: sum(_ratio(sam.value(c, a), pq[c], label=f"QINT[{c},{a}]")
                    if pq[c] else 0.0 for c in C) for a in A}
    qint = {(c, a): (_ratio(sam.value(c, a), pq[c], label=f"QINT[{c},{a}]")
                     if pq[c] else 0.0) for c in C for a in A}
    ica = {(c, a): (_ratio(qint[(c, a)], qinta[a], label=f"ICA[{c},{a}]")
                    if qinta[a] else 0.0) for c in C for a in A}
    pinta = {a: sum(ica[(c, a)] * pq[c] for c in C) for a in A}

    # Physical factor quantities fall back to SAM values when neither supply
    # nor demand quantities were supplied in the external data file.
    qf: Dict[Tuple[str, str], float] = {}
    for f in F:
        supplied_total = inputs.factor_quantities.supply[f]
        explicit = {a: inputs.factor_quantities.demand[(f, a)] for a in A}
        factor_value = sum(sam.value(f, a) for a in A)
        for a in A:
            if explicit[a] != 0.0:
                qf[(f, a)] = explicit[a]
            elif supplied_total != 0.0 and factor_value != 0.0:
                qf[(f, a)] = supplied_total * sam.value(f, a) / factor_value
            else:
                qf[(f, a)] = sam.value(f, a)
    qfs = {f: sum(qf[(f, a)] for a in A) for f in F}
    wfa = {(f, a): (_ratio(sam.value(f, a), qf[(f, a)],
                           label=f"WFA[{f},{a}]") if qf[(f, a)] else 0.0)
           for f in F for a in A}
    wf = {f: _ratio(sum(sam.value(f, a) for a in A), qfs[f], label=f"WF[{f}]")
          if qfs[f] else 0.0 for f in F}
    wfdist = {(f, a): (_ratio(wfa[(f, a)], wf[f], label=f"WFDIST[{f},{a}]")
                       if wfa[(f, a)] else 0.0) for f in F for a in A}

    # --- Production and commodity aggregation parameters ---
    iva = {a: _ratio(qva[a], qa[a], label=f"IVA[{a}]") for a in A}
    inta = {a: _ratio(qinta[a], qa[a], label=f"INTA[{a}]") for a in A}
    theta = {
        (a, c): _ratio(sam.value(a, c) + sum(qha[(a, c, h)] for h in H),
                       qa[a], label=f"THETA[{a},{c}]")
        if pxac[(a, c)] else 0.0
        for a in A for c in C
    }

    rho_va = {a: 1.0 / inputs.elasticities.factor_substitution[a] - 1.0 for a in A}
    delta_va: Dict[Tuple[str, str], float] = {}
    alpha_va: Dict[str, float] = {}
    for a in A:
        numerators = {
            f: wfdist[(f, a)] * wf[f] * qf[(f, a)] ** (1.0 + rho_va[a])
            if qf[(f, a)] > 0.0 else 0.0
            for f in F
        }
        denominator = sum(numerators.values())
        for f in F:
            delta_va[(f, a)] = _ratio(numerators[f], denominator,
                                      label=f"DELTAVA[{f},{a}]") if denominator else 0.0
        alpha_va[a] = _ces_scale(
            qva[a], ((delta_va[(f, a)], qf[(f, a)]) for f in F), rho_va[a],
            label=f"ALPHAVA[{a}]"
        )

    rho_ac = {c: (1.0 / inputs.elasticities.output_aggregation[c] - 1.0)
              if qx[c] else 0.0 for c in C}
    delta_ac: Dict[Tuple[str, str], float] = {}
    alpha_ac: Dict[str, float] = {}
    for c in C:
        sigma = inputs.elasticities.output_aggregation[c]
        numerators = {a: (pxac[(a, c)] * qxac[(a, c)] ** (1.0 / sigma)
                          if qxac[(a, c)] > 0.0 else 0.0) for a in A}
        denominator = sum(numerators.values())
        for a in A:
            delta_ac[(a, c)] = _ratio(numerators[a], denominator,
                                      label=f"DELTAAC[{a},{c}]") if denominator else 0.0
        alpha_ac[c] = _ces_scale(
            qx[c], ((delta_ac[(a, c)], qxac[(a, c)]) for a in A), rho_ac[c],
            label=f"ALPHAAC[{c}]"
        ) if denominator else 0.0

    rho_q = {c: (1.0 / inputs.elasticities.armington[c] - 1.0)
             if qm[c] and qd[c] else 0.0 for c in C}
    delta_q: Dict[str, float] = {}
    alpha_q: Dict[str, float] = {}
    for c in C:
        if qm[c] and qd[c]:
            pre = (pm[c] / pdd[c]) * (qm[c] / qd[c]) ** (1.0 + rho_q[c])
            delta_q[c] = pre / (1.0 + pre)
            alpha_q[c] = _ces_scale(
                qq[c], ((delta_q[c], qm[c]), (1.0 - delta_q[c], qd[c])),
                rho_q[c], label=f"ALPHAQ[{c}]"
            )
        else:
            delta_q[c] = 0.0
            alpha_q[c] = 0.0

    rho_t = {c: (1.0 / inputs.elasticities.transformation[c] + 1.0)
             if qe[c] and qd[c] else 0.0 for c in C}
    delta_t: Dict[str, float] = {}
    alpha_t: Dict[str, float] = {}
    for c in C:
        if qe[c] and qd[c]:
            delta_t[c] = 1.0 / (
                1.0 + pds[c] / pe[c] * (qe[c] / qd[c]) ** (rho_t[c] - 1.0)
            )
            alpha_t[c] = _cet_scale(qx[c], qe[c], qd[c], delta_t[c], rho_t[c],
                                    label=f"ALPHAT[{c}]")
        else:
            delta_t[c] = 0.0
            alpha_t[c] = 0.0

    def transaction_shares(transaction_accounts: Tuple[str, ...]) -> Dict[str, float]:
        return {
            ct: sum(_ratio(sam.value(ct, account), sam.column_total(account),
                           label=f"transaction share[{ct},{account}]")
                    if sam.column_total(account) else 0.0
                    for account in transaction_accounts)
            for ct in C
        }

    def transaction_margins(shares, transaction_accounts, quantity):
        """Trade and transport margin needed per unit of a commodity.

        Getting a good from producer to buyer costs something: transport, trade
        services, and so on.  In a SAM those costs appear as payments to
        transaction accounts.  This works out how much of each such service is
        needed per unit of the good moved.

        The same calculation applies to goods sold at home, goods imported, and
        goods exported.  It was written out three times, once per direction,
        which is how three copies of one formula ended up in this file.

        Where either the price or the quantity is zero, the margin is reported
        as zero: there is no flow to carry, so there is nothing to charge for.
        """
        # How much is paid to these transaction accounts depends only on which
        # commodity is being moved, not on which service is doing the moving,
        # so it is worked out once per commodity.  Computing it inside both
        # loops instead would repeat the same addition once per pair.
        totals = {c: sum(sam.value(account, c) for account in transaction_accounts)
                  for c in C}

        margin = {}
        for ct in C:
            for c in C:
                movable = pq[ct] and quantity[c]
                margin[(ct, c)] = (shares[ct] * totals[c] / pq[ct] / quantity[c]
                                   if movable else 0.0)
        return margin

    sh_d = transaction_shares(CTD)
    sh_m = transaction_shares(CTM)
    sh_e = transaction_shares(CTE)
    icd = transaction_margins(sh_d, CTD, qd)   # on goods sold domestically
    icm = transaction_margins(sh_m, CTM, qm)   # on goods imported
    ice = transaction_margins(sh_e, CTE, qe)   # on goods exported

    qt = {
        ct: (sum(sam.value(ct, account) for account in CTD)
             + sum(sam.value(ct, account) for account in CTE)
             + sum(sam.value(ct, account) for account in CTM)) / pq[ct]
        if pq[ct] else 0.0
        for ct in C
    }

    # --- Taxes ---
    tax_calibration = IfpriTaxCalibration(
        activity={a: _ratio(taxes.payment("ACTTAX", a), sam.column_total(a),
                            label=f"TA[{a}]") for a in A},
        value_added={a: _ratio(taxes.payment("VATAX", a), pva[a] * qva[a],
                               label=f"TVA[{a}]") if qva[a] else 0.0 for a in A},
        commodity={c: _ratio(taxes.payment("COMTAX", c), pq[c] * qq[c],
                             label=f"TQ[{c}]") if qq[c] else 0.0 for c in C},
        import_={c: _ratio(taxes.payment("IMPTAX", c), sam.value("ROW", c),
                           label=f"TM[{c}]") if sam.value("ROW", c) else 0.0 for c in C},
        export={c: _ratio(taxes.payment("EXPTAX", c), sam.value(c, "ROW"),
                          label=f"TE[{c}]") if sam.value(c, "ROW") else 0.0 for c in C},
        factor={f: _ratio(taxes.payment("FACTAX", f), sam.column_total(f),
                          label=f"TF[{f}]") for f in F},
        institution={i: _ratio(taxes.payment("INSTAX", i), sam.column_total(i),
                               label=f"TINS[{i}]") for i in INSDNG},
    )

    # --- Institutions and LES ---
    yi = {i: sam.column_total(i) for i in INSDNG}
    yf = {f: sum(sam.value(f, a) for a in A) for f in F}
    yif = {(i, f): sam.value(i, f) for i in INSD for f in F}
    shif = {
        (i, f): _ratio(
            sam.value(i, f), sam.row_total(f) - taxes.payment("FACTAX", f)
            - sam.value("ROW", f), label=f"SHIF[{i},{f}]"
        ) for i in INSD for f in F
    }
    shii = {
        (i, ip): _ratio(
            sam.value(i, ip), sam.column_total(ip) - taxes.payment("INSTAX", ip)
            - sam.value("S-I", ip), label=f"SHII[{i},{ip}]"
        ) for i in INSDNG for ip in INSDNG
    }
    mps = {
        i: _ratio(sam.value("S-I", i), sam.column_total(i)
                  - taxes.payment("INSTAX", i), label=f"MPS[{i}]")
        for i in INSDNG
    }
    eh = {h: sum(sam.value(c, h) for c in C) + sum(sam.value(a, h) for a in A)
          for h in H}
    def deflate(column):
        """Convert a column of spending into physical quantities.

        A SAM records values — how much money changed hands.  A model needs
        quantities — how many units were bought.  Dividing a value by the price
        of the composite good gives the quantity.  Where a commodity has no
        price, because nothing of it exists in this economy, the quantity is
        zero rather than an error.
        """
        return {c: (sam.value(c, column) / pq[c] if pq[c] else 0.0) for c in C}

    qh = {(c, h): (sam.value(c, h) / pq[c] if pq[c] else 0.0)
          for c in C for h in H}
    qg = deflate("GOV")
    yg = sam.column_total("GOV")
    gsav = sam.value("S-I", "GOV")
    eg = yg - gsav

    market_budget = {(c, h): _ratio(sam.value(c, h), eh[h],
                                     label=f"BUDSHR[{c},{h}]")
                     for c in C for h in H}
    home_budget = {(a, c, h): _ratio(sam.value(a, h)
                                     * inputs.home_consumption.value_shares.get((a, c, h), 0.0),
                                     eh[h], label=f"BUDSHR2[{a},{c},{h}]")
                   for a in A for c in C for h in H}
    elasticity_check = {
        h: (sum(market_budget[(c, h)] * inputs.elasticities.market_expenditure[(c, h)]
                for c in C)
            + sum(home_budget[(a, c, h)]
                  * inputs.elasticities.home_expenditure[(a, c, h)]
                  for a in A for c in C))
        for h in H
    }
    norm_market = {(c, h): inputs.elasticities.market_expenditure[(c, h)]
                    / elasticity_check[h] for c in C for h in H}
    norm_home = {(a, c, h): inputs.elasticities.home_expenditure[(a, c, h)]
                  / elasticity_check[h] for a in A for c in C for h in H}
    beta_m = {(c, h): market_budget[(c, h)] * norm_market[(c, h)]
              for c in C for h in H}
    beta_h = {(a, c, h): home_budget[(a, c, h)] * norm_home[(a, c, h)]
              for a in A for c in C for h in H}
    gamma_m = {
        (c, h): (eh[h] / pq[c])
        * (market_budget[(c, h)] + beta_m[(c, h)] / inputs.elasticities.frisch[h])
        if market_budget[(c, h)] and pq[c] else 0.0
        for c in C for h in H
    }
    gamma_h = {
        (a, c, h): (eh[h] / pxac[(a, c)])
        * (home_budget[(a, c, h)] + beta_h[(a, c, h)] / inputs.elasticities.frisch[h])
        if home_budget[(a, c, h)] and pxac[(a, c)] else 0.0
        for a in A for c in C for h in H
    }
    supernum = {
        h: sum(gamma_h[(a, c, h)] * pxac[(a, c)] for a in A for c in C)
        + sum(gamma_m[(c, h)] * pq[c] for c in C)
        for h in H
    }
    implied_frisch = {h: -eh[h] / (eh[h] - supernum[h]) for h in H}

    institutions = IfpriInstitutionCalibration(
        institution_income=yi,
        factor_income=yf,
        institution_factor_income=yif,
        factor_income_share=shif,
        interinstitution_share=shii,
        savings_rate=mps,
        household_expenditure=eh,
        government_income=yg,
        government_expenditure=eg,
        government_saving=gsav,
    )
    les = IfpriLesCalibration(
        market_budget_share=market_budget,
        home_budget_share=home_budget,
        normalized_market_elasticity=norm_market,
        normalized_home_elasticity=norm_home,
        market_marginal_share=beta_m,
        home_marginal_share=beta_h,
        market_subsistence=gamma_m,
        home_subsistence=gamma_h,
        supernumerary_income=supernum,
        implied_frisch=implied_frisch,
    )

    # --- Price indices and savings-investment aggregates ---
    market_hh_total = sum(sam.value(c, h) for c in C for h in H)
    cwts = {c: _ratio(sum(sam.value(c, h) for h in H), market_hh_total,
                      label=f"CWTS[{c}]") for c in C}
    domestic_values = {
        c: sum(sam.value(a, c) for a in A)
        - (sam.value(c, "ROW") - sum(sam.value(cte, c) for cte in CTE))
        for c in C
    }
    domestic_total = sum(domestic_values.values())
    dwts = {c: _ratio(domestic_values[c], domestic_total, label=f"DWTS[{c}]")
            for c in C}
    cpi = sum(cwts[c] * pq[c] for c in C)
    dpi = sum(dwts[c] * pds[c] for c in C if qd[c])

    qinv = deflate("S-I")    # goods bought as investment
    qdst = deflate("DSTK")   # goods added to or taken from stocks
    fsav = sam.value("S-I", "ROW") / exr
    # Total absorption: everything the economy uses, however it is used.  The
    # first term is household purchases of marketed goods, which was already
    # needed above as `market_hh_total` and is reused here rather than summed
    # a second time.
    tabs = (market_hh_total
            + sum(sam.value(a, h) for a in A for h in H)
            + sum(sam.value(c, "GOV") for c in C)
            + sum(sam.value(c, "S-I") for c in C)
            + sum(sam.value(c, "DSTK") for c in C))
    inv_share = _ratio(sam.column_total("S-I"), tabs, label="INVSHR")
    gov_share = _ratio(sum(sam.value(c, "GOV") for c in C), tabs, label="GOVSHR")

    prices = IfpriBenchmarkPrices(
        exchange_rate=exr,
        activity=pa,
        activity_commodity=pxac,
        value_added=pva,
        intermediate_aggregate=pinta,
        marketed_output=px,
        domestic_supply=pds,
        domestic_demand=pdd,
        export=pe,
        import_=pm,
        composite=pq,
        world_export=pwe,
        world_import=pwm,
        factor=wf,
        factor_activity=wfdist,
    )
    quantities = IfpriBenchmarkQuantities(
        activity=qa,
        value_added=qva,
        activity_commodity=qxac,
        home_consumption=qha,
        marketed_output=qx,
        domestic_sales=qd,
        exports=qe,
        imports=qm,
        composite_supply=qq,
        factor_demand=qf,
        factor_supply=qfs,
        intermediate=qint,
        intermediate_aggregate=qinta,
        transaction_demand=qt,
        household_market=qh,
        government=qg,
        investment=qinv,
        stock_change=qdst,
    )
    production = IfpriProductionCalibration(
        value_added_coefficient=iva,
        intermediate_coefficient=inta,
        intermediate_shares=ica,
        yield_coefficient=theta,
        factor_exponent=rho_va,
        factor_shares=delta_va,
        factor_scale=alpha_va,
        output_exponent=rho_ac,
        output_shares=delta_ac,
        output_scale=alpha_ac,
        armington_exponent=rho_q,
        armington_share=delta_q,
        armington_scale=alpha_q,
        cet_exponent=rho_t,
        cet_share=delta_t,
        cet_scale=alpha_t,
        transaction_domestic=icd,
        transaction_import=icm,
        transaction_export=ice,
    )
    system = IfpriSystemCalibration(
        consumer_price_weights=cwts,
        domestic_price_weights=dwts,
        consumer_price_index=cpi,
        domestic_price_index=dpi,
        foreign_saving=fsav,
        total_absorption=tabs,
        investment_share=inv_share,
        government_share=gov_share,
        walras_residual=0.0,
    )
    return IfpriBenchmarkCalibration(
        prices=prices,
        quantities=quantities,
        production=production,
        taxes=tax_calibration,
        institutions=institutions,
        les=les,
        system=system,
    )



def validate_ifpri_calibration(dataset: IfpriDataset,
                               calibration: IfpriBenchmarkCalibration,
                               tolerance: float = 1e-8) -> None:
    """Check the calibrated benchmark identities without invoking a solver."""
    s = dataset.sets
    q = calibration.quantities
    p = calibration.prices
    prod = calibration.production
    les = calibration.les

    def close(actual: float, expected: float, label: str) -> None:
        if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
            raise IfpriDataError(
                f"Calibration identity {label} failed: "
                f"actual={actual:.12g}, expected={expected:.12g}."
            )

    for c in s.commodities:
        close(q.marketed_output[c], q.domestic_sales[c] + q.exports[c],
              f"marketed output[{c}]")
        close(q.composite_supply[c], q.domestic_sales[c] + q.imports[c],
              f"composite supply[{c}]")

    for a in s.activities:
        if q.value_added[a] > tolerance:
            close(sum(prod.factor_shares[(f, a)] for f in s.factors), 1.0,
                  f"factor shares[{a}]")
            rho = prod.factor_exponent[a]
            aggregate = sum(
                prod.factor_shares[(f, a)]
                * q.factor_demand[(f, a)] ** (-rho)
                for f in s.factors if q.factor_demand[(f, a)] > 0.0
            ) ** (-1.0 / rho)
            close(prod.factor_scale[a] * aggregate, q.value_added[a],
                  f"value-added CES[{a}]")

    for c in s.commodities:
        active_outputs = [a for a in s.activities
                          if q.activity_commodity[(a, c)] > 0.0]
        if active_outputs:
            close(sum(prod.output_shares[(a, c)] for a in s.activities), 1.0,
                  f"output shares[{c}]")
            rho = prod.output_exponent[c]
            aggregate = sum(
                prod.output_shares[(a, c)]
                * q.activity_commodity[(a, c)] ** (-rho)
                for a in active_outputs
            ) ** (-1.0 / rho)
            close(prod.output_scale[c] * aggregate, q.marketed_output[c],
                  f"output aggregation[{c}]")

        if q.imports[c] > 0.0 and q.domestic_sales[c] > 0.0:
            rho = prod.armington_exponent[c]
            share = prod.armington_share[c]
            aggregate = (
                share * q.imports[c] ** (-rho)
                + (1.0 - share) * q.domestic_sales[c] ** (-rho)
            ) ** (-1.0 / rho)
            close(prod.armington_scale[c] * aggregate, q.composite_supply[c],
                  f"Armington aggregation[{c}]")

        if q.exports[c] > 0.0 and q.domestic_sales[c] > 0.0:
            rho = prod.cet_exponent[c]
            share = prod.cet_share[c]
            aggregate = (
                share * q.exports[c] ** rho
                + (1.0 - share) * q.domestic_sales[c] ** rho
            ) ** (1.0 / rho)
            close(prod.cet_scale[c] * aggregate, q.marketed_output[c],
                  f"CET transformation[{c}]")

    for h in s.households:
        close(
            sum(les.market_budget_share[(c, h)] for c in s.commodities)
            + sum(les.home_budget_share[(a, c, h)]
                  for a in s.activities for c in s.commodities),
            1.0, f"LES budget shares[{h}]"
        )
        close(
            sum(les.market_marginal_share[(c, h)] for c in s.commodities)
            + sum(les.home_marginal_share[(a, c, h)]
                  for a in s.activities for c in s.commodities),
            1.0, f"LES marginal shares[{h}]"
        )
        close(les.implied_frisch[h], dataset.inputs.elasticities.frisch[h],
              f"Frisch parameter[{h}]")

    close(sum(calibration.system.consumer_price_weights.values()), 1.0,
          "consumer price weights")
    close(sum(calibration.system.domestic_price_weights.values()), 1.0,
          "domestic price weights")

    for mapping_name, mapping in (
        ("activity prices", p.activity),
        ("composite prices", p.composite),
        ("factor prices", p.factor),
    ):
        for key, value in mapping.items():
            if not math.isfinite(value):
                raise IfpriDataError(
                    f"Non-finite calibrated {mapping_name}[{key!r}]={value!r}."
                )
