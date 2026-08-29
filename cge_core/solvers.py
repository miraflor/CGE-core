"""One solver-resolution policy for the v0.7 public modelling system."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import os
from pathlib import Path
import platform
from typing import Optional


class SolverResolutionError(RuntimeError):
    """Raised before a solve when no supported local NLP backend is usable."""


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
    """Expose an already-installed AMPL COIN Ipopt module to Pyomo.

    This is infrastructure below the practitioner API.  It never installs
    anything; it only makes an existing optional solver module discoverable.
    """
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


def install_solver() -> str:
    """Install the default open-source NLP backend when no solver is present.

    The optional ``cge-core[solver]`` extra supplies ``amplpy``.  This helper
    asks AMPL Modules to install the open-source COIN bundle containing Ipopt,
    then hides module-path plumbing from ordinary model code.  Existing local
    IPOPT/cyipopt installations are used unchanged.
    """
    try:
        return resolve_solver()
    except SolverResolutionError:
        pass
    try:
        from amplpy import modules
    except Exception as exc:
        raise SolverResolutionError(
            "Automatic solver setup needs the optional installer dependency. "
            "Run `pip install \"cge-core[solver]\"`, then call "
            "`cge install-solver` again."
        ) from exc
    try:
        modules.install("coin")
    except Exception as exc:
        raise SolverResolutionError(
            "Could not install the open-source COIN/Ipopt module automatically. "
            "Run `cge doctor` and use a platform-supported IPOPT installation."
        ) from exc
    if _activate_ampl_ipopt():
        return "ipopt"
    raise SolverResolutionError(
        "The COIN module installation completed, but IPOPT was not usable by "
        "Pyomo. Run `cge doctor` for diagnostics."
    )


def resolve_solver(preferred: Optional[str] = None) -> str:
    """Return a usable supported solver name, or raise an actionable error."""
    candidates = (preferred,) if preferred else ("ipopt", "cyipopt")
    for candidate in candidates:
        if candidate and _probe(candidate):
            return candidate
    if preferred in (None, "ipopt") and _activate_ampl_ipopt():
        return "ipopt"
    requested = preferred or "ipopt or cyipopt"
    raise SolverResolutionError(
        f"CGE-Core could not find a usable local NLP solver ({requested}). "
        "Run `cge install-solver` after installing `cge-core[solver]`, or "
        "provide an existing IPOPT/cyipopt backend. Ordinary model code does "
        "not need a solver name once a backend is available."
    )


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
