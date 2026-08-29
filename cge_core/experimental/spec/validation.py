"""Semantic validation for the experimental .cge.md AST."""
from __future__ import annotations

import re

from .errors import CGESpecError

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TARGET_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?$")


def validate_document(doc):
    names = {}

    def declare(name, location, kind):
        if name in names:
            old_kind, old_loc = names[name]
            raise CGESpecError(
                f"Duplicate declaration `{name}`; already declared as {old_kind} "
                f"at line {old_loc.line}.",
                path=location.path, line=location.line, column=location.column,
            )
        names[name] = (kind, location)

    for item in doc.sets:
        declare(item.name, item.location, "set")
        if not item.members or len(set(item.members)) != len(item.members):
            raise CGESpecError(
                f"Set `{item.name}` must contain unique members.",
                path=item.location.path, line=item.location.line,
            )
        invalid_members = [member for member in item.members if not _NAME_RE.match(member)]
        if invalid_members:
            raise CGESpecError(
                f"Set `{item.name}` contains member(s) that are not valid grammar-0 "
                f"identifiers: {invalid_members}.",
                path=item.location.path, line=item.location.line,
            )
    for item in doc.data:
        declare(item.name, item.location, "data")
    # Repeated concrete-index parameter assignments are allowed.
    param_names = set()
    for item in doc.parameters:
        if item.name not in param_names:
            if item.name in names:
                raise CGESpecError(
                    f"Duplicate declaration `{item.name}`.",
                    path=item.location.path, line=item.location.line,
                )
            names[item.name] = ("parameter", item.location)
            param_names.add(item.name)
    for item in doc.variables:
        declare(item.name, item.location, "variable")
        if item.set_name and item.set_name not in {x.name for x in doc.sets}:
            raise CGESpecError(
                f"Unknown set `{item.set_name}` in variable `{item.name}`.",
                path=item.location.path, line=item.location.line,
            )
    equation_names = set()
    for item in doc.equations:
        if item.name in equation_names:
            raise CGESpecError(
                f"Duplicate equation `{item.name}`.",
                path=item.location.path, line=item.location.line,
            )
        equation_names.add(item.name)

    declared_names = set(names)
    for set_decl in doc.sets:
        for member in set_decl.members:
            if member in declared_names:
                kind, declared_at = names[member]
                raise CGESpecError(
                    f"Set member `{member}` collides with declared {kind} `{member}` "
                    f"at line {declared_at.line}.",
                    path=set_decl.location.path, line=set_decl.location.line,
                )

    variable_names = {x.name for x in doc.variables}
    declared_components = variable_names | param_names
    for item in doc.fixes:
        match = _TARGET_RE.match(item.target)
        if not match or match.group(1) not in variable_names:
            raise CGESpecError(
                f"Closure fix targets unknown variable `{item.target}`.",
                path=item.location.path, line=item.location.line,
            )
    for item in doc.drops:
        target = item.target.split("[", 1)[0]
        if target not in equation_names:
            raise CGESpecError(
                f"Closure drop targets unknown equation `{item.target}`.",
                path=item.location.path, line=item.location.line,
            )
    for group in doc.shockables:
        for name in group.names:
            if name not in declared_components:
                raise CGESpecError(
                    f"Shockable declaration references unknown component `{name}`.",
                    path=group.location.path, line=group.location.line,
                )
    return doc
