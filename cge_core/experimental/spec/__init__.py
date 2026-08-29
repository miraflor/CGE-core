"""Experimental human-readable CGE specification.

Syntax may evolve before 1.0.  Markdown prose is inert; only fenced `cge`
blocks are executable.
"""
from .compiler import compile_document
from .errors import CGESpecError
from .parser import parse_file, parse_text
from .validation import validate_document

__all__ = [
    "CGESpecError", "parse_file", "parse_text", "validate_document",
    "compile_document",
]
