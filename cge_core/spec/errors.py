"""Source-located errors for .cge.md parsing and semantic checks."""
from __future__ import annotations


class CGESpecError(ValueError):
    def __init__(self, message: str, *, path: str = "<model>", line: int = 1,
                 column: int = 1):
        super().__init__(message)
        self.path = path
        self.line = line
        self.column = column

    def __str__(self):
        return f"{self.path}:{self.line}:{self.column}\n\n{super().__str__()}"
