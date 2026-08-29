"""Central solver policy for CGE-Core v0.7.

Ordinary users call ``.solve()``. Solver discovery and first-use setup remain
below the practitioner API. Advanced users may still request a backend
explicitly with ``.solve(solver="ipopt")``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import platform
from typing import Optional

from pyomo.common import Executable


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


def _ampl_ipopt_path() -> Optional[Path]:
    try:
        from amplpy import modules

        executable = Path(modules.find("ipopt")).resolve()
    except Exception:
        return None
    return executable if executable.is_file() else None


def _activate_ampl_ipopt() -> bool:
    """Register AMPL's Ipopt driver through Pyomo's NL solver interface.

    AMPL solver modules are NL/ASL solver drivers.  Pyomo's documented route
    for these binaries is ``SolverFactory("ipoptnl", executable=..., solve_io="nl")``.
    Registering the module binary as a normal ``ipopt`` executable is not
    sufficient and is the bug that broke fresh Colab runtimes.
    """
    executable = _ampl_ipopt_path()
    if executable is None:
        return False

    try:
        # Pyomo's `ipoptnl` plugin looks up the executable through the
        # Executable registry when instantiated without an explicit path.
        Executable("ipoptnl").set_path(str(executable))
    except Exception:
        return False

    return _probe("ipoptnl")


def _install_default_solver() -> str:
    """Install and register the default open-source NLP backend on first use."""
    try:
        from amplpy import modules
    except Exception as exc:
        raise SolverResolutionError(
            "CGE-Core could not prepare its default NLP solver because the "
            "solver-support dependency is missing."
        ) from exc

    try:
        installed = set(modules.installed())
    except Exception:
        installed = set()

    try:
        if "coin" not in installed:
            modules.install("coin")
    except Exception as exc:
        raise SolverResolutionError(
            "CGE-Core could not install its default open-source NLP solver. "
            "Check network access or choose an already installed solver."
        ) from exc

    if _activate_ampl_ipopt():
        return "ipoptnl"

    raise SolverResolutionError(
        "CGE-Core installed the COIN solver bundle, but Pyomo could not use "
        "its Ipopt NL driver."
    )


def resolve_solver(preferred: Optional[str] = None) -> str:
    """Return a solver name usable by Pyomo.

    Priority without an explicit preference:
      1. a normal system ``ipopt``;
      2. a working ``cyipopt``;
      3. AMPL's COIN Ipopt through Pyomo's ``ipoptnl`` interface.

    ``preferred="ipopt"`` means "use Ipopt"; if a system executable is absent,
    the AMPL NL driver is an acceptable implementation of that same solver.
    """
    if preferred:
        if _probe(preferred):
            return preferred
        if preferred == "ipopt":
            if _activate_ampl_ipopt():
                return "ipoptnl"
            try:
                return _install_default_solver()
            except SolverResolutionError:
                pass
        raise SolverResolutionError(
            f"The requested solver {preferred!r} is not usable in this environment."
        )

    if _probe("ipopt"):
        return "ipopt"
    if _probe("cyipopt"):
        return "cyipopt"
    if _activate_ampl_ipopt():
        return "ipoptnl"
    return _install_default_solver()


def install_solver() -> str:
    """Compatibility helper; ordinary users should simply call ``.solve()``."""
    return resolve_solver()


def solver_info(preferred: Optional[str] = None) -> SolverInfo:
    selected = None
    detail = ""
    try:
        selected = resolve_solver(preferred)
        detail = "usable"
    except SolverResolutionError as exc:
        detail = str(exc)

    return SolverInfo(
        selected=selected,
        ipopt=_probe("ipopt") or _probe("ipoptnl"),
        cyipopt=_probe("cyipopt"),
        python=platform.python_version(),
        platform=platform.platform(),
        detail=detail,
    )
