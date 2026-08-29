from cge_core.spec import compile_document, parse_text, validate_document

MODEL = r'''# Human explanation A

```cge
set goods = [FOOD, MFG]
param alpha[FOOD] = 0.5
param alpha[MFG] = 0.5
param endowment[FOOD] = 60
param endowment[MFG] = 40
var p[i in goods] > 0
var q[i in goods] >= 0
equation demand_food:
    q[FOOD] = alpha[FOOD] * (p[FOOD]*endowment[FOOD] + p[MFG]*endowment[MFG]) / p[FOOD]
equation demand_mfg:
    q[MFG] = alpha[MFG] * (p[FOOD]*endowment[FOOD] + p[MFG]*endowment[MFG]) / p[MFG]
equation market_food:
    q[FOOD] = endowment[FOOD]
equation market_mfg:
    q[MFG] = endowment[MFG]
fix p[FOOD] = 1
drop market_food
shockable endowment
```
'''


def test_prose_is_inert():
    a = validate_document(parse_text(MODEL, path="a.cge.md"))
    b = validate_document(parse_text(MODEL.replace("Human explanation A", "Completely different prose"), path="b.cge.md"))
    assert a.executable_blocks == b.executable_blocks
    assert [(x.name, x.lhs, x.rhs) for x in a.equations] == [
        (x.name, x.lhs, x.rhs) for x in b.equations
    ]


def test_reference_spec_compiles_to_square_model():
    from pyomo.environ import Constraint, Var
    doc = validate_document(parse_text(MODEL, path="example.cge.md"))
    model = compile_document(doc)
    free = sum(1 for x in model.component_data_objects(Var, active=True) if not x.fixed)
    equations = sum(
        1 for x in model.component_data_objects(Constraint, active=True) if x.equality
    )
    assert free == equations
    assert model.p["FOOD"].fixed
    assert not model.market_food.active
    assert model._cge_shockable == frozenset({"endowment"})


def test_multidimensional_parameter_compiles():
    doc = parse_text(
        r'''```cge
set rows = [A]
set cols = [X]
param a[A,X] = 1
var y >= 0
equation e: y = a[A,X]
fix y = 1
drop e
shockable a
```''',
        path="multi.cge.md",
    )
    model = compile_document(validate_document(doc))
    assert float(model.a["A", "X"]) == 1.0


def test_hyphenated_component_name_is_rejected_at_parse_time():
    import pytest
    from cge_core.spec import CGESpecError

    with pytest.raises(CGESpecError, match="Unsupported CGE statement"):
        parse_text("```cge\nvar x-y >= 0\n```", path="bad-name.cge.md")


def test_comparison_operator_has_named_error():
    import pytest
    from cge_core.spec import CGESpecError

    with pytest.raises(CGESpecError, match="Comparison operators"):
        parse_text(
            "```cge\nvar x >= 0\nvar y >= 0\nequation e: x >= y\n```",
            path="comparison.cge.md",
        )


def test_parameter_only_equation_is_rejected():
    import pytest
    from cge_core.spec import CGESpecError

    doc = validate_document(
        parse_text(
            r'''```cge
param a = 1
param b = 1
equation e: a = b
```''',
            path="param-only.cge.md",
        )
    )
    with pytest.raises(CGESpecError, match="contains no decision variable"):
        compile_document(doc)


def test_set_member_component_collision_is_rejected():
    import pytest
    from cge_core.spec import CGESpecError

    doc = parse_text(
        r'''```cge
set g = [FOOD]
var FOOD >= 0
```''',
        path="collision.cge.md",
    )
    with pytest.raises(CGESpecError, match="collides with declared"):
        validate_document(doc)
