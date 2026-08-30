# -*- coding: utf-8 -*-
"""v0.8 policy adapter over the inherited PyCGE engine.

The economic model algebra remains in the model-definition classes. The
lower-level implementation in :mod:`cge_core._pycge` owns instance creation,
mutation, undo/rollback, solver execution, and result bookkeeping.

``CoreEngine`` changes one policy: component protection is declared explicitly
by each model's :class:`~cge_core.model_spec.ModelSpec` rather than inferred
from naming conventions such as a trailing ``0``. Keeping that difference in a
small subclass prevents the validated engine mechanics from being duplicated.
"""
from __future__ import annotations

import logging

from cge_core._pycge import PyCGE
from cge_core.model_spec import ModelSpec

logger = logging.getLogger(__name__)


class CoreEngine(PyCGE):
    """PyCGE with model-declared protection instead of name matching."""

    def __init__(self, model_def, spec: ModelSpec):
        super().__init__(model_def)
        self.model_spec = spec

    def _protection_error(self, name, base: bool):
        """Return an error message if this component must not be changed, else None.

        This replaces the older engine's spelling rule.  Two lists come from
        the model's own specification:

        ``benchmark_only``
            Numbers that describe the base-year economy the model was
            calibrated to.  They are inputs, not results, and changing them
            after the model is built cannot produce a meaningful answer on
            either instance.

        ``base_protected``
            Numbers that are held fixed on the benchmark instance but are an
            ordinary policy shock on the counterfactual instance.  A factor
            endowment is the usual example: the benchmark must reproduce the
            observed economy, but shocking the endowment is exactly the kind of
            experiment a counterfactual is for.
        """
        if name in self.model_spec.benchmark_only or (
            base and name in self.model_spec.base_protected
        ):
            scope = "BASE" if base else "SIM"
            return (
                f"{scope} component '{name}' is declared benchmark/base-protected "
                "by this model and cannot be modified in-place."
            )
        return None
