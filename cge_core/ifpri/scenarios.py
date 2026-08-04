# -*- coding: utf-8 -*-
"""Official IFPRI test-economy policy scenarios and macro closures.

This module builds the five counterfactuals recorded in the external GAMS
reference run without embedding or translating the official GAMS source.  The
Pyomo equations come from :mod:`cge_core.ifpri.model`; this layer changes only
exogenous data and closure choices.
"""
from __future__ import annotations

from dataclasses import replace
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping, Optional, Tuple, Union

from pyomo.environ import Constraint, Var

from .calibration import calibrate_ifpri_benchmark
from .model import build_ifpri_benchmark_model
from .schema import IfpriBenchmarkCalibration, IfpriDataset
from .solve import (
    IfpriSolveReport,
    apply_ifpri_base_closure,
    ifpri_degrees_of_freedom,
    perturb_ifpri_start,
    solve_ifpri_base,
)
from .validation import IfpriDataError


class IfpriScenario(str, Enum):
    """Named counterfactuals in the official IFPRI test simulation file."""

    TARCUT1 = "TARCUT1"
    TARCUT2 = "TARCUT2"
    FSAVINCR = "FSAVINCR"
    PWMINCR = "PWMINCR"
    DEVAL = "DEVAL"


IFPRI_POLICY_SCENARIOS: Tuple[IfpriScenario, ...] = tuple(IfpriScenario)

IFPRI_SCENARIO_DESCRIPTIONS: Mapping[IfpriScenario, str] = MappingProxyType({
    IfpriScenario.TARCUT1: "50% tariff cut; flexible government savings",
    IfpriScenario.TARCUT2: "50% tariff cut; fixed government savings and uniform direct-tax adjustment",
    IfpriScenario.FSAVINCR: "10% increase in foreign savings",
    IfpriScenario.PWMINCR: "10% increase in world import prices",
    IfpriScenario.DEVAL: "10% devaluation under a fixed-exchange-rate closure",
})

ScenarioLike = Union[IfpriScenario, str]


def normalize_ifpri_scenario(scenario: ScenarioLike) -> IfpriScenario:
    """Return a validated :class:`IfpriScenario` from a string or enum value."""
    if isinstance(scenario, IfpriScenario):
        return scenario
    try:
        return IfpriScenario(str(scenario).strip().upper())
    except ValueError as exc:
        allowed = ", ".join(item.value for item in IFPRI_POLICY_SCENARIOS)
        raise IfpriDataError(
            f"Unknown IFPRI scenario {scenario!r}; expected one of: {allowed}."
        ) from exc


def _scaled_mapping(values: Mapping, factor: float) -> Mapping:
    return MappingProxyType({key: float(item) * factor for key, item in values.items()})


def _shock_calibration(
    calibration: IfpriBenchmarkCalibration,
    scenario: IfpriScenario,
) -> IfpriBenchmarkCalibration:
    """Return calibration parameters with only the scenario's exogenous shock."""
    if scenario in {IfpriScenario.TARCUT1, IfpriScenario.TARCUT2}:
        taxes = replace(
            calibration.taxes,
            import_=_scaled_mapping(calibration.taxes.import_, 0.5),
        )
        return replace(calibration, taxes=taxes)

    if scenario is IfpriScenario.PWMINCR:
        prices = replace(
            calibration.prices,
            world_import=_scaled_mapping(calibration.prices.world_import, 1.1),
        )
        return replace(calibration, prices=prices)

    return calibration


def _add_direct_tax_adjustment(model) -> None:
    """Expose the official uniform direct-tax rate-point adjustment variable."""
    if not hasattr(model, "DTINS"):
        model.DTINS = Var(initialize=0.0)
    model.DTINS.fix(0.0)


def _apply_tier_two_government_closure(model) -> None:
    """Replace flexible government saving with a uniform direct-tax adjustment."""
    calibration = model._ifpri_base_calibration
    model.GSAV.fix(calibration.institutions.government_saving)
    model.direct_tax_definition.deactivate()
    if not hasattr(model, "adjusted_direct_tax_definition"):
        model.adjusted_direct_tax_definition = Constraint(
            model.INSDNG,
            rule=lambda m, i: m.TINS[i] == m.tinsbar[i] + m.DTINS,
        )
    model.DTINS.unfix()


def _apply_devaluation_closure(model) -> None:
    """Use DPI as numeraire and fix the shocked exchange rate."""
    calibration = model._ifpri_base_calibration
    model.CPI.unfix()
    model.FSAV.unfix()
    model.DPI.fix(calibration.system.domestic_price_index)
    model.EXR.fix(1.1 * calibration.prices.exchange_rate)


def apply_ifpri_scenario_closure(model, scenario: ScenarioLike) -> None:
    """Apply one official policy shock and closure to a benchmark model.

    The model must have been created by :func:`build_ifpri_scenario_model` so
    that tariff and import-price shocks are already embedded in its immutable
    Pyomo parameters.
    """
    selected = normalize_ifpri_scenario(scenario)
    calibration = model._ifpri_base_calibration

    _add_direct_tax_adjustment(model)
    apply_ifpri_base_closure(model)

    if selected is IfpriScenario.TARCUT2:
        _apply_tier_two_government_closure(model)
    elif selected is IfpriScenario.FSAVINCR:
        model.FSAV.set_value(1.1 * calibration.system.foreign_saving)
    elif selected is IfpriScenario.DEVAL:
        _apply_devaluation_closure(model)

    dof = ifpri_degrees_of_freedom(model)
    if dof != 0:
        raise IfpriDataError(
            f"IFPRI {selected.value} closure has {dof} degrees of freedom; expected 0."
        )
    object.__setattr__(model, "_ifpri_scenario", selected)


def build_ifpri_scenario_model(
    dataset: IfpriDataset,
    scenario: ScenarioLike,
    calibration: Optional[IfpriBenchmarkCalibration] = None,
):
    """Build one closed IFPRI policy simulation, initialized at the benchmark."""
    selected = normalize_ifpri_scenario(scenario)
    base = calibration or calibrate_ifpri_benchmark(dataset)
    shocked = _shock_calibration(base, selected)
    model = build_ifpri_benchmark_model(dataset, shocked)
    object.__setattr__(model, "_ifpri_base_calibration", base)
    apply_ifpri_scenario_closure(model, selected)
    return model


def solve_ifpri_scenario(
    model,
    solver: Optional[str] = None,
    tee: bool = False,
) -> IfpriSolveReport:
    """Solve a closed policy scenario with the same NLP formulation as BASE."""
    return solve_ifpri_base(model, solver=solver, tee=tee)


def build_and_solve_ifpri_scenarios(
    dataset: IfpriDataset,
    scenarios: Optional[Iterable[ScenarioLike]] = None,
    solver: Optional[str] = None,
    perturbation: Optional[float] = 1.01,
):
    """Build and solve multiple scenarios, returning models and solve reports."""
    selected = IFPRI_POLICY_SCENARIOS if scenarios is None else tuple(
        normalize_ifpri_scenario(item) for item in scenarios
    )
    results = {}
    calibration = calibrate_ifpri_benchmark(dataset)
    for scenario in selected:
        model = build_ifpri_scenario_model(dataset, scenario, calibration)
        if perturbation is not None:
            perturb_ifpri_start(model, perturbation)
        report = solve_ifpri_scenario(model, solver=solver)
        results[scenario] = (model, report)
    return results
