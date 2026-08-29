from types import ModuleType

import pytest
from pyomo.environ import ConcreteModel, Constraint, Param, Var

from cge_core.authoring.module_adapter import FunctionalEconomy, FunctionalEquilibrium
from cge_core.workflow import _Snapshot
from cge_core.compat.pycge import ComponentError


def _module(*, shockable_marker="absent", immutable=False):
    module = ModuleType("review_model")
    module.model_name = "ReviewModel"
    if shockable_marker != "absent":
        module.shockable = shockable_marker
    module.benchmark_only = set()

    def build_model(_data):
        model = ConcreteModel()
        model.p = Param(initialize=1.0, mutable=not immutable)
        model.x = Var(initialize=1.0)
        model.eq = Constraint(expr=model.x == model.p)
        return model

    def apply_default_closure(_model):
        pass

    module.build_model = build_model
    module.apply_default_closure = apply_default_closure
    return module


def _scenario(module):
    economy = FunctionalEconomy(module)
    model = module.build_model(None)
    module.apply_default_closure(model)
    snapshot = _Snapshot.from_instance(
        model_id=economy.name,
        label="benchmark",
        instance=model,
        results=None,
    )
    return FunctionalEquilibrium(economy, model, snapshot).scenario("test")


def test_explicit_empty_shockable_set_locks_model():
    scenario = _scenario(_module(shockable_marker=set()))
    with pytest.raises(ComponentError, match="not declared shockable"):
        scenario.set("p", None, 2.0)


def test_absent_shockable_declaration_keeps_open_authoring_mode():
    scenario = _scenario(_module())
    scenario.set("p", None, 2.0)
    assert float(scenario.model.p.value) == 2.0


def test_immutable_param_reports_author_facing_error():
    scenario = _scenario(_module(shockable_marker={"p"}, immutable=True))
    with pytest.raises(ComponentError, match="immutable"):
        scenario.set("p", None, 2.0)
