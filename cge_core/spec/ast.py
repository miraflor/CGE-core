"""AST nodes for the experimental deterministic .cge.md specification."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Location:
    path: str
    line: int
    column: int = 1


@dataclass(frozen=True)
class SetDecl:
    name: str
    members: tuple[str, ...]
    location: Location


@dataclass(frozen=True)
class DataDecl:
    name: str
    path: str
    location: Location


@dataclass(frozen=True)
class ParamDecl:
    name: str
    index: Optional[str]
    expression: str
    location: Location


@dataclass(frozen=True)
class VarDecl:
    name: str
    binder: Optional[str]
    set_name: Optional[str]
    lower: Optional[float]
    lower_strict: bool
    upper: Optional[float]
    upper_strict: bool
    location: Location


@dataclass(frozen=True)
class EquationDecl:
    name: str
    lhs: str
    rhs: str
    location: Location


@dataclass(frozen=True)
class FixStmt:
    target: str
    expression: str
    location: Location


@dataclass(frozen=True)
class DropStmt:
    target: str
    location: Location


@dataclass(frozen=True)
class ShockableDecl:
    names: tuple[str, ...]
    location: Location


@dataclass
class ModelDocument:
    path: str
    sets: list[SetDecl] = field(default_factory=list)
    data: list[DataDecl] = field(default_factory=list)
    parameters: list[ParamDecl] = field(default_factory=list)
    variables: list[VarDecl] = field(default_factory=list)
    equations: list[EquationDecl] = field(default_factory=list)
    fixes: list[FixStmt] = field(default_factory=list)
    drops: list[DropStmt] = field(default_factory=list)
    shockables: list[ShockableDecl] = field(default_factory=list)
    executable_blocks: list[str] = field(default_factory=list)

    @property
    def source_path(self) -> Path:
        return Path(self.path)
