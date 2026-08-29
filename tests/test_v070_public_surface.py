from pathlib import Path

import pytest

def test_version_and_public_entry_points():
    import cge_core

    assert cge_core.__version__ == "0.7.0"
    for name in ("SimpleCGE", "StandardCGE", "CamCGE", "IFPRICGE"):
        assert hasattr(cge_core, name)

def test_default_solver_resolution_provisions_internally(monkeypatch):
    from cge_core import solvers

    monkeypatch.setattr(solvers, "_probe", lambda _name: False)
    monkeypatch.setattr(solvers, "_activate_ampl_ipopt", lambda: False)
    monkeypatch.setattr(solvers, "_install_default_solver", lambda: "ipopt")

    assert solvers.resolve_solver() == "ipopt"

def test_explicit_solver_choice_does_not_silently_install_or_substitute(monkeypatch):
    from cge_core import solvers

    installed = {"called": False}

    monkeypatch.setattr(solvers, "_probe", lambda _name: False)
    monkeypatch.setattr(solvers, "_activate_ampl_ipopt", lambda: False)

    def unexpected_install():
        installed["called"] = True
        return "ipopt"

    monkeypatch.setattr(solvers, "_install_default_solver", unexpected_install)

    with pytest.raises(solvers.SolverResolutionError, match="requested solver"):
        solvers.resolve_solver("cyipopt")

    assert installed["called"] is False

def test_explicit_standard_metadata_has_no_name_heuristic():
    from cge_core.model_spec import STANDARD_SPEC

    assert "sam" in STANDARD_SPEC.benchmark_only
    assert "F0" in STANDARD_SPEC.benchmark_only
    assert "FF" in STANDARD_SPEC.base_protected
    assert STANDARD_SPEC.semantic_shocks["tariff"] == "taum"
    source = (Path(__file__).parents[1] / "cge_core" / "modern_engine.py").read_text()
    assert 'endswith("0")' not in source
    assert "endswith('0')" not in source

def test_default_closures_are_model_owned():
    from cge_core.model_spec import CAM_SPEC, SIMPLE_SPEC, STANDARD_SPEC

    assert SIMPLE_SPEC.default_numeraire == ("pf", "LAB")
    assert STANDARD_SPEC.default_redundant == ("eqpf", "LAB")
    assert CAM_SPEC.default_numeraire == ("mps", None)
    assert CAM_SPEC.default_redundant == ("caeq", None)

def test_cam_benchmark_protection_explicitly_preserves_v06_suffix_zero_guard():
    from cge_core.model_spec import CAM_SPEC

    expected = frozenset({
        "gr0", "cdtot0", "wa0", "mps0", "tm0", "m0", "e0", "xd0",
        "pd0", "pm0", "pe0", "pwe0", "pva0", "xxd0", "dst0", "id0",
        "ls0", "x0", "int0", "y0",
    })
    assert CAM_SPEC.benchmark_only == expected
    assert "tm" not in CAM_SPEC.benchmark_only
