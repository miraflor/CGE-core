# -*- coding: utf-8 -*-
r"""
Standard CGE model definition (Hosoe, Gasawa & Hashimoto 2010, Ch. 5-6).
------------------------------------------------------------------------

Pyomo port of ``stdcge.gms`` (GAMS Model Library, SEQ=276): a static,
single-country, open-economy CGE model with

* Cobb-Douglas value added over primary factors,
* Leontief intermediate demand,
* Armington (CES) aggregation of imports and domestic goods,
* CET transformation between exports and domestic supply,
* a government sector (direct tax, production tax, import tariff), and
* saving-driven investment with exogenous foreign saving.

Sets in the bundled example data: goods ``i in {BRD, MLK}``, factors
``h in {CAP, LAB}``. The equation-by-equation crosswalk to the GAMS
source lives in ``docs/MODEL.md``; the crosswalk to OG-Core conventions
lives in ``docs/OG_CORE_CROSSWALK.md``.

Style note (for readers coming from OG-Core):
    This module plays the role that ``firms.py`` + ``household.py`` +
    ``tax.py`` + ``aggregates.py`` play in OG-Core (DeBacker & Evans,
    https://github.com/PSLmodels/OG-Core): it defines the model's
    algebra and nothing else. Docstrings follow OG-Core's convention of
    stating each relationship in a ``.. math::`` block with Args/Returns
    sections. Because this is a Pyomo *simultaneous system* rather than
    OG-Core's function-per-object design, each "function" here is either
    a calibration initializer (returns a number from the SAM benchmark)
    or a constraint rule (returns a Pyomo equality). Workflow -- data
    loading, closure, solving, comparison -- lives in
    ``cge_core/engine.py`` (the analogue of ``SS.py``/``execute.py``).

Notation:
    Variables carry Hosoe's names: ``Y`` composite factor (value added),
    ``F`` factor input, ``X`` intermediate input, ``Z`` gross output,
    ``Xp/Xg/Xv`` household/government/investment demand, ``E/M`` exports
    and imports, ``Q`` the Armington composite, ``D`` the domestic good,
    ``p*`` the corresponding prices, ``epsilon`` the exchange rate,
    ``Sp/Sg/Sf`` private/government/foreign saving, ``Td/Tz/Tm`` tax
    revenues. A trailing ``0`` (``Y0``, ``Q0``, ...) marks a benchmark
    (SAM-observed) magnitude used only for calibration, mirroring the
    GAMS ``.gms`` file's ``*0`` parameters.

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
    Pyomo ``prod``; tax-revenue variable domains ``PositiveReals`` ->
    ``NonNegativeReals``; removed unused numpy import; OG-Core-style
    documentation. The economics is unchanged; see CHANGELOG.md.
"""
import logging

from pyomo.environ import (
    AbstractModel,
    Constraint,
    NonNegativeReals,
    Objective,
    Param,
    PositiveReals,
    Set,
    Var,
    maximize,
    prod,
)

logger = logging.getLogger(__name__)

# Numerical guard reproduced from the reference implementation: keeps
# divisions and fractional powers away from zero during IPOPT iterations.
# See docs/MODEL.md, "Numerical lower bounds".
STDCGE_LOWER_BOUND = 1e-5

#: Default institutional account labels, as used in Hosoe's stdcge.gms
#: SAM. Pass an ``accounts`` mapping to :class:`StdModelDef` to relabel
#: any of them for a SAM that uses different names (e.g. a country SAM
#: with ``HH`` instead of ``HOH``). Keys: ``hoh`` household, ``gov``
#: government, ``inv`` investment/saving, ``ext`` external (rest of
#: world), ``idt`` indirect (production) tax, ``trf`` tariff.
STDCGE_ACCOUNTS = {
    'hoh': 'HOH',
    'gov': 'GOV',
    'inv': 'INV',
    'ext': 'EXT',
    'idt': 'IDT',
    'trf': 'TRF',
}


class StdModelDef:
    r"""Builder for the Hosoe standard CGE model as a Pyomo AbstractModel.

    The class exposes a single method, :meth:`model`, matching the
    ``model_def`` protocol expected by :class:`cge_core.engine.PyCGE`
    (analogous to how an OG-Core ``Specifications`` object is passed
    into ``SS.run_SS``). All sets, parameters, variables, constraints,
    and the objective are declared inside :meth:`model` so that a fresh
    AbstractModel is produced on every call.

    Args:
        accounts (dict, optional): overrides for the institutional
            account labels the equations read from the SAM; see
            :data:`STDCGE_ACCOUNTS`. Only the keys you want to relabel
            need to be supplied, e.g. ``{'hoh': 'HH'}``. Unknown keys
            raise ValueError. The goods and factor accounts come from
            the ``set-i-.csv`` / ``set-h-.csv`` files (or
            :func:`cge_core.samtools.build_dataset`), so they need no
            mapping.

    Notes:
        The Armington and CET elasticities are fixed at
        :math:`\sigma_i = \psi_i = 2`, exactly matching ``stdcge.gms``.
        They are not currently constructor inputs. A model adapted to a
        different SAM therefore retains these GAMS benchmark assumptions
        unless its model definition is edited explicitly.
    """

    # Only market-clearing equations are valid Walras-law closures. This
    # metadata lets the engine reject a mathematically square but economically
    # invalid model created by dropping an arbitrary behavioural equation.
    redundant_constraints = frozenset({'eqpf', 'eqpqd'})
    required_data_files = frozenset({
        'set-i-.csv', 'set-h-.csv', 'set-u-.csv', 'param-sam-.csv',
    })
    numeraire_variables = frozenset({
        'pf', 'py', 'pz', 'pq', 'pe', 'pm', 'pd', 'epsilon',
    })

    def __init__(self, accounts=None):
        merged = dict(STDCGE_ACCOUNTS)
        if accounts:
            unknown = sorted(set(accounts) - set(merged))
            if unknown:
                raise ValueError(
                    "Unknown account keys %s; valid keys are %s."
                    % (unknown, sorted(merged)))
            merged.update(accounts)
        if any(not isinstance(label, str) or not label.strip()
               for label in merged.values()):
            raise ValueError("Account labels must be non-empty strings.")
        merged = {key: label.strip() for key, label in merged.items()}
        if len(set(merged.values())) != len(merged):
            raise ValueError(
                "Institutional account labels must be distinct; one SAM "
                "account cannot fill multiple economic roles.")
        self.accounts = merged

    def model(self):
        r"""Declare and return the standard-model AbstractModel.

        Returns:
            m (pyomo.environ.AbstractModel): the abstract standard CGE
                model. Concrete data (sets and the SAM) are attached
                later by ``PyCGE.model_data`` / ``model_instance`` via a
                DataPortal, so this object carries structure only.
        """
        # Institutional account labels (configurable; see STDCGE_ACCOUNTS).
        HOH = self.accounts['hoh']
        GOV = self.accounts['gov']
        INV = self.accounts['inv']
        EXT = self.accounts['ext']
        IDT = self.accounts['idt']
        TRF = self.accounts['trf']

        # ------------------------------------------------------------------ #
        # MODEL OBJECT
        # ------------------------------------------------------------------ #
        self.m = AbstractModel()

        # ------------------------------------------------------------------ #
        # SETS
        # Populated from set-i-.csv, set-h-.csv, set-u-.csv at load time.
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
        # Each initializer reads one cell or margin of the SAM. These are
        # the observed base-year quantities the model is calibrated to
        # reproduce; they never appear in the equilibrium equations except
        # through the calibrated share/scale parameters below and through
        # variable initialization.
        # ------------------------------------------------------------------ #
        def Td0_init(model):
            r"""Benchmark direct-tax revenue.

            .. math::
                T^{d}_{0} = \mathrm{SAM}[\mathrm{GOV}, \mathrm{HOH}]

            Args:
                model (AbstractModel): model under construction

            Returns:
                Td0 (scalar): base-year direct tax paid by the household
            """
            return model.sam[GOV, HOH]

        self.m.Td0 = Param(initialize=Td0_init,
                           doc='benchmark direct tax', mutable=True)

        def Tz0_init(model, i):
            r"""Benchmark production-tax revenue on good :math:`i`.

            .. math::
                T^{z}_{0,i} = \mathrm{SAM}[\mathrm{IDT}, i]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Tz0 (scalar): base-year production (indirect) tax on
                    sector :math:`i`
            """
            return model.sam[IDT, i]

        self.m.Tz0 = Param(self.m.i, initialize=Tz0_init,
                           doc='benchmark production tax', mutable=True)

        def Tm0_init(model, i):
            r"""Benchmark import-tariff revenue on good :math:`i`.

            .. math::
                T^{m}_{0,i} = \mathrm{SAM}[\mathrm{TRF}, i]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Tm0 (scalar): base-year tariff revenue on good :math:`i`
            """
            return model.sam[TRF, i]

        self.m.Tm0 = Param(self.m.i, initialize=Tm0_init,
                           doc='benchmark import tariff', mutable=True)

        def F0_init(model, h, i):
            r"""Benchmark factor input (factor payments block of the SAM).

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

        self.m.F0 = Param(self.m.h, self.m.i, initialize=F0_init,
                          doc='benchmark factor input by the j-th firm',
                          mutable=True)

        def Y0_init(model, i):
            r"""Benchmark composite factor (value added) of sector :math:`i`.

            .. math::
                Y_{0,i} = \sum_{h} F_{0,h,i}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Y0 (scalar): base-year value added in sector :math:`i`
            """
            return sum(model.F0[h, i] for h in model.h)

        self.m.Y0 = Param(self.m.i, initialize=Y0_init,
                          doc='benchmark composite factor', mutable=True)

        def X0_init(model, i, j):
            r"""Benchmark intermediate input of good :math:`i` into sector
            :math:`j` (the interindustry block of the SAM).

            .. math::
                X_{0,i,j} = \mathrm{SAM}[i, j]

            Args:
                model (AbstractModel): model under construction
                i (str): supplying good, element of set ``i``
                j (str): using sector, element of set ``i``

            Returns:
                X0 (scalar): base-year intermediate flow :math:`i \to j`
            """
            return model.sam[i, j]

        self.m.X0 = Param(self.m.i, self.m.i, initialize=X0_init,
                          doc='benchmark intermediate input', mutable=True)

        def Z0_init(model, j):
            r"""Benchmark gross output of sector :math:`j`.

            .. math::
                Z_{0,j} = Y_{0,j} + \sum_{i} X_{0,i,j}

            Args:
                model (AbstractModel): model under construction
                j (str): element of goods set ``i``

            Returns:
                Z0 (scalar): base-year gross output of sector :math:`j`
            """
            return model.Y0[j] + sum(model.X0[i, j] for i in model.i)

        self.m.Z0 = Param(self.m.i, initialize=Z0_init,
                          doc='benchmark gross output of the j-th good',
                          mutable=True)

        def M0_init(model, i):
            r"""Benchmark imports of good :math:`i` (payments to the
            external account row).

            .. math::
                M_{0,i} = \mathrm{SAM}[\mathrm{EXT}, i]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                M0 (scalar): base-year imports of good :math:`i`
            """
            return model.sam[EXT, i]

        self.m.M0 = Param(self.m.i, initialize=M0_init,
                          doc='benchmark imports', mutable=True)

        def tauz_init(model, i):
            r"""Production-tax rate implied by the benchmark.

            .. math::
                \tau^{z}_{i} = \frac{T^{z}_{0,i}}{Z_{0,i}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                tauz (scalar): ad valorem production tax rate on
                    sector :math:`i`
            """
            return model.Tz0[i] / model.Z0[i]

        self.m.tauz = Param(self.m.i, initialize=tauz_init,
                            doc='production tax rate', mutable=True)

        def taum_init(model, i):
            r"""Import-tariff rate implied by the benchmark.

            .. math::
                \tau^{m}_{i} = \frac{T^{m}_{0,i}}{M_{0,i}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                taum (scalar): ad valorem tariff rate on good :math:`i`
            """
            return model.Tm0[i] / model.M0[i]

        self.m.taum = Param(self.m.i, initialize=taum_init,
                            doc='import tariff rate', mutable=True)

        def Xp0_init(model, i):
            r"""Benchmark household consumption of good :math:`i`.

            .. math::
                X^{p}_{0,i} = \mathrm{SAM}[i, \mathrm{HOH}]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Xp0 (scalar): base-year household purchase of good
                    :math:`i`
            """
            return model.sam[i, HOH]

        self.m.Xp0 = Param(self.m.i, initialize=Xp0_init,
                           doc='benchmark household consumption',
                           mutable=True)

        def FF_init(model, h):
            r"""Factor endowment of the household (exogenous supply).

            .. math::
                FF_{h} = \mathrm{SAM}[\mathrm{HOH}, h]

            Args:
                model (AbstractModel): model under construction
                h (str): element of factor set ``h``

            Returns:
                FF (scalar): endowment of factor :math:`h`; fixed over
                    the simulation (full-employment closure)
            """
            return model.sam[HOH, h]

        self.m.FF = Param(self.m.h, initialize=FF_init,
                          doc='factor endowment of the h-th factor',
                          mutable=True)

        def Xg0_init(model, i):
            r"""Benchmark government consumption of good :math:`i`.

            .. math::
                X^{g}_{0,i} = \mathrm{SAM}[i, \mathrm{GOV}]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Xg0 (scalar): base-year government purchase of good
                    :math:`i`
            """
            return model.sam[i, GOV]

        self.m.Xg0 = Param(self.m.i, initialize=Xg0_init,
                           doc='benchmark government consumption',
                           mutable=True)

        def Xv0_init(model, i):
            r"""Benchmark investment demand for good :math:`i`.

            .. math::
                X^{v}_{0,i} = \mathrm{SAM}[i, \mathrm{INV}]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Xv0 (scalar): base-year investment purchase of good
                    :math:`i`
            """
            return model.sam[i, INV]

        self.m.Xv0 = Param(self.m.i, initialize=Xv0_init,
                           doc='benchmark investment demand', mutable=True)

        def E0_init(model, i):
            r"""Benchmark exports of good :math:`i` (receipts from the
            external account column).

            .. math::
                E_{0,i} = \mathrm{SAM}[i, \mathrm{EXT}]

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                E0 (scalar): base-year exports of good :math:`i`
            """
            return model.sam[i, EXT]

        self.m.E0 = Param(self.m.i, initialize=E0_init,
                          doc='benchmark exports', mutable=True)

        def Q0_init(model, i):
            r"""Benchmark Armington composite supply of good :math:`i`
            (total absorption).

            .. math::
                Q_{0,i} = X^{p}_{0,i} + X^{g}_{0,i} + X^{v}_{0,i}
                          + \sum_{j} X_{0,i,j}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                Q0 (scalar): base-year composite-good quantity
            """
            return (model.Xp0[i] + model.Xg0[i] + model.Xv0[i]
                    + sum(model.X0[i, j] for j in model.i))

        self.m.Q0 = Param(self.m.i, initialize=Q0_init,
                          doc="benchmark Armington composite good",
                          mutable=True)

        def D0_init(model, i):
            r"""Benchmark domestic good (output sold at home), valued at
            the tax-inclusive producer price.

            .. math::
                D_{0,i} = (1 + \tau^{z}_{i})\, Z_{0,i} - E_{0,i}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                D0 (scalar): base-year domestic sales of good :math:`i`
            """
            return (1 + model.tauz[i]) * model.Z0[i] - model.E0[i]

        self.m.D0 = Param(self.m.i, initialize=D0_init,
                          doc='benchmark domestic good', mutable=True)

        def Sp0_init(model):
            r"""Benchmark private saving.

            .. math::
                S^{p}_{0} = \mathrm{SAM}[\mathrm{INV}, \mathrm{HOH}]

            Args:
                model (AbstractModel): model under construction

            Returns:
                Sp0 (scalar): base-year household saving
            """
            return model.sam[INV, HOH]

        self.m.Sp0 = Param(initialize=Sp0_init,
                           doc='benchmark private saving', mutable=True)

        def Sg0_init(model):
            r"""Benchmark government saving.

            .. math::
                S^{g}_{0} = \mathrm{SAM}[\mathrm{INV}, \mathrm{GOV}]

            Args:
                model (AbstractModel): model under construction

            Returns:
                Sg0 (scalar): base-year government saving (fiscal
                    surplus channelled to investment)
            """
            return model.sam[INV, GOV]

        self.m.Sg0 = Param(initialize=Sg0_init,
                           doc='benchmark government saving', mutable=True)

        def Sf_init(model):
            r"""Foreign saving in foreign-currency units (exogenous).

            .. math::
                S^{f} = \mathrm{SAM}[\mathrm{INV}, \mathrm{EXT}]

            Args:
                model (AbstractModel): model under construction

            Returns:
                Sf (scalar): current-account deficit financing
                    investment; held fixed across simulations
                    (savings-driven closure)
            """
            return model.sam[INV, EXT]

        self.m.Sf = Param(initialize=Sf_init,
                          doc='foreign saving in US dollars', mutable=True)

        def pWe_init(model, i):
            r"""World export price (small-country assumption).

            .. math::
                p^{We}_{i} = 1

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                pWe (scalar): exogenous world price of exports,
                    normalized to one in the benchmark
            """
            return 1

        self.m.pWe = Param(self.m.i, initialize=pWe_init,
                           doc='export price in US dollars', mutable=True)

        def pWm_init(model, i):
            r"""World import price (small-country assumption).

            .. math::
                p^{Wm}_{i} = 1

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                pWm (scalar): exogenous world price of imports,
                    normalized to one in the benchmark
            """
            return 1

        self.m.pWm = Param(self.m.i, initialize=pWm_init,
                           doc='import price in US dollars', mutable=True)

        # ------------------------------------------------------------------ #
        # CALIBRATED BEHAVIOURAL PARAMETERS
        # Elasticities are set by assumption (sigma = psi = 2, as in
        # stdcge.gms); every share and scale parameter is then recovered
        # so the model reproduces the SAM exactly at unit prices. This is
        # the CGE analogue of OG-Core's calibration step: parameters are
        # chosen so the baseline equilibrium matches the data by
        # construction.
        # ------------------------------------------------------------------ #
        def sigma_init(model, i):
            r"""Armington elasticity of substitution (assumed).

            .. math::
                \sigma_{i} = 2

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                sigma (scalar): elasticity of substitution between
                    imports and the domestic good
            """
            return 2

        self.m.sigma = Param(self.m.i, initialize=sigma_init,
                             doc='elasticity of substitution')

        def psi_init(model, i):
            r"""CET elasticity of transformation (assumed).

            .. math::
                \psi_{i} = 2

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                psi (scalar): elasticity of transformation between
                    exports and domestic sales
            """
            return 2

        self.m.psi = Param(self.m.i, initialize=psi_init,
                           doc='elasticity of transformation')

        def eta_init(model, i):
            r"""CES exponent implied by the Armington elasticity.

            .. math::
                \eta_{i} = \frac{\sigma_{i} - 1}{\sigma_{i}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                eta (scalar): substitution-elasticity parameter in the
                    Armington CES aggregator
            """
            return (model.sigma[i] - 1) / model.sigma[i]

        self.m.eta = Param(self.m.i, initialize=eta_init,
                           doc='substitution elasticity parameter')

        def phi_init(model, i):
            r"""CET exponent implied by the transformation elasticity.

            .. math::
                \phi_{i} = \frac{\psi_{i} + 1}{\psi_{i}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                phi (scalar): transformation-elasticity parameter in
                    the CET function
            """
            return (model.psi[i] + 1) / model.psi[i]

        self.m.phi = Param(self.m.i, initialize=phi_init,
                           doc='transformation elasticity parameter')

        def alpha_init(model, i):
            r"""Cobb-Douglas utility share of good :math:`i`.

            .. math::
                \alpha_{i} = \frac{X^{p}_{0,i}}{\sum_{j} X^{p}_{0,j}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                alpha (scalar): household expenditure share on good
                    :math:`i`; shares sum to one
            """
            return model.Xp0[i] / sum(model.Xp0[j] for j in model.i)

        self.m.alpha = Param(self.m.i, initialize=alpha_init,
                             doc='share parameter in utility func.')

        def beta_init(model, h, i):
            r"""Cobb-Douglas factor share in value added.

            .. math::
                \beta_{h,i} = \frac{F_{0,h,i}}{\sum_{k} F_{0,k,i}}

            Args:
                model (AbstractModel): model under construction
                h (str): element of factor set ``h``
                i (str): element of goods set ``i``

            Returns:
                beta (scalar): cost share of factor :math:`h` in sector
                    :math:`i`; shares sum to one within a sector
            """
            return model.F0[h, i] / sum(model.F0[k, i] for k in model.h)

        self.m.beta = Param(self.m.h, self.m.i, initialize=beta_init,
                            doc='share parameter in production func.')

        def b_init(model, i):
            r"""Scale (TFP) parameter of the value-added function,
            recovered so production reproduces the benchmark.

            .. math::
                b_{i} = \frac{Y_{0,i}}
                             {\prod_{h} F_{0,h,i}^{\,\beta_{h,i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                b (scalar): scale parameter of sector :math:`i`'s
                    Cobb-Douglas value-added function
            """
            return model.Y0[i] / prod(
                [model.F0[h, i] ** model.beta[h, i] for h in model.h])

        self.m.b = Param(self.m.i, initialize=b_init,
                         doc='scale parameter in production func.')

        def ax_init(model, i, j):
            r"""Leontief intermediate input coefficient.

            .. math::
                ax_{i,j} = \frac{X_{0,i,j}}{Z_{0,j}}

            Args:
                model (AbstractModel): model under construction
                i (str): supplying good, element of set ``i``
                j (str): using sector, element of set ``i``

            Returns:
                ax (scalar): units of good :math:`i` required per unit
                    of gross output of sector :math:`j`
            """
            return model.X0[i, j] / model.Z0[j]

        self.m.ax = Param(self.m.i, self.m.i, initialize=ax_init,
                          doc='intermediate input requirement coeff.')

        def ay_init(model, i):
            r"""Leontief composite-factor (value-added) coefficient.

            .. math::
                ay_{i} = \frac{Y_{0,i}}{Z_{0,i}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                ay (scalar): units of composite factor per unit of
                    gross output in sector :math:`i`
            """
            return model.Y0[i] / model.Z0[i]

        self.m.ay = Param(self.m.i, initialize=ay_init,
                          doc='composite fact. input req. coeff.')

        def mu_init(model, i):
            r"""Government expenditure share of good :math:`i`.

            .. math::
                \mu_{i} = \frac{X^{g}_{0,i}}{\sum_{j} X^{g}_{0,j}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                mu (scalar): share of government spending on good
                    :math:`i`; shares sum to one
            """
            return model.Xg0[i] / sum(model.Xg0[j] for j in model.i)

        self.m.mu = Param(self.m.i, initialize=mu_init,
                          doc='government consumption share')

        def lambd_init(model, i):
            r"""Investment expenditure share of good :math:`i`
            (``lambd`` because ``lambda`` is a Python keyword).

            .. math::
                \lambda_{i} = \frac{X^{v}_{0,i}}
                                   {S^{p}_{0} + S^{g}_{0} + S^{f}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                lambd (scalar): share of total saving spent on
                    investment good :math:`i`
            """
            return model.Xv0[i] / (model.Sp0 + model.Sg0 + model.Sf)

        self.m.lambd = Param(self.m.i, initialize=lambd_init,
                             doc='investment demand share')

        def deltam_init(model, i):
            r"""Armington share parameter on imports, recovered from the
            benchmark first-order conditions at tariff-inclusive prices.

            .. math::
                \delta^{m}_{i} =
                    \frac{(1+\tau^{m}_{i})\, M_{0,i}^{\,1-\eta_{i}}}
                         {(1+\tau^{m}_{i})\, M_{0,i}^{\,1-\eta_{i}}
                          + D_{0,i}^{\,1-\eta_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                deltam (scalar): import share parameter in the
                    Armington CES function
            """
            return ((1 + model.taum[i]) * model.M0[i] ** (1 - model.eta[i])
                    / ((1 + model.taum[i]) * model.M0[i] ** (1 - model.eta[i])
                       + model.D0[i] ** (1 - model.eta[i])))

        self.m.deltam = Param(self.m.i, initialize=deltam_init,
                              doc='share par. in Armington func.')

        def deltad_init(model, i):
            r"""Armington share parameter on the domestic good.

            .. math::
                \delta^{d}_{i} =
                    \frac{D_{0,i}^{\,1-\eta_{i}}}
                         {(1+\tau^{m}_{i})\, M_{0,i}^{\,1-\eta_{i}}
                          + D_{0,i}^{\,1-\eta_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                deltad (scalar): domestic share parameter in the
                    Armington CES function
            """
            return (model.D0[i] ** (1 - model.eta[i])
                    / ((1 + model.taum[i]) * model.M0[i] ** (1 - model.eta[i])
                       + model.D0[i] ** (1 - model.eta[i])))

        self.m.deltad = Param(self.m.i, initialize=deltad_init,
                              doc='share par. in Armington func.')

        def gamma_init(model, i):
            r"""Armington scale parameter, recovered so the CES
            aggregator reproduces benchmark absorption.

            .. math::
                \gamma_{i} = \frac{Q_{0,i}}
                    {\left[\delta^{m}_{i} M_{0,i}^{\,\eta_{i}}
                     + \delta^{d}_{i} D_{0,i}^{\,\eta_{i}}
                     \right]^{1/\eta_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                gamma (scalar): scale parameter of the Armington
                    function for good :math:`i`
            """
            return model.Q0[i] / (
                model.deltam[i] * model.M0[i] ** model.eta[i]
                + model.deltad[i] * model.D0[i] ** model.eta[i]
            ) ** (1 / model.eta[i])

        self.m.gamma = Param(self.m.i, initialize=gamma_init,
                             doc='scale par. in Armington func.')

        def xie_init(model, i):
            r"""CET share parameter on exports.

            .. math::
                \xi^{e}_{i} =
                    \frac{E_{0,i}^{\,1-\phi_{i}}}
                         {E_{0,i}^{\,1-\phi_{i}} + D_{0,i}^{\,1-\phi_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                xie (scalar): export share parameter in the CET
                    transformation function
            """
            return (model.E0[i] ** (1 - model.phi[i])
                    / (model.E0[i] ** (1 - model.phi[i])
                       + model.D0[i] ** (1 - model.phi[i])))

        self.m.xie = Param(self.m.i, initialize=xie_init,
                           doc='share par. in transformation func.')

        def xid_init(model, i):
            r"""CET share parameter on domestic sales.

            .. math::
                \xi^{d}_{i} =
                    \frac{D_{0,i}^{\,1-\phi_{i}}}
                         {E_{0,i}^{\,1-\phi_{i}} + D_{0,i}^{\,1-\phi_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                xid (scalar): domestic share parameter in the CET
                    transformation function
            """
            return (model.D0[i] ** (1 - model.phi[i])
                    / (model.E0[i] ** (1 - model.phi[i])
                       + model.D0[i] ** (1 - model.phi[i])))

        self.m.xid = Param(self.m.i, initialize=xid_init,
                           doc='share par. in transformation func.')

        def theta_init(model, i):
            r"""CET scale parameter, recovered so transformation
            reproduces benchmark gross output.

            .. math::
                \theta_{i} = \frac{Z_{0,i}}
                    {\left[\xi^{e}_{i} E_{0,i}^{\,\phi_{i}}
                     + \xi^{d}_{i} D_{0,i}^{\,\phi_{i}}
                     \right]^{1/\phi_{i}}}

            Args:
                model (AbstractModel): model under construction
                i (str): element of goods set ``i``

            Returns:
                theta (scalar): scale parameter of the CET function for
                    sector :math:`i`
            """
            return model.Z0[i] / (
                model.xie[i] * model.E0[i] ** model.phi[i]
                + model.xid[i] * model.D0[i] ** model.phi[i]
            ) ** (1 / model.phi[i])

        self.m.theta = Param(self.m.i, initialize=theta_init,
                             doc='scale par. in transformation func.')

        def ssp_init(model):
            r"""Average propensity to save out of factor income
            (household).

            .. math::
                ss^{p} = \frac{S^{p}_{0}}{\sum_{h} FF_{h}}

            Args:
                model (AbstractModel): model under construction

            Returns:
                ssp (scalar): private average saving rate
            """
            return model.Sp0 / sum(model.FF[h] for h in model.h)

        self.m.ssp = Param(initialize=ssp_init,
                           doc='average propensity for private saving')

        def ssg_init(model):
            r"""Average propensity to save out of tax revenue
            (government).

            .. math::
                ss^{g} = \frac{S^{g}_{0}}
                              {T^{d}_{0} + \sum_{i} T^{z}_{0,i}
                               + \sum_{i} T^{m}_{0,i}}

            Args:
                model (AbstractModel): model under construction

            Returns:
                ssg (scalar): government average saving rate
            """
            return model.Sg0 / (model.Td0
                                + sum(model.Tz0[i] for i in model.i)
                                + sum(model.Tm0[i] for i in model.i))

        self.m.ssg = Param(initialize=ssg_init,
                           doc='average propensity for gov. saving')

        def taud_init(model):
            r"""Direct-tax rate on factor income.

            .. math::
                \tau^{d} = \frac{T^{d}_{0}}{\sum_{h} FF_{h}}

            Args:
                model (AbstractModel): model under construction

            Returns:
                taud (scalar): flat direct tax rate applied to
                    household factor income
            """
            return model.Td0 / sum(model.FF[h] for h in model.h)

        self.m.taud = Param(initialize=taud_init,
                            doc='direct tax rate')

        # ------------------------------------------------------------------ #
        # ENDOGENOUS VARIABLES
        # Initialized at benchmark quantities and unit prices -- the known
        # base equilibrium -- so IPOPT starts at (or near) the solution.
        # Lower bounds keep the CES/CET power terms and denominators away
        # from zero; see docs/MODEL.md.
        # ------------------------------------------------------------------ #
        self.m.Y = Var(self.m.i,
                       initialize=Y0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='composite factor')

        self.m.F = Var(self.m.h, self.m.i,
                       initialize=F0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='the h-th factor input by the j-th firm')

        self.m.X = Var(self.m.i, self.m.i,
                       initialize=X0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='intermediate input')

        self.m.Z = Var(self.m.i,
                       initialize=Z0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='output of the j-th good')

        self.m.Xp = Var(self.m.i,
                        initialize=Xp0_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='household consumption of the i-th good')

        self.m.Xg = Var(self.m.i,
                        initialize=Xg0_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='government consumption')

        self.m.Xv = Var(self.m.i,
                        initialize=Xv0_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='investment demand')

        self.m.E = Var(self.m.i,
                       initialize=E0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='exports')

        self.m.M = Var(self.m.i,
                       initialize=M0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='imports')

        self.m.Q = Var(self.m.i,
                       initialize=Q0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc="Armington's composite good")

        self.m.D = Var(self.m.i,
                       initialize=D0_init,
                       within=PositiveReals,
                       bounds=(STDCGE_LOWER_BOUND, None),
                       doc='domestic good')

        def p_init(model, v):
            r"""Unit price initializer: all prices equal one in the
            benchmark equilibrium (Hosoe's price normalization).

            Args:
                model (AbstractModel): model under construction
                v (str): index element (good or factor)

            Returns:
                p (scalar): 1
            """
            return 1

        self.m.pf = Var(self.m.h,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='the h-th factor price')

        self.m.py = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='composite factor price')

        self.m.pz = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='supply price of the i-th good')

        self.m.pq = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc="Armington's composite good price")

        self.m.pe = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='export price in local currency')

        self.m.pm = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='import price in local currency')

        self.m.pd = Var(self.m.i,
                        initialize=p_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='the i-th domestic good price')

        self.m.epsilon = Var(initialize=1,
                             within=PositiveReals,
                             bounds=(STDCGE_LOWER_BOUND, None),
                             doc='exchange rate')

        self.m.Sp = Var(initialize=Sp0_init,
                        within=PositiveReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='private saving')

        self.m.Sg = Var(initialize=Sg0_init,
                        within=NonNegativeReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='government saving')

        self.m.Td = Var(initialize=Td0_init,
                        within=NonNegativeReals,
                        bounds=(STDCGE_LOWER_BOUND, None),
                        doc='direct tax')

        # Tz and Tm may be driven exactly to zero by tax-abolition
        # experiments, so they carry no positive lower bound.
        self.m.Tz = Var(self.m.i,
                        initialize=Tz0_init,
                        within=NonNegativeReals,
                        doc='production tax')

        self.m.Tm = Var(self.m.i,
                        initialize=Tm0_init,
                        within=NonNegativeReals,
                        doc='import tariff')

        # ------------------------------------------------------------------ #
        # EQUILIBRIUM CONDITIONS
        # One rule per GAMS equation, same names as stdcge.gms. Grouped as
        # in docs/MODEL.md: production/factors, taxes, final demand and
        # saving, trade, market clearing.
        # ------------------------------------------------------------------ #

        # -- Production and factors ---------------------------------------- #
        def eqpy_rule(model, i):
            r"""Composite-factor (value-added) production function
            (stdcge.gms: ``eqpy``; Hosoe Ch. 5, firm behaviour).

            .. math::
                Y_{i} = b_{i} \prod_{h} F_{h,i}^{\,\beta_{h,i}}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): Cobb-Douglas aggregation of
                    primary factors into value added
            """
            return (model.Y[i] == model.b[i] * prod(
                [model.F[h, i] ** model.beta[h, i] for h in model.h]))

        self.m.eqpy = Constraint(self.m.i, rule=eqpy_rule,
                                 doc='composite factor agg. func.')

        def eqF_rule(model, h, i):
            r"""Factor demand from cost minimization
            (stdcge.gms: ``eqF``).

            .. math::
                F_{h,i} = \frac{\beta_{h,i}\, p^{y}_{i}\, Y_{i}}{p^{f}_{h}}

            Args:
                model (AbstractModel): concrete model instance
                h (str): element of factor set ``h``
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): Cobb-Douglas conditional factor
                    demand -- factor cost share equals :math:`\beta_{h,i}`
            """
            return (model.F[h, i]
                    == model.beta[h, i] * model.py[i] * model.Y[i]
                    / model.pf[h])

        self.m.eqF = Constraint(self.m.h, self.m.i, rule=eqF_rule,
                                doc='factor demand function')

        def eqX_rule(model, i, j):
            r"""Leontief intermediate demand (stdcge.gms: ``eqX``).

            .. math::
                X_{i,j} = ax_{i,j}\, Z_{j}

            Args:
                model (AbstractModel): concrete model instance
                i (str): supplying good, element of set ``i``
                j (str): using sector, element of set ``i``

            Returns:
                (Constraint expression): fixed-coefficient intermediate
                    input requirement
            """
            return (model.X[i, j] == model.ax[i, j] * model.Z[j])

        self.m.eqX = Constraint(self.m.i, self.m.i, rule=eqX_rule,
                                doc='intermediate demand function')

        def eqY_rule(model, i):
            r"""Leontief composite-factor demand (stdcge.gms: ``eqY``).

            .. math::
                Y_{i} = ay_{i}\, Z_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): fixed-coefficient value-added
                    requirement per unit of gross output
            """
            return (model.Y[i] == model.ay[i] * model.Z[i])

        self.m.eqY = Constraint(self.m.i, rule=eqY_rule,
                                doc='composite factor demand function')

        def eqpzs_rule(model, j):
            r"""Zero-profit / unit-cost pricing of gross output
            (stdcge.gms: ``eqpzs``).

            .. math::
                p^{z}_{j} = ay_{j}\, p^{y}_{j}
                            + \sum_{i} ax_{i,j}\, p^{q}_{i}

            Args:
                model (AbstractModel): concrete model instance
                j (str): element of goods set ``i``

            Returns:
                (Constraint expression): supply price equals unit cost
                    of value added plus intermediates
            """
            return (model.pz[j] == model.ay[j] * model.py[j]
                    + sum(model.ax[i, j] * model.pq[i] for i in model.i))

        self.m.eqpzs = Constraint(self.m.i, rule=eqpzs_rule,
                                  doc='unit cost function')

        # -- Government: tax revenues -------------------------------------- #
        def eqTd_rule(model):
            r"""Direct tax revenue (stdcge.gms: ``eqTd``).

            .. math::
                T^{d} = \tau^{d} \sum_{h} p^{f}_{h}\, FF_{h}

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Constraint expression): flat tax on household factor
                    income
            """
            return (model.Td == model.taud
                    * sum(model.pf[h] * model.FF[h] for h in model.h))

        self.m.eqTd = Constraint(rule=eqTd_rule,
                                 doc='direct tax revenue function')

        def eqTz_rule(model, i):
            r"""Production tax revenue (stdcge.gms: ``eqTz``).

            .. math::
                T^{z}_{i} = \tau^{z}_{i}\, p^{z}_{i}\, Z_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): ad valorem tax on the value of
                    gross output
            """
            return (model.Tz[i] == model.tauz[i] * model.pz[i] * model.Z[i])

        self.m.eqTz = Constraint(self.m.i, rule=eqTz_rule,
                                 doc='production tax revenue function')

        def eqTm_rule(model, i):
            r"""Import tariff revenue (stdcge.gms: ``eqTm``).

            .. math::
                T^{m}_{i} = \tau^{m}_{i}\, p^{m}_{i}\, M_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): ad valorem tariff on the local-
                    currency value of imports
            """
            return (model.Tm[i] == model.taum[i] * model.pm[i] * model.M[i])

        self.m.eqTm = Constraint(self.m.i, rule=eqTm_rule,
                                 doc='import tariff revenue function')

        # -- Final demand and saving --------------------------------------- #
        def eqXg_rule(model, i):
            r"""Government demand (stdcge.gms: ``eqXg``): tax revenue net
            of government saving is spent in fixed shares.

            .. math::
                X^{g}_{i} = \frac{\mu_{i}}{p^{q}_{i}}
                    \left(T^{d} + \sum_{j} T^{z}_{j}
                          + \sum_{j} T^{m}_{j} - S^{g}\right)

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): Cobb-Douglas government demand
                    out of disposable revenue
            """
            return (model.Xg[i] == model.mu[i]
                    * (model.Td
                       + sum(model.Tz[j] for j in model.i)
                       + sum(model.Tm[j] for j in model.i)
                       - model.Sg)
                    / model.pq[i])

        self.m.eqXg = Constraint(self.m.i, rule=eqXg_rule,
                                 doc='government demand function')

        def eqXv_rule(model, i):
            r"""Investment demand (stdcge.gms: ``eqXv``): total saving is
            spent on investment goods in fixed shares
            (savings-driven closure).

            .. math::
                X^{v}_{i} = \frac{\lambda_{i}}{p^{q}_{i}}
                    \left(S^{p} + S^{g} + \varepsilon S^{f}\right)

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): investment demand financed by
                    private, government, and foreign saving
            """
            return (model.Xv[i] == model.lambd[i]
                    * (model.Sp + model.Sg + model.epsilon * model.Sf)
                    / model.pq[i])

        self.m.eqXv = Constraint(self.m.i, rule=eqXv_rule,
                                 doc='investment demand function')

        def eqSp_rule(model):
            r"""Private saving (stdcge.gms: ``eqSp``).

            .. math::
                S^{p} = ss^{p} \sum_{h} p^{f}_{h}\, FF_{h}

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Constraint expression): fixed average saving rate out
                    of factor income
            """
            return (model.Sp == model.ssp
                    * sum(model.pf[h] * model.FF[h] for h in model.h))

        self.m.eqSp = Constraint(rule=eqSp_rule,
                                 doc='private saving function')

        def eqSg_rule(model):
            r"""Government saving (stdcge.gms: ``eqSg``).

            .. math::
                S^{g} = ss^{g} \left(T^{d} + \sum_{j} T^{z}_{j}
                        + \sum_{j} T^{m}_{j}\right)

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Constraint expression): fixed average saving rate out
                    of total tax revenue
            """
            return (model.Sg == model.ssg
                    * (model.Td
                       + sum(model.Tz[j] for j in model.i)
                       + sum(model.Tm[j] for j in model.i)))

        self.m.eqSg = Constraint(rule=eqSg_rule,
                                 doc='government saving function')

        def eqXp_rule(model, i):
            r"""Household demand (stdcge.gms: ``eqXp``): Cobb-Douglas
            demand out of disposable income.

            .. math::
                X^{p}_{i} = \frac{\alpha_{i}}{p^{q}_{i}}
                    \left(\sum_{h} p^{f}_{h}\, FF_{h}
                          - S^{p} - T^{d}\right)

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): utility-maximizing consumption
                    of good :math:`i` given income net of saving and
                    direct tax
            """
            return (model.Xp[i] == model.alpha[i]
                    * (sum(model.pf[h] * model.FF[h] for h in model.h)
                       - model.Sp - model.Td)
                    / model.pq[i])

        self.m.eqXp = Constraint(self.m.i, rule=eqXp_rule,
                                 doc='household demand function')

        # -- Trade: prices, balance of payments, Armington, CET ------------ #
        def eqpe_rule(model, i):
            r"""Export price link (stdcge.gms: ``eqpe``): local-currency
            export price is the world price times the exchange rate.

            .. math::
                p^{e}_{i} = \varepsilon\, p^{We}_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): small-country export price
                    equation
            """
            return (model.pe[i] == (model.epsilon * model.pWe[i]))

        self.m.eqpe = Constraint(self.m.i, rule=eqpe_rule,
                                 doc='world export price equation')

        def eqpm_rule(model, i):
            r"""Import price link (stdcge.gms: ``eqpm``).

            .. math::
                p^{m}_{i} = \varepsilon\, p^{Wm}_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): small-country import price
                    equation
            """
            return (model.pm[i] == model.epsilon * model.pWm[i])

        self.m.eqpm = Constraint(self.m.i, rule=eqpm_rule,
                                 doc='world import price equation')

        def eqepsilon_rule(model):
            r"""Balance of payments (stdcge.gms: ``eqepsilon``): export
            receipts plus foreign saving finance imports, in world
            prices.

            .. math::
                \sum_{i} p^{We}_{i} E_{i} + S^{f}
                    = \sum_{i} p^{Wm}_{i} M_{i}

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Constraint expression): external closure determining
                    the exchange rate :math:`\varepsilon`
            """
            return (sum(model.pWe[i] * model.E[i] for i in model.i)
                    + model.Sf
                    == sum(model.pWm[i] * model.M[i] for i in model.i))

        self.m.eqepsilon = Constraint(rule=eqepsilon_rule,
                                      doc='balance of payments')

        def eqpqs_rule(model, i):
            r"""Armington aggregation (stdcge.gms: ``eqpqs``): the
            composite good is a CES aggregate of imports and the
            domestic good.

            .. math::
                Q_{i} = \gamma_{i}\left[
                    \delta^{m}_{i} M_{i}^{\,\eta_{i}}
                    + \delta^{d}_{i} D_{i}^{\,\eta_{i}}
                    \right]^{1/\eta_{i}}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CES composite-supply function
            """
            return (model.Q[i] == model.gamma[i]
                    * (model.deltam[i] * model.M[i] ** model.eta[i]
                       + model.deltad[i] * model.D[i] ** model.eta[i])
                    ** (1 / model.eta[i]))

        self.m.eqpqs = Constraint(self.m.i, rule=eqpqs_rule,
                                  doc='Armington function')

        def eqM_rule(model, i):
            r"""Import demand (stdcge.gms: ``eqM``): first-order
            condition of composite-cost minimization at the
            tariff-inclusive import price.

            .. math::
                M_{i} = \left[
                    \frac{\gamma_{i}^{\,\eta_{i}} \delta^{m}_{i}
                          p^{q}_{i}}
                         {(1+\tau^{m}_{i})\, p^{m}_{i}}
                    \right]^{1/(1-\eta_{i})} Q_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CES import demand
            """
            return (model.M[i]
                    == (model.gamma[i] ** model.eta[i] * model.deltam[i]
                        * model.pq[i]
                        / ((1 + model.taum[i]) * model.pm[i]))
                    ** (1 / (1 - model.eta[i])) * model.Q[i])

        self.m.eqM = Constraint(self.m.i, rule=eqM_rule,
                                doc='import demand function')

        def eqD_rule(model, i):
            r"""Domestic-good demand (stdcge.gms: ``eqD``): the other
            first-order condition of composite-cost minimization.

            .. math::
                D_{i} = \left[
                    \frac{\gamma_{i}^{\,\eta_{i}} \delta^{d}_{i}
                          p^{q}_{i}}{p^{d}_{i}}
                    \right]^{1/(1-\eta_{i})} Q_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CES demand for the domestic
                    good
            """
            return (model.D[i]
                    == (model.gamma[i] ** model.eta[i] * model.deltad[i]
                        * model.pq[i] / model.pd[i])
                    ** (1 / (1 - model.eta[i])) * model.Q[i])

        self.m.eqD = Constraint(self.m.i, rule=eqD_rule,
                                doc='domestic good demand function')

        def eqpzd_rule(model, i):
            r"""CET transformation (stdcge.gms: ``eqpzd``): gross output
            is transformed into exports and domestic sales.

            .. math::
                Z_{i} = \theta_{i}\left[
                    \xi^{e}_{i} E_{i}^{\,\phi_{i}}
                    + \xi^{d}_{i} D_{i}^{\,\phi_{i}}
                    \right]^{1/\phi_{i}}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CET output-transformation
                    frontier
            """
            return (model.Z[i] == model.theta[i]
                    * (model.xie[i] * model.E[i] ** model.phi[i]
                       + model.xid[i] * model.D[i] ** model.phi[i])
                    ** (1 / model.phi[i]))

        self.m.eqpzd = Constraint(self.m.i, rule=eqpzd_rule,
                                  doc='transformation function')

        def eqE_rule(model, i):
            r"""Export supply (stdcge.gms: ``eqE``): first-order
            condition of revenue maximization on the CET frontier, at
            the tax-inclusive supply price.

            .. math::
                E_{i} = \left[
                    \frac{\theta_{i}^{\,\phi_{i}} \xi^{e}_{i}
                          (1+\tau^{z}_{i})\, p^{z}_{i}}{p^{e}_{i}}
                    \right]^{1/(1-\phi_{i})} Z_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CET export supply
            """
            return (model.E[i]
                    == (model.theta[i] ** model.phi[i] * model.xie[i]
                        * (1 + model.tauz[i]) * model.pz[i] / model.pe[i])
                    ** (1 / (1 - model.phi[i])) * model.Z[i])

        self.m.eqE = Constraint(self.m.i, rule=eqE_rule,
                                doc='export supply function')

        def eqDs_rule(model, i):
            r"""Domestic supply (stdcge.gms: ``eqDs``): the other
            first-order condition on the CET frontier.

            .. math::
                D_{i} = \left[
                    \frac{\theta_{i}^{\,\phi_{i}} \xi^{d}_{i}
                          (1+\tau^{z}_{i})\, p^{z}_{i}}{p^{d}_{i}}
                    \right]^{1/(1-\phi_{i})} Z_{i}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): CET domestic supply
            """
            return (model.D[i]
                    == (model.theta[i] ** model.phi[i] * model.xid[i]
                        * (1 + model.tauz[i]) * model.pz[i] / model.pd[i])
                    ** (1 / (1 - model.phi[i])) * model.Z[i])

        self.m.eqDs = Constraint(self.m.i, rule=eqDs_rule,
                                 doc='domestic good supply function')

        # -- Market clearing ------------------------------------------------ #
        def eqpqd_rule(model, i):
            r"""Composite-good market clearing (stdcge.gms: ``eqpqd``).

            .. math::
                Q_{i} = X^{p}_{i} + X^{g}_{i} + X^{v}_{i}
                        + \sum_{j} X_{i,j}

            Args:
                model (AbstractModel): concrete model instance
                i (str): element of goods set ``i``

            Returns:
                (Constraint expression): absorption of the composite
                    good by households, government, investment, and
                    intermediate use
            """
            return (model.Q[i] == model.Xp[i] + model.Xg[i] + model.Xv[i]
                    + sum(model.X[i, j] for j in model.i))

        self.m.eqpqd = Constraint(self.m.i, rule=eqpqd_rule,
                                  doc='market clearing cond. for comp. good')

        def eqpf_rule(model, h):
            r"""Factor market clearing (stdcge.gms: ``eqpf``).

            .. math::
                \sum_{i} F_{h,i} = FF_{h}

            One instance of this constraint is redundant by Walras' law
            and must be dropped before solving with IPOPT -- see
            ``PyCGE.model_drop_redundant`` and docs/MODEL.md, "Closure
            and degrees of freedom".

            Args:
                model (AbstractModel): concrete model instance
                h (str): element of factor set ``h``

            Returns:
                (Constraint expression): full employment of factor
                    :math:`h`
            """
            return (sum(model.F[h, i] for i in model.i) == model.FF[h])

        self.m.eqpf = Constraint(self.m.h, rule=eqpf_rule,
                                 doc='factor market clearing condition')

        # ------------------------------------------------------------------ #
        # OBJECTIVE
        # ------------------------------------------------------------------ #
        def obj_rule(model):
            r"""Fictitious objective (stdcge.gms: ``obj``): Cobb-Douglas
            utility over household consumption.

            .. math::
                UU = \prod_{i} \left(X^{p}_{i}\right)^{\alpha_{i}}

            The household demand equations ``eqXp`` already embody
            utility maximization, so the equilibrium is pinned down by
            the constraint system alone; the objective merely gives the
            NLP solver a well-defined problem once the system is square.
            Its value at the solution *is* the utility level used for
            welfare (EV) calculations.

            Args:
                model (AbstractModel): concrete model instance

            Returns:
                (Objective expression): household utility
            """
            return prod([model.Xp[i] ** model.alpha[i] for i in model.i])

        self.m.obj = Objective(rule=obj_rule, sense=maximize,
                               doc='utility function [fictitious]')

        logger.info("stdcge model loaded")
        return self.m
