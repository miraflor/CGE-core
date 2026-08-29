"""Tiny no-inheritance equilibrium model for the CGE-Core authoring tutorial."""
from pyomo.environ import ConcreteModel, Constraint, Objective, Param, Set, Var

model_name = "TwoGoodFunctionalExample"
benchmark_only = set()
shockable = {"endowment"}


def build_model(data=None):
    m = ConcreteModel()
    m.goods = Set(initialize=["FOOD", "MFG"], ordered=True)
    m.alpha = Param(m.goods, initialize={"FOOD": 0.5, "MFG": 0.5})
    m.endowment = Param(
        m.goods,
        initialize={"FOOD": 60.0, "MFG": 40.0},
        mutable=True,
    )
    m.p = Var(m.goods, bounds=(1e-8, None), initialize=1.0)
    m.q = Var(m.goods, bounds=(0.0, None), initialize=50.0)

    def income(model):
        return sum(model.p[g] * model.endowment[g] for g in model.goods)

    m.demand_food = Constraint(
        expr=m.q["FOOD"] == m.alpha["FOOD"] * income(m) / m.p["FOOD"]
    )
    m.demand_mfg = Constraint(
        expr=m.q["MFG"] == m.alpha["MFG"] * income(m) / m.p["MFG"]
    )
    m.market_food = Constraint(expr=m.q["FOOD"] == m.endowment["FOOD"])
    m.market_mfg = Constraint(expr=m.q["MFG"] == m.endowment["MFG"])
    # A zero objective makes this documented authoring example an explicit
    # feasibility problem for NLP interfaces that expect an Objective.
    m.obj = Objective(expr=0.0)
    return m


def apply_default_closure(model):
    model.p["FOOD"].fix(1.0)
    model.market_food.deactivate()
