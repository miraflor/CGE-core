"""Compatibility import path; implementation moved to ``cge_core.models.ifpri.reporting``."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("cge_core.models.ifpri.reporting")
_sys.modules[__name__] = _impl
