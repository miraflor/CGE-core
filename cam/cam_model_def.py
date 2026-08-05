# -*- coding: utf-8 -*-
"""camcge (GAMS Model Library SEQ=81) as a CGE-Core model definition.

1:1 port of Condon, Dahl & Devarajan (1987), "Implementing a Computable
General Equilibrium Model on GAMS: The Cameroon Model", World Bank DRD290.
Dervis-de Melo-Robinson style: Cobb-Douglas production over three labor
categories with fixed sectoral capital, Armington imports, CET + finite-
elasticity export demand, savings-driven closure (mps fixed), fixed er and
world import prices as the price anchor, Walras redundancy in the current
account (caeq).

Engine mapping (differs from stdcge, disclosed):
  * model_instance('mps', None)  -> the closure fix (savings-driven closure,
    DMR ch.7), not a price numeraire; prices are anchored by the fixed
    exchange-rate parameter er and fixed world import prices pwm.
  * model_drop_redundant('caeq') -> Walras' law drops the current account
    (the paper's own choice: "Implied by Walras' Law").
  * Exogenous-throughout closure items (k, pwm, ls, er, te) are mutable
    Params rather than fixed Vars; policy levers (tm, fsav, gdtot) are
    mutable Params reachable via model_modify_sim.

Variable bounds reproduce the GAMS file (.01 lower bounds on the listed
variables; pe/pva/cd/gd/id/dst/dk free) with one added numerical guard:
cd >= .01 for sectors with cles > 0 (verified non-binding at solution).
Initialization reproduces GAMS levels; variables GAMS leaves at default 0
(hhsav, govsav, deprecia, duty, dk) are initialized at their base-
consistent values instead - initialization only, no model change.
"""
from pyomo.environ import (
    AbstractModel, Constraint, Objective, Param, Set, Var, maximize, prod,
    value,
)

LB = .01


class CamModelDef:
    redundant_constraints = frozenset({'caeq'})
    required_data_files = frozenset({
        'set-i-.csv', 'set-lc-.csv', 'set-zrow-.csv',
        'param-io-.csv', 'param-imat-.csv', 'param-wdist-.csv',
        'param-xle-.csv', 'param-zz-.csv',
    })
    numeraire_variables = frozenset({'mps'})

    def model(self):
        self.m = m = AbstractModel()

        # sets and raw tables -------------------------------------------
        m.i = Set(doc='sectors')
        m.lc = Set(doc='labor categories')
        m.zrow = Set(doc='zz row labels')
        m.io = Param(m.i, m.i, default=0)
        m.imat = Param(m.i, m.i, default=0)
        m.wdist = Param(m.i, m.lc, default=0)
        m.xle = Param(m.i, m.lc, default=0)
        m.zz = Param(m.zrow, m.i, default=0)

        m.it = Set(within=m.i, initialize=lambda m: [
            i for i in m.i if value(m.zz['m0', i]) > 0])
        m.iN = Set(within=m.i, initialize=lambda m: [
            i for i in m.i if value(m.zz['m0', i]) == 0])
        m.LP = Set(dimen=2, initialize=lambda m: [
            (i, l) for i in m.i for l in m.lc if value(m.wdist[i, l]) > 0])

        # scalars hardcoded in camcge.gms -------------------------------
        m.er = Param(initialize=.21, mutable=True)
        m.gr0 = Param(initialize=179.00)
        m.gdtot = Param(initialize=135.03, mutable=True)   # gdtot.fx
        m.cdtot0 = Param(initialize=947.98)
        m.fsav = Param(initialize=36.841, mutable=True)    # fsav.fx
        _wa0 = {'rural': .11, 'urban-unsk': .15678, 'urban-skil': 1.8657}
        m.wa0 = Param(m.lc, initialize=lambda m, l: _wa0[l])
        m.mps0 = Param(initialize=.09305)

        # GAMS parameter assignments ------------------------------------
        z = lambda r: (lambda m, i: m.zz[r, i])
        m.depr = Param(m.i, initialize=z('depr'))
        m.rhoc = Param(m.i, initialize=lambda m, i: 1 / m.zz['rhoc', i] - 1)
        m.rhot = Param(m.i, initialize=lambda m, i: 1 / m.zz['rhot', i] + 1)
        m.eta = Param(m.i, initialize=z('eta'))
        m.tm0 = Param(m.i, initialize=z('tm0'))
        m.tm = Param(m.it, initialize=lambda m, i: m.tm0[i], mutable=True)
        m.te = Param(m.i, initialize=0, mutable=True)
        m.itax = Param(m.i, initialize=z('itax'))
        m.cles = Param(m.i, initialize=z('cles'))
        m.gles = Param(m.i, initialize=z('gles'))
        m.kio = Param(m.i, initialize=z('kio'))
        m.dstr = Param(m.i, initialize=z('dstr'))
        m.m0 = Param(m.i, initialize=z('m0'))
        m.e0 = Param(m.i, initialize=z('e0'))
        m.xd0 = Param(m.i, initialize=z('xd0'))
        m.kap = Param(m.i, initialize=z('k'), mutable=True)     # k.fx
        m.pd0 = Param(m.i, initialize=z('pd0'))
        m.pm0 = Param(m.i, initialize=lambda m, i: m.pd0[i])
        m.pe0 = Param(m.i, initialize=lambda m, i: m.pd0[i])
        m.pwm = Param(m.it, mutable=True, initialize=lambda m, i:
                      m.pm0[i] / ((1 + m.tm0[i]) * m.er))       # pwm.fx
        m.pwe0 = Param(m.it, initialize=lambda m, i:
                       m.pe0[i] * (1 + m.te[i]) / m.er)
        m.pva0 = Param(m.i, initialize=lambda m, i:
                       m.pd0[i] - sum(m.io[j, i] * m.pd0[j] for j in m.i)
                       - m.itax[i])
        m.xxd0 = Param(m.i, initialize=lambda m, i: m.xd0[i] - m.e0[i])
        m.dst0 = Param(m.i, initialize=z('dst'))
        m.id0 = Param(m.i, initialize=z('id'))
        m.ls0 = Param(m.lc, initialize=lambda m, l:
                      sum(m.xle[i, l] for i in m.i))            # ls.fx

        # calibration ---------------------------------------------------
        def delta_init(m, i):
            d = (m.pm0[i] / m.pd0[i]
                 * (m.m0[i] / m.xxd0[i]) ** (1 + m.rhoc[i]))
            return d / (1 + d)
        m.delta = Param(m.it, initialize=delta_init)
        m.x0 = Param(m.i, initialize=lambda m, i:
                     m.pd0[i] * m.xxd0[i]
                     + (m.pm0[i] * m.m0[i] if i in m.it else 0))
        m.ac = Param(m.it, initialize=lambda m, i: m.x0[i] / (
            m.delta[i] * m.m0[i] ** (-m.rhoc[i])
            + (1 - m.delta[i]) * m.xxd0[i] ** (-m.rhoc[i])
        ) ** (-1 / m.rhoc[i]))
        m.int0 = Param(m.i, initialize=lambda m, i:
                       sum(m.io[i, j] * m.xd0[j] for j in m.i))
        m.gamma = Param(m.it, initialize=lambda m, i: 1 / (
            1 + m.pd0[i] / m.pe0[i]
            * (m.e0[i] / m.xxd0[i]) ** (m.rhot[i] - 1)))
        m.alphl = Param(m.LP, initialize=lambda m, i, l:
                        m.wdist[i, l] * m.wa0[l] * m.xle[i, l]
                        / (m.pva0[i] * m.xd0[i]))
        m.ad = Param(m.i, initialize=lambda m, i: m.xd0[i] / (
            prod([m.xle[i, l] ** m.alphl[i, l]
                  for l in m.lc if (i, l) in m.LP])
            * m.kap[i] ** (1 - sum(m.alphl[i, l]
                                   for l in m.lc if (i, l) in m.LP))))
        m.at = Param(m.it, initialize=lambda m, i: m.xd0[i] / (
            m.gamma[i] * m.e0[i] ** m.rhot[i]
            + (1 - m.gamma[i]) * m.xxd0[i] ** m.rhot[i]
        ) ** (1 / m.rhot[i]))
        m.y0 = Param(initialize=lambda m: sum(
            m.pva0[i] * m.xd0[i] - m.depr[i] * m.kap[i] for i in m.i))

        # variables (GAMS bounds and levels) ----------------------------
        one = lambda m, *a: 1
        m.pd = Var(m.i, initialize=one, bounds=(LB, None))
        m.pm = Var(m.it, initialize=one, bounds=(LB, None))
        m.pe = Var(m.it, initialize=one)
        m.pk = Var(m.i, initialize=one, bounds=(LB, None))
        m.px = Var(m.i, initialize=one, bounds=(LB, None))
        m.p = Var(m.i, initialize=one, bounds=(LB, None))
        m.pva = Var(m.i, initialize=lambda m, i: m.pva0[i])
        m.pwe = Var(m.it, initialize=lambda m, i: m.pwe0[i],
                    bounds=(LB, None))
        m.x = Var(m.i, initialize=lambda m, i: m.x0[i], bounds=(LB, None))
        m.xd = Var(m.i, initialize=lambda m, i: m.xd0[i], bounds=(LB, None))
        m.xxd = Var(m.i, initialize=lambda m, i: m.xxd0[i],
                    bounds=lambda m, i: (LB if i in m.it else None, None))
        m.e = Var(m.it, initialize=lambda m, i: m.e0[i], bounds=(LB, None))
        m.mq = Var(m.it, initialize=lambda m, i: m.m0[i], bounds=(LB, None))
        m.wa = Var(m.lc, initialize=lambda m, l: m.wa0[l], bounds=(LB, None))
        m.l = Var(m.LP, initialize=lambda m, i, l: m.xle[i, l],
                  bounds=(LB, None))
        m.intm = Var(m.i, initialize=lambda m, i: m.int0[i],
                     bounds=(LB, None))
        m.cd = Var(m.i, initialize=lambda m, i: m.cles[i] * m.cdtot0,
                   bounds=lambda m, i: (LB if value(m.cles[i]) > 0 else None,
                                        None))
        m.gd = Var(m.i, initialize=lambda m, i:
                   value(m.gdtot) if value(m.gles[i]) > 0 else 0)
        m.idv = Var(m.i, initialize=lambda m, i: m.id0[i])
        m.dst = Var(m.i, initialize=lambda m, i: m.dst0[i])
        m.y = Var(initialize=lambda m: m.y0, bounds=(LB, None))
        m.gr = Var(initialize=lambda m: m.gr0)
        m.tariff = Var(initialize=76.548)
        m.indtax = Var(initialize=102.45)
        m.duty = Var(initialize=0)
        m.mps = Var(initialize=lambda m: m.mps0)         # fixed via engine
        m.hhsav = Var(initialize=lambda m: value(m.mps0) * value(m.y0))
        m.govsav = Var(initialize=lambda m: value(m.gr0) - value(m.gdtot))
        m.deprecia = Var(initialize=lambda m: sum(
            value(m.depr[i]) * value(m.kap[i]) for i in m.i))
        m.savings = Var(initialize=280.98)
        m.dk = Var(m.i, initialize=lambda m, i: value(m.kio[i]) * (
            280.98 - sum(value(m.dst0[j]) for j in m.i)))

        # equations (names and forms as in camcge.gms) ------------------
        m.pmdef = Constraint(m.it, rule=lambda m, i:
            m.pm[i] == m.pwm[i] * m.er * (1 + m.tm[i]))
        m.pedef = Constraint(m.it, rule=lambda m, i:
            m.pe[i] * (1 + m.te[i]) == m.pwe[i] * m.er)
        m.absorption = Constraint(m.i, rule=lambda m, i:
            m.p[i] * m.x[i] == m.pd[i] * m.xxd[i]
            + (m.pm[i] * m.mq[i] if i in m.it else 0))
        m.sales = Constraint(m.i, rule=lambda m, i:
            m.px[i] * m.xd[i] == m.pd[i] * m.xxd[i]
            + (m.pe[i] * m.e[i] if i in m.it else 0))
        m.actp = Constraint(m.i, rule=lambda m, i:
            m.px[i] * (1 - m.itax[i]) == m.pva[i]
            + sum(m.io[j, i] * m.p[j] for j in m.i))
        m.pkdef = Constraint(m.i, rule=lambda m, i:
            m.pk[i] == sum(m.p[j] * m.imat[j, i] for j in m.i))
        m.activity = Constraint(m.i, rule=lambda m, i:
            m.xd[i] == m.ad[i]
            * prod([m.l[i, l] ** m.alphl[i, l]
                    for l in m.lc if (i, l) in m.LP])
            * m.kap[i] ** (1 - sum(m.alphl[i, l]
                                   for l in m.lc if (i, l) in m.LP)))
        m.profitmax = Constraint(m.LP, rule=lambda m, i, l:
            m.wa[l] * m.wdist[i, l] * m.l[i, l]
            == m.xd[i] * m.pva[i] * m.alphl[i, l])
        m.lmequil = Constraint(m.lc, rule=lambda m, l:
            sum(m.l[i, l] for i in m.i if (i, l) in m.LP) == m.ls0[l])
        m.cet = Constraint(m.it, rule=lambda m, i:
            m.xd[i] == m.at[i] * (
                m.gamma[i] * m.e[i] ** m.rhot[i]
                + (1 - m.gamma[i]) * m.xxd[i] ** m.rhot[i]
            ) ** (1 / m.rhot[i]))
        m.edemand = Constraint(m.it, rule=lambda m, i:
            m.e[i] / m.e0[i] == (m.pwe0[i] / m.pwe[i]) ** m.eta[i])
        m.esupply = Constraint(m.it, rule=lambda m, i:
            m.e[i] / m.xxd[i] == (
                m.pe[i] / m.pd[i] * (1 - m.gamma[i]) / m.gamma[i]
            ) ** (1 / (m.rhot[i] - 1)))
        m.armington = Constraint(m.it, rule=lambda m, i:
            m.x[i] == m.ac[i] * (
                m.delta[i] * m.mq[i] ** (-m.rhoc[i])
                + (1 - m.delta[i]) * m.xxd[i] ** (-m.rhoc[i])
            ) ** (-1 / m.rhoc[i]))
        m.costmin = Constraint(m.it, rule=lambda m, i:
            m.mq[i] / m.xxd[i] == (
                m.pd[i] / m.pm[i] * m.delta[i] / (1 - m.delta[i])
            ) ** (1 / (1 + m.rhoc[i])))
        m.xxdsn = Constraint(m.iN, rule=lambda m, i: m.xxd[i] == m.xd[i])
        m.xsn = Constraint(m.iN, rule=lambda m, i: m.x[i] == m.xxd[i])
        m.inteq = Constraint(m.i, rule=lambda m, j:
            m.intm[j] == sum(m.io[j, i] * m.xd[i] for i in m.i))
        m.dsteq = Constraint(m.i, rule=lambda m, i:
            m.dst[i] == m.dstr[i] * m.xd[i])
        m.cdeq = Constraint(m.i, rule=lambda m, i:
            m.p[i] * m.cd[i] == m.cles[i] * (1 - m.mps) * m.y)
        m.gdp = Constraint(rule=lambda m:
            m.y == sum(m.pva[i] * m.xd[i] for i in m.i) - m.deprecia)
        m.hhsaveq = Constraint(rule=lambda m: m.hhsav == m.mps * m.y)
        m.greq = Constraint(rule=lambda m:
            m.gr == m.tariff + m.duty + m.indtax)
        m.gruse = Constraint(rule=lambda m:
            m.gr == sum(m.p[i] * m.gd[i] for i in m.i) + m.govsav)
        m.gdeq = Constraint(m.i, rule=lambda m, i:
            m.gd[i] == m.gles[i] * m.gdtot)
        m.tariffdef = Constraint(rule=lambda m:
            m.tariff == sum(m.tm[i] * m.mq[i] * m.pwm[i]
                            for i in m.it) * m.er)
        m.indtaxdef = Constraint(rule=lambda m:
            m.indtax == sum(m.itax[i] * m.px[i] * m.xd[i] for i in m.i))
        m.dutydef = Constraint(rule=lambda m:
            m.duty == sum(m.te[i] * m.e[i] * m.pe[i] for i in m.it))
        m.depreq = Constraint(rule=lambda m:
            m.deprecia == sum(m.depr[i] * m.pk[i] * m.kap[i] for i in m.i))
        m.totsav = Constraint(rule=lambda m:
            m.savings == m.hhsav + m.govsav + m.deprecia + m.fsav * m.er)
        m.prodinv = Constraint(m.i, rule=lambda m, i:
            m.pk[i] * m.dk[i] == m.kio[i] * m.savings
            - m.kio[i] * sum(m.dst[j] * m.p[j] for j in m.i))
        m.ieq = Constraint(m.i, rule=lambda m, i:
            m.idv[i] == sum(m.imat[i, j] * m.dk[j] for j in m.i))
        m.caeq = Constraint(rule=lambda m:
            sum(m.pwm[i] * m.mq[i] for i in m.it)
            == sum(m.pwe[i] * m.e[i] for i in m.it) + m.fsav)
        m.equil = Constraint(m.i, rule=lambda m, i:
            m.x[i] == m.intm[i] + m.cd[i] + m.gd[i] + m.idv[i] + m.dst[i])
        m.obj = Objective(sense=maximize, rule=lambda m: prod(
            [m.cd[i] ** m.cles[i] for i in m.i if value(m.cles[i]) > 0]))
        return self.m
