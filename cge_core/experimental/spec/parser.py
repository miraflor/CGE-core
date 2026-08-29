"""Handwritten, deliberately small parser for fenced `cge` blocks."""
from __future__ import annotations

import re
from pathlib import Path

from .ast import (
    DataDecl, DropStmt, EquationDecl, FixStmt, Location, ModelDocument,
    ParamDecl, SetDecl, ShockableDecl, VarDecl,
)
from .errors import CGESpecError

_NAME = r"[A-Za-z_][A-Za-z0-9_]*"
_SET_RE = re.compile(rf"^set\s+({_NAME})\s*=\s*\[(.*)\]\s*$")
_DATA_RE = re.compile(rf'^data\s+({_NAME})\s*=\s*["\']([^"\']+)["\']\s*$')
_PARAM_RE = re.compile(rf"^param\s+({_NAME})(?:\[([^\]]+)\])?\s*=\s*(.+)$")
_VAR_RE = re.compile(
    rf"^var\s+({_NAME})(?:\[({_NAME})\s+in\s+({_NAME})\])?"
    r"(?:\s*(>=|>)\s*(-?\d+(?:\.\d+)?))?"
    r"(?:\s*(<=|<)\s*(-?\d+(?:\.\d+)?))?\s*$"
)
_EQ_RE = re.compile(rf"^equation\s+({_NAME})\s*:\s*(.*)$")
_FIX_RE = re.compile(r"^fix\s+(.+?)\s*=\s*(.+)$")
_DROP_RE = re.compile(r"^drop\s+(.+?)\s*$")
_SHOCK_RE = re.compile(r"^shockable\s+(.+)$")


def _blocks(text: str, path: str):
    lines = text.splitlines()
    in_block = False
    block = []
    start = 1
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not in_block and stripped.startswith("```cge"):
            in_block = True
            block = []
            start = number + 1
            continue
        if in_block and stripped.startswith("```"):
            yield start, block
            in_block = False
            continue
        if in_block:
            block.append((number, raw))
    if in_block:
        raise CGESpecError("Unclosed fenced `cge` block.", path=path, line=start)


def parse_text(text: str, *, path: str = "<model>") -> ModelDocument:
    doc = ModelDocument(path=path)
    for _, block in _blocks(text, path):
        doc.executable_blocks.append("\n".join(raw for _, raw in block))
        i = 0
        while i < len(block):
            line_no, raw = block[i]
            stripped = raw.strip()
            i += 1
            if not stripped or stripped.startswith("#"):
                continue
            loc = Location(path, line_no, max(1, len(raw) - len(raw.lstrip()) + 1))

            match = _SET_RE.match(stripped)
            if match:
                members = tuple(x.strip() for x in match.group(2).split(",") if x.strip())
                doc.sets.append(SetDecl(match.group(1), members, loc))
                continue
            match = _DATA_RE.match(stripped)
            if match:
                doc.data.append(DataDecl(match.group(1), match.group(2), loc))
                continue
            match = _PARAM_RE.match(stripped)
            if match:
                doc.parameters.append(ParamDecl(match.group(1), match.group(2), match.group(3).strip(), loc))
                continue
            match = _VAR_RE.match(stripped)
            if match:
                lower = float(match.group(5)) if match.group(5) is not None else None
                upper = float(match.group(7)) if match.group(7) is not None else None
                doc.variables.append(VarDecl(
                    name=match.group(1), binder=match.group(2), set_name=match.group(3),
                    lower=lower, lower_strict=match.group(4) == ">",
                    upper=upper, upper_strict=match.group(6) == "<", location=loc,
                ))
                continue
            match = _EQ_RE.match(stripped)
            if match:
                expression = match.group(2).strip()
                if not expression:
                    continuation = []
                    while i < len(block):
                        _, candidate = block[i]
                        if not candidate.strip():
                            i += 1
                            continue
                        if len(candidate) == len(candidate.lstrip()):
                            break
                        continuation.append(candidate.strip())
                        i += 1
                    expression = " ".join(continuation)
                if any(op in expression for op in ("==", ">=", "<=", "!=")):
                    raise CGESpecError(
                        "Equations use one standalone `=`. Comparison operators "
                        "(`==`, `>=`, `<=`, `!=`) are not supported.",
                        path=path, line=line_no,
                    )
                equality = re.findall(r"(?<![<>=!])=(?!=)", expression)
                if len(equality) != 1:
                    raise CGESpecError(
                        "Equation must contain exactly one standalone equality sign (`=`).",
                        path=path, line=line_no,
                    )
                split = re.search(r"(?<![<>=!])=(?!=)", expression)
                lhs, rhs = expression[:split.start()], expression[split.end():]
                doc.equations.append(EquationDecl(match.group(1), lhs.strip(), rhs.strip(), loc))
                continue
            match = _FIX_RE.match(stripped)
            if match:
                doc.fixes.append(FixStmt(match.group(1).strip(), match.group(2).strip(), loc))
                continue
            match = _DROP_RE.match(stripped)
            if match:
                doc.drops.append(DropStmt(match.group(1).strip(), loc))
                continue
            match = _SHOCK_RE.match(stripped)
            if match:
                names = tuple(x.strip() for x in match.group(1).split(",") if x.strip())
                doc.shockables.append(ShockableDecl(names, loc))
                continue
            raise CGESpecError(
                f"Unsupported CGE statement: {stripped!r}",
                path=path, line=line_no, column=loc.column,
            )
    return doc


def parse_file(path) -> ModelDocument:
    path = Path(path)
    return parse_text(path.read_text(encoding="utf-8"), path=str(path))
