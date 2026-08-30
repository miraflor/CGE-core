import sys
import types
from pathlib import Path


def test_ampl_ipopt_uses_pyomo_nl_driver(monkeypatch, tmp_path):
    from cge_core import solver as solvers

    executable = tmp_path / "ipopt"
    executable.write_text("fake", encoding="utf-8")
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
        lambda name: registered.setdefault("name", name) or FakeExecutable(),
    )

    # Correct the helper above: return an object while recording the key.
    def executable_factory(name):
        registered["name"] = name
        return FakeExecutable()

    monkeypatch.setattr(solvers, "Executable", executable_factory)
    monkeypatch.setattr(
        solvers,
        "_probe",
        lambda name: name == "ipoptnl"
        and registered.get("name") == "ipoptnl"
        and registered.get("path") == str(Path(executable).resolve()),
    )

    assert solvers._activate_ampl_ipopt() is True
    assert registered["name"] == "ipoptnl"
    assert registered["path"] == str(Path(executable).resolve())


def test_default_fresh_environment_falls_back_to_ampl_nl(monkeypatch):
    from cge_core import solver as solvers

    calls = []
    monkeypatch.setattr(solvers, "_probe", lambda name: False)
    monkeypatch.setattr(
        solvers, "_activate_ampl_ipopt",
        lambda: calls.append("activate") or False,
    )
    monkeypatch.setattr(
        solvers, "_install_default_solver",
        lambda: calls.append("install") or "ipoptnl",
    )

    assert solvers.resolve_solver() == "ipoptnl"
    assert calls == ["activate", "install"]


def test_explicit_ipopt_can_resolve_to_ampl_ipoptnl(monkeypatch):
    from cge_core import solver as solvers

    monkeypatch.setattr(solvers, "_probe", lambda name: False)
    monkeypatch.setattr(solvers, "_activate_ampl_ipopt", lambda: True)

    assert solvers.resolve_solver("ipopt") == "ipoptnl"
