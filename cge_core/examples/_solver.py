# -*- coding: utf-8 -*-
"""Solver lookup for the bundled lower-level example scripts.

Examples use the same central solver policy as the practitioner API; they do
not maintain a second discovery or installation path.
"""
from cge_core.solver import SolverResolutionError, resolve_solver


def detect_solver(preferred=None):
    """Return the name of a solver this machine can actually run.

    Parameters
    ----------
    preferred : str, optional
        Ask for this solver by name, for example ``"ipopt"``.  If it is not
        usable directly, an equivalent backend may be substituted.

    Raises
    ------
    RuntimeError
        If no solver can be found or prepared.  The message comes from the
        solver policy itself, so it describes the actual reason rather than a
        generic guess.
    """
    try:
        return resolve_solver(preferred)
    except SolverResolutionError as exc:
        raise RuntimeError(str(exc)) from exc
