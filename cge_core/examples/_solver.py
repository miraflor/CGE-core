# -*- coding: utf-8 -*-
"""Local NLP solver detection shared by the bundled examples."""
from pyomo.environ import SolverFactory

_CANDIDATES = ('ipopt', 'cyipopt')


def detect_solver(preferred=None):
    """Return the name of an available local NLP solver.

    Parameters
    ----------
    preferred : str, optional
        Try this solver first (e.g. 'cyipopt'). Falls back to the standard
        candidates if it is not available.

    Raises
    ------
    RuntimeError
        If no local NLP solver can be found, with installation guidance.
    """
    names = ([preferred] if preferred else []) + list(_CANDIDATES)
    for name in names:
        try:
            if SolverFactory(name).available(exception_flag=False):
                return name
        except Exception:
            continue
    raise RuntimeError(
        "No local NLP solver found. CGE-Core needs one of:\n"
        "  * an 'ipopt' executable on PATH "
        "(conda install -c conda-forge ipopt), or\n"
        "  * cyipopt (pip install 'cge-core[solver]'; requires the IPOPT "
        "system library and a PyNumero ASL build)."
    )
