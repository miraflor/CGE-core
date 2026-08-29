"""Compatibility import path; implementation moved to ``cge_core.models.standard.model``."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("cge_core.models.standard.model")
_sys.modules[__name__] = _impl
