"""Central solver policy for the v0.7 public modelling system.

Ordinary users call ``.solve()``.  Solver discovery and first-use setup are
infrastructure below the practitioner API.  Advanced users may still request a
specific backend explicitly with ``.solve(solver="ipopt")``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import os
from pathlib import Path
import platform
from typing import Optional


class SolverResolutionError(RuntimeError):
    """Raised before a solve when no supported NLP backend can be made usable."""


@dataclass(frozen=True)
class SolverInfo:
    selected: Optional[str]
    ipopt: bool
    cyipopt: bool
    python: str
    platform: str
    detail: str = ""

    def as_dict(self):
        return asdict(self)


def _probe(name: str) -> bool:
    try:
        from pyomo.environ import SolverFactory

        if not SolverFactory(name).available(exception_flag=False):
            return False
        if name == "cyipopt":
            if importlib.util.find_spec("scipy") is None:
                return False
            from pyomo.contrib.pynumero.asl import AmplInterface

            if not AmplInterface.available():
                return False
        return True
    except Exception:
        return False


def _activate_ampl_ipopt() -> bool:
    """Expose an already-installed AMPL COIN Ipopt module to Pyomo."""
    try:
        from amplpy import modules

        executable = Path(modules.find("ipopt")).resolve()
    except Exception:
        return False
    if not executable.is_file():
        return False

    parent = str(executable.parent)
    current = os.environ.get("PATH", "")
    pieces = current.split(os.pathsep) if current else []
    if parent not in pieces:
        os.environ["PATH"] = parent + (os.pathsep + current if current else "")
    return _probe("ipopt")


def _install_default_solver() -> str:
    """Prepare CGE-Core's default open-source NLP backend on first use."""
    try:
        from amplpy import modules
    except Exception as exc:
        raise SolverResolutionError(
            "CGE-Core could not prepare its default NLP solver because the "
            "solver-support dependency is missing. Reinstall CGE-Core, or use "
            "an existing supported solver explicitly."
        ) from exc

    try:
        modules.install("coin")
    except Exception as exc:
        raise SolverResolutionError(
            "CGE-Core could not prepare its default open-source NLP solver "
            "automatically. Check network access, or use an existing supported "
            "solver explicitly with .solve(solver=...)."
        ) from exc

    if _activate_ampl_ipopt():
        return "ipopt"

    raise SolverResolutionError(
        "CGE-Core prepared the default COIN solver bundle, but IPOPT was not "
        "usable by Pyomo. Advanced users can inspect the environment with "
        "`cge doctor` or supply a supported solver explicitly."
    )


def resolve_solver(preferred: Optional[str] = None) -> str:
    """Return a usable solver.

    With no explicit preference, CGE-Core first uses an existing supported
    backend and, if necessary, prepares its default Ipopt backend automatically.
    If an advanced user explicitly requests a solver, CGE-Core does not silently
    substitute or install a different backend.
    """
    candidates = (preferred,) if preferred else ("ipopt", "cyipopt")
    for candidate in candidates:
        if candidate and _probe(candidate):
            return candidate

    # An AMPL solver module may already be installed but not yet exposed on PATH.
    if preferred in (None, "ipopt") and _activate_ampl_ipopt():
        return "ipopt"

    # First-use setup belongs below the ordinary .solve() interface.
    if preferred is None:
        return _install_default_solver()

    raise SolverResolutionError(
        f"The requested solver {preferred!r} is not usable in this environment. "
        "Install/configure that backend or omit solver= to use CGE-Core's "
        "automatic default."
    )


def install_solver() -> str:
    """Compatibility helper for explicit environment setup.

    Ordinary users should not need this function: ``.solve()`` performs default
    solver setup automatically when required.
    """
    return resolve_solver()


def solver_info(preferred: Optional[str] = None) -> SolverInfo:
    _activate_ampl_ipopt()
    ipopt = _probe("ipopt")
    cyipopt = _probe("cyipopt")

    selected = None
    if preferred:
        selected = preferred if _probe(preferred) else None
    elif ipopt:
        selected = "ipopt"
    elif cyipopt:
        selected = "cyipopt"

    if selected:
        detail = "usable"
    elif preferred and (ipopt or cyipopt):
        alternatives = ", ".join(
            name for name, ok in (("ipopt", ipopt), ("cyipopt", cyipopt)) if ok
        )
        detail = (
            f"requested solver {preferred!r} is unavailable; "
            f"usable alternative(s): {alternatives}"
        )
    else:
        detail = "no supported local NLP solver detected"

    return SolverInfo(
        selected=selected,
        ipopt=ipopt,
        cyipopt=cyipopt,
        python=platform.python_version(),
        platform=platform.platform(),
        detail=detail,
    )
