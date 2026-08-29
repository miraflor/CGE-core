import os
import sys
import types
from pathlib import Path


def test_ampl_ipopt_registration_replaces_cached_missing_executable(
    monkeypatch, tmp_path
):
    """A newly installed AMPL Ipopt must become visible in the same process."""
    from cge_core import solvers

    executable = tmp_path / ("ipopt.exe" if os.name == "nt" else "ipopt")
    executable.write_text("fake", encoding="utf-8")
    if os.name != "nt":
        executable.chmod(0o755)

    fake_modules = types.SimpleNamespace(find=lambda name: str(executable))
    fake_amplpy = types.ModuleType("amplpy")
    fake_amplpy.modules = fake_modules
    monkeypatch.setitem(sys.modules, "amplpy", fake_amplpy)

    registered = {}

    class FakeExecutable:
        def set_path(self, value):
            registered["path"] = value

    monkeypatch.setattr(
        solvers,
        "Executable",
        lambda name: FakeExecutable(),
    )
    monkeypatch.setattr(
        solvers,
        "_probe",
        lambda name: (
            name == "ipopt"
            and registered.get("path") == str(Path(executable).resolve())
        ),
    )

    original_path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", original_path)

    assert solvers._activate_ampl_ipopt() is True
    assert registered["path"] == str(Path(executable).resolve())
    assert str(executable.parent.resolve()) in os.environ["PATH"].split(os.pathsep)


def test_default_install_registers_coin_ipopt_before_returning(monkeypatch):
    from cge_core import solvers

    calls = []

    class FakeModules:
        @staticmethod
        def installed():
            calls.append("installed")
            return []

        @staticmethod
        def install(name):
            calls.append(("install", name))

    fake_amplpy = types.ModuleType("amplpy")
    fake_amplpy.modules = FakeModules
    monkeypatch.setitem(sys.modules, "amplpy", fake_amplpy)
    monkeypatch.setattr(
        solvers,
        "_activate_ampl_ipopt",
        lambda: calls.append("activate") or True,
    )

    assert solvers._install_default_solver() == "ipopt"
    assert calls == ["installed", ("install", "coin"), "activate"]
