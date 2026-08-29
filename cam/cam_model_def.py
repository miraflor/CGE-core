"""Compatibility import path; implementation moved to ``cge_core.models.camcge.model``."""
from importlib import import_module as _import_module
import sys as _sys

_impl = _import_module("cge_core.models.camcge.model")
_sys.modules[__name__] = _impl
