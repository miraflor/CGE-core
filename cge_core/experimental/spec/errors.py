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


# ---------------------------------------------------------------------------
# Shared patterns for reading a .cge.md document
# ---------------------------------------------------------------------------
# A "grammar-0 identifier" is what a name in a model document is allowed to look
# like: a letter or underscore, then any mix of letters, digits and underscores.
# It is the same rule Python itself uses for names, and it is deliberately
# strict so that a model document cannot contain a name that later turns out to
# be unusable.
#
# This pattern, and the one for a name with an optional index after it such as
# ``price[BRD]``, were each written out separately in three files.  Three
# separately maintained copies of one rule is three chances for them to stop
# agreeing about what a valid name is.
NAME_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"
TARGET_PATTERN = r"^(%s)(?:\[([^\]]+)\])?$" % NAME_PATTERN
