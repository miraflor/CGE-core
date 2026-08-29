"""Narrow Pyomo compiler for the experimental .cge.md MVP."""
from __future__ import annotations

import ast
import math
import operator
import re
from pathlib import Path

from .errors import CGESpecError
from .validation import validate_document

_ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_TARGET = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?$")


def _matching_paren(text, start):
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unmatched parenthesis")


def _split_top_level(text, delimiter=","):
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == delimiter and depth == 0:
            return text[:i], text[i + 1:]
    raise ValueError("delimiter not found")


def _expand_aggregates(expr, env):
    counter = 0
    while True:
        matches = [(expr.find("sum("), "sum"), (expr.find("prod("), "prod")]
        matches = [(pos, kind) for pos, kind in matches if pos >= 0]
        if not matches:
            return expr, env
        start, kind = min(matches)
        open_pos = start + len(kind)
        close = _matching_paren(expr, open_pos)
        inner = expr[open_pos + 1:close]
        binder_text, body = _split_top_level(inner)
        binder_match = re.match(r"^\s*([A-Za-z_]\w*)\s+in\s+([A-Za-z_]\w*)\s*$", binder_text)
        if not binder_match:
            raise ValueError(f"Bad {kind} binder: {binder_text!r}")
        binder, set_name = binder_match.groups()
        if set_name not in env:
            raise NameError(set_name)
        values = []
        for member in list(env[set_name]):
            local = dict(env)
            local[binder] = member
            values.append(_safe_eval(body, local))
        if kind == "sum":
            aggregate = sum(values)
        else:
            aggregate = 1
            for item in values:
                aggregate *= item
        placeholder = f"_agg_{counter}"
        counter += 1
        env = dict(env)
        env[placeholder] = aggregate
        expr = expr[:start] + placeholder + expr[close + 1:]


def _eval_node(node, env):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in env:
            raise NameError(node.id)
        return env[node.id]
    if isinstance(node, ast.Subscript):
        target = _eval_node(node.value, env)
        index = _eval_node(node.slice, env)
        return target[index]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(x, env) for x in node.elts)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](
            _eval_node(node.left, env), _eval_node(node.right, env)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        return _ALLOWED_UNARY[type(node.op)](_eval_node(node.operand, env))
    raise ValueError(f"Unsupported expression syntax: {ast.dump(node, include_attributes=False)}")


def _safe_eval(expr, env):
    expr, env = _expand_aggregates(expr, dict(env))
    tree = ast.parse(expr, mode="eval")
    return _eval_node(tree, env)


def _resolve_target(model, text, env):
    match = _TARGET.match(text.strip())
    if not match:
        raise ValueError(f"Bad target: {text!r}")
    name, raw_index = match.groups()
    component = getattr(model, name)
    if raw_index is None:
        return component
    index_text = raw_index.strip()
    if "," in index_text:
        parts = tuple(x.strip() for x in index_text.split(","))
        index = tuple(env.get(x, x) for x in parts)
    else:
        index = env.get(index_text, index_text)
    return component[index]


def compile_document(doc, *, base_dir=None):
    """Compile a validated document into one ConcreteModel.

    The MVP is intentionally narrow but deterministic: scalar equations,
    indexed/scalar variables, concrete indexed/scalar parameters, sum/prod,
    fix, drop, and shockability.  Unsupported syntax fails before solving.
    """
    validate_document(doc)
    try:
        from pyomo.environ import ConcreteModel, Constraint, Param, Set, Var
    except ImportError as exc:
        raise RuntimeError("Pyomo is required to compile .cge.md models.") from exc

    model = ConcreteModel()
    env = {}
    for decl in doc.sets:
        component = Set(initialize=list(decl.members), ordered=True)
        setattr(model, decl.name, component)
        env[decl.name] = component
        for member in decl.members:
            env.setdefault(member, member)

    # External data declarations are provenance-bearing references in grammar 0;
    # model expressions do not silently execute arbitrary file formats.
    model._cge_external_data = {
        item.name: str((Path(base_dir or ".") / item.path).resolve()) for item in doc.data
    }

    grouped = {}
    for decl in doc.parameters:
        grouped.setdefault(decl.name, []).append(decl)
    for name, declarations in grouped.items():
        scalar = all(x.index is None for x in declarations)
        if scalar:
            if len(declarations) != 1:
                raise CGESpecError(
                    f"Scalar parameter `{name}` is assigned more than once.",
                    path=declarations[0].location.path, line=declarations[0].location.line,
                )
            number = _safe_eval(declarations[0].expression, env)
            component = Param(initialize=float(number), mutable=True)
        else:
            if any(x.index is None for x in declarations):
                raise CGESpecError(
                    f"Parameter `{name}` mixes scalar and indexed assignments.",
                    path=declarations[0].location.path, line=declarations[0].location.line,
                )
            values = {}
            for item in declarations:
                parts = [x.strip() for x in item.index.strip().split(",")]
                if not all(parts):
                    raise CGESpecError(
                        f"Parameter `{name}` has an empty index position.",
                        path=item.location.path, line=item.location.line,
                    )
                key = (
                    tuple(env.get(x, x) for x in parts)
                    if len(parts) > 1 else env.get(parts[0], parts[0])
                )
                values[key] = float(_safe_eval(item.expression, env))
            component = Param(list(values), initialize=values, mutable=True)
        setattr(model, name, component)
        env[name] = component

    for decl in doc.variables:
        lb = decl.lower
        ub = decl.upper
        if lb is not None and decl.lower_strict:
            lb = math.nextafter(lb, math.inf)
        if ub is not None and decl.upper_strict:
            ub = math.nextafter(ub, -math.inf)
        if decl.set_name:
            component = Var(getattr(model, decl.set_name), bounds=(lb, ub), initialize=1.0)
        else:
            component = Var(bounds=(lb, ub), initialize=1.0)
        setattr(model, decl.name, component)
        env[decl.name] = component

    for decl in doc.equations:
        try:
            from pyomo.core.expr.visitor import identify_variables
            lhs = _safe_eval(decl.lhs, env)
            rhs = _safe_eval(decl.rhs, env)
            residual = lhs - rhs
            variables = (
                tuple(identify_variables(residual, include_fixed=True))
                if hasattr(residual, "is_expression_type")
                else ()
            )
            if not variables:
                raise CGESpecError(
                    f"Equation `{decl.name}` contains no decision variable; "
                    "parameter-only identities are not model constraints.",
                    path=decl.location.path, line=decl.location.line,
                )
        except CGESpecError:
            raise
        except Exception as exc:
            raise CGESpecError(
                f"Could not compile equation `{decl.name}`: {exc}",
                path=decl.location.path, line=decl.location.line,
            ) from exc
        setattr(model, decl.name, Constraint(expr=lhs == rhs))

    for stmt in doc.fixes:
        try:
            target = _resolve_target(model, stmt.target, env)
            target.fix(float(_safe_eval(stmt.expression, env)))
        except Exception as exc:
            raise CGESpecError(
                f"Could not apply closure fix `{stmt.target}`: {exc}",
                path=stmt.location.path, line=stmt.location.line,
            ) from exc
    for stmt in doc.drops:
        try:
            target = _resolve_target(model, stmt.target, env)
            target.deactivate()
        except Exception as exc:
            raise CGESpecError(
                f"Could not drop `{stmt.target}`: {exc}",
                path=stmt.location.path, line=stmt.location.line,
            ) from exc

    shockable = set()
    for group in doc.shockables:
        shockable.update(group.names)
    model._cge_shockable = frozenset(shockable)
    model._cge_spec_path = doc.path
    return model
