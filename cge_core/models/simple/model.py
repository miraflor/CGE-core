# -*- coding: utf-8 -*-
r"""
Simple CGE model definition (Hosoe, Gasawa & Hashimoto 2010, Ch. 3-4).
----------------------------------------------------------------------

Pyomo port of ``splcge.gms`` (GAMS Model Library, SEQ=275): a static,
closed-economy CGE model with Cobb-Douglas production and Cobb-Douglas
utility, no government, no trade, and no intermediates. Goods
``i in {BRD, MLK}``, factors ``h in {CAP, LAB}``. This is Hosoe's
pedagogical "simplest CGE" and the natural first read before
``stdcge_model_def.py``.

Style note (for readers coming from OG-Core):
    See the header of ``stdcge_model_def.py``. As there, docstrings
    follow OG-Core's (DeBacker & Evans) convention -- ``.. math::``
    statements with Args/Returns -- and each constraint carries the
    equation name used in the GAMS source so it can be checked line by
    line against ``splcge.gms``.

Reference:
    Hosoe, N., Gasawa, K. & Hashimoto, H. (2010). *Textbook of
    Computable General Equilibrium Modelling: Programming and
    Simulations*. Palgrave Macmillan. doi:10.1057/9780230281653

Provenance and authorship:
    Original Pyomo port: Charley Burtwistle (cmb11) with Juan Fung,
    U.S. National Institute of Standards and Technology (2017),
    https://github.com/juanfung/pycge -- a U.S. Government work in the
    public domain (17 U.S.C. 105). **The underlying model port is not
    the fork maintainer's work.**

    This fork (CGE-Core): revised and annotated by James Matthew
    Miraflor (2026) via an AI-assisted ("vibecoded") workflow directed
    and reviewed by him. Changes relative to PyCGE: ``np.prod`` ->
    Pyomo ``prod``; removed unused numpy import; OG-Core-style
    documentation. The economics is unchanged; see CHANGELOG.md.
"""
import logging

from pyomo.environ import (
    AbstractModel,
    Constraint,
    Objective,
    Param,
    PositiveReals,
    Set,
    Var,
    maximize,
    prod,
)

from cge_core.models._accounts import merge_accounts

logger = logging.getLogger(__name__)

# Numerical guard reproduced from the reference implementation; the
# simple model uses a larger bound than stdcge (1e-3 vs 1e-5). See
# docs/MODEL.md, "Numerical lower bounds".
SPLCGE_LOWER_BOUND = 1e-3

#: Default institutional account labels (the simple model has only the
#: household). Pass ``accounts={'hoh': ...}`` to relabel.
SPLCGE_ACCOUNTS = {'hoh': 'HOH'}


class SplModelDef:
    r"""Builder for the Hosoe simple CGE model as a Pyomo AbstractModel.

    Exposes a single method, :meth:`model`, matching the ``model_def``
    protocol expected by :class:`cge_core._pycge.PyCGE`.

    Args:
        accounts (dict, optional): overrides for the institutional
            account labels; see :data:`SPLCGE_ACCOUNTS`. The simple
            model has only ``hoh`` (the household).
    """

    redundant_constraints = frozenset({'eqpf', 'eqpx'})
    required_data_files = frozenset({
        'set-i-.csv', 'set-h-.csv', 'set-u-.csv', 'param-sam-.csv',
    })
    numeraire_variables = frozenset({'pf', 'px', 'pz'})

    def __init__(self, accounts=None):
        # Shared with the standard model; see cge_core/models/_accounts.py.
        # This model names only the household account, so there is nothing for
        # a distinctness check to compare against.
        self.accounts = merge_accounts(SPLCGE_ACCOUNTS, accounts)

    def model(self):
        r"""Declare and return the simple-model AbstractModel.

        Returns:
            m (pyomo.environ.AbstractModel): the abstract simple CGE
                model; data are attached later via a DataPortal.
        """
        # Institutional account label (configurable; see SPLCGE_ACCOUNTS).
        HOH = self.accounts['hoh']

        # ------------------------------------------------------------------ #
        # MODEL OBJECT
        # ------------------------------------------------------------------ #
        self.m = AbstractModel()

        # ------------------------------------------------------------------ #
        # SETS
        # ------------------------------------------------------------------ #
        self.m.i = Set(doc='goods')
        self.m.h = Set(doc='factor')
        self.m.u = Set(doc='SAM entry')

        # ------------------------------------------------------------------ #
        # BENCHMARK DATA (the social accounting matrix)
        # ------------------------------------------------------------------ #
        self.m.sam = Param(self.m.u, self.m.u,
                           doc='social accounting matrix')

        # ------------------------------------------------------------------ #
        # BENCHMARK MAGNITUDES (GAMS *0 parameters)
        # ------------------------------------------------------------------ #
        def X0_init(model, i):
            r"""Benchmark household consumption of good :math:`i`.

            .. math::
                X_{0,i} = \mathrm{SAM}[i, \mathrm{HOH}]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                X0 (scalar): base-year household purchase of good
                    :math:`i`
            """
            return model.sam[i, HOH]

        self.m.X0 = Param(self.m.i,
                          initialize=X0_init,
                          doc='hh consumption of i-th good', mutable=True)

        def F0_init(model, h, i):
            r"""Benchmark factor input.

            .. math::
                F_{0,h,i} = \mathrm{SAM}[h, i]

            Args:
                model (AbstractModel): model under construction
                h (str): element of factor set ``h``
                i (str): element of goods set ``i``

            Returns:
                F0 (scalar): base-year payment by sector :math:`i` to
                    factor :math:`h`
            """
            return model.sam[h, i]

        self.m.F0 = Param(self.m.h, self.m.i,
                          initialize=F0_init,
                          doc='h-th factor input by j-th firm',
                          mutable=True)

        def Z0_init(model, i):
            r"""Benchmark output of good :math:`i`. With no
            intermediates, output equals total factor input.

            .. math::
                Z_{0,i} = \sum_{h} F_{0,h,i}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Z0 (scalar): base-year output of good :math:`i`
            """
            return sum(model.F0[h, i] for h in model.h)

        self.m.Z0 = Param(self.m.i,
                          initialize=Z0_init,
                          doc='output of j-th good', mutable=True)

        def FF_init(model, h):
            r"""Factor endowment of the household (exogenous supply).

            .. math::
                FF_{h} = \mathrm{SAM}[\mathrm{HOH}, h]

            Args:
                model (AbstractModel): model under construction
                h (str): element of factor set ``h``

            Returns:
                FF (scalar): endowment of factor :math:`h`
            """
            return model.sam[HOH, h]

        self.m.FF = Param(self.m.h,
                          initialize=FF_init,
                          doc='factor endowment of the h-th factor',
                          mutable=True)

        # ------------------------------------------------------------------ #
        # CALIBRATED BEHAVIOURAL PARAMETERS
        # Shares and scale parameters recovered so the model reproduces
        # the SAM exactly at unit prices.
        # ------------------------------------------------------------------ #
        def alpha_init(model, i):
            r"""Cobb-Douglas utility share of good :math:`i`.

            .. math::
                \alpha_{i} = \frac{X_{0,i}}{\sum_{j} X_{0,j}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                alpha (scalar): household expenditure share on good
                    :math:`i`; shares sum to one
            """
            return model.X0[i] / sum(model.X0[j] for j in model.i)

        self.m.alpha = Param(self.m.i,
                             initialize=alpha_init,
                             doc='share parameter in utility function')

        def beta_init(model, h, i):
            r"""Cobb-Douglas factor share in production.

            .. math::
                \beta_{h,i} = \frac{F_{0,h,i}}{\sum_{k} F_{0,k,i}}

            Args:
                model (AbstractModel): model under construction
                h (str): element of factor set ``h``
                i (str): element of goods set ``i``

            Returns:
                beta (scalar): cost share of factor :math:`h` in
                    sector :math:`i`
            """
            return model.F0[h, i] / sum(model.F0[k, i] for k in model.h)

        self.m.beta = Param(self.m.h, self.m.i,
                            initialize=beta_init,
                            doc='share parameter in production function')

        def b_init(model, i):
            r"""Scale (TFP) parameter of the production function,
            recovered so production reproduces the benchmark.

            .. math::
                b_{i} = \frac{Z_{0,i}}
                             {\prod_{h} F_{0,h,i}^{\,\beta_{h,i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                b (scalar): scale parameter of sector :math:`i`'s
                    Cobb-Douglas production function
            """
            return model.Z0[i] / prod(
                [model.F0[h, i] ** model.beta[h, i] for h in model.h])

        self.m.b = Param(self.m.i,
                         initialize=b_init,
                         doc='scale parameter in production function')

        # ------------------------------------------------------------------ #
        # ENDOGENOUS VARIABLES
        # Initialized at the known benchmark equilibrium (quantities from
        # the SAM, unit prices).
        # ------------------------------------------------------------------ #
        self.m.X = Var(self.m.i,
                       initialize=X0_init,
                       within=PositiveReals,
                       bounds=(SPLCGE_LOWER_BOUND, None),
                       doc='household consumption of the i-th good')

        self.m.F = Var(self.m.h, self.m.i,
                       initialize=F0_init,
                       within=PositiveReals,
                       bounds=(SPLCGE_LOWER_BOUND, None),
                       doc='the h-th factor input by the j-th firm')

        self.m.Z = Var(self.m.i,
                       initialize=Z0_init,
                       within=PositiveReals,
                       bounds=(SPLCGE_LOWER_BOUND, None),
                       doc='output of the j-th good')

        def p_init(model, v):
            r"""Unit price initializer: all prices equal one in the
            benchmark equilibrium.

            Args:
                model (AbstractModel): model under construction
                v (str): index element (good or factor)

            Returns:
                p (scalar): 1
            """
            return 1

        self.m.px = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(SPLCGE_LOWER_BOUND, None),
                        doc='demand price of the i-th good')

        self.m.pz = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(SPLCGE_LOWER_BOUND, None),
                        doc='supply price of the i-th good')

        self.m.pf = Var(self.m.h,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(SPLCGE_LOWER_BOUND, None),
                        doc='the h-th factor price')

        # ------------------------------------------------------------------ #
        # EQUILIBRIUM CONDITIONS
        # One rule per GAMS equation, same names as splcge.gms.
        # ------------------------------------------------------------------ #
        def eqX_rule(model, i):
            r"""Household demand (splcge.gms: ``eqX``): Cobb-Douglas
            demand out of factor income.

            .. math::
                X_{i} = \frac{\alpha_{i}}{p^{x}_{i}}
                        \sum_{h} p^{f}_{h}\, FF_{h}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): utility-maximizing consumption
                    of good :math:`i`
            """
            return (model.X[i] == model.alpha[i]
                    * sum(model.pf[h] * model.FF[h] / model.px[i]
                          for h in model.h))

        self.m.eqX = Constraint(self.m.i,
                                rule=eqX_rule,
                                doc='household demand function')

        def eqpz_rule(model, i):
            r"""Production function (splcge.gms: ``eqpz``).

            .. math::
                Z_{i} = b_{i} \prod_{h} F_{h,i}^{\,\beta_{h,i}}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): Cobb-Douglas production of
                    good :math:`i`
            """
            return (model.Z[i] == model.b[i] * prod(
                [model.F[h, i] ** model.beta[h, i] for h in model.h]))

        self.m.eqpz = Constraint(self.m.i,
                                 rule=eqpz_rule,
                                 doc='production function')

        def eqF_rule(model, h, i):
            r"""Factor demand from profit maximization
            (splcge.gms: ``eqF``).

            .. math::
                F_{h,i} = \frac{\beta_{h,i}\, p^{z}_{i}\, Z_{i}}
                               {p^{f}_{h}}

            Args:
                model (AbstractModel): concrete model instance
                h (str): element of factor set ``h``
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): Cobb-Douglas factor demand --
                    factor cost share equals :math:`\beta_{h,i}`
            """
            return (model.F[h, i]
                    == model.beta[h, i] * model.pz[i] * model.Z[i]
                    / model.pf[h])

        self.m.eqF = Constraint(self.m.h, self.m.i,
                                rule=eqF_rule,
                                doc='factor demand function')

        def eqpx_rule(model, i):
            r"""Goods market clearing (splcge.gms: ``eqpx``).

            .. math::
                X_{i} = Z_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): demand equals supply for good
                    :math:`i`
            """
            return (model.X[i] == model.Z[i])

        self.m.eqpx = Constraint(self.m.i,
                                 rule=eqpx_rule,
                                 doc='good market clearing condition')

        def eqpf_rule(model, h):
            r"""Factor market clearing (splcge.gms: ``eqpf``).

            .. math::
                \sum_{j} F_{h,j} = FF_{h}

            One instance of this constraint is redundant by Walras' law
            and must be dropped before solving with IPOPT -- see
            ``PyCGE.model_drop_redundant``.

            Args:
                model (AbstractModel): concrete model instance
                h (str): element of factor set ``h``

            Returns:
                (Constraint expression): full employment of factor
                    :math:`h`
            """
            return (sum(model.F[h, j] for j in model.i) == model.FF[h])

        self.m.eqpf = Constraint(self.m.h,
                                 rule=eqpf_rule,
                                 doc='factor market clearing condition')

        def eqZ_rule(model, i):
            r"""Price equation (splcge.gms: ``eqZ``): with no taxes or
            margins, the demand price equals the supply price.

            .. math::
                p^{x}_{i} = p^{z}_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): zero-margin price link
            """
            return (model.px[i] == model.pz[i])

        self.m.eqZ = Constraint(self.m.i,
                                rule=eqZ_rule,
                                doc='price equation')

        # ------------------------------------------------------------------ #
        # OBJECTIVE
        # ------------------------------------------------------------------ #
        def obj_rule(model):
            r"""Fictitious objective (splcge.gms: ``obj``): Cobb-Douglas
            utility. The demand equations ``eqX`` already embody utility
            maximization; the objective only gives the NLP solver a
            well-defined problem once the system is square.

            .. math::
                UU = \prod_{i} X_{i}^{\,\alpha_{i}}

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Objective expression): household utility
            """
            return prod([model.X[i] ** model.alpha[i] for i in model.i])

        self.m.obj = Objective(rule=obj_rule,
                               sense=maximize,
                               doc='utility function [fictitious]')

        logger.info("splcge model loaded")
        return self.m
