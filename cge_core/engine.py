"""Compatibility import path; implementation moved to ``cge_core.compat.pycge``."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("cge_core.compat.pycge")
_sys.modules[__name__] = _impl
