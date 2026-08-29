from pathlib import Path


def test_version_and_public_entry_points():
    import cge_core
    assert cge_core.__version__ == "0.7.0"
    for name in ("SimpleCGE", "StandardCGE", "CamCGE", "IFPRICGE", "install_solver"):
        assert hasattr(cge_core, name)


def test_explicit_standard_metadata_has_no_name_heuristic():
    from cge_core.model_spec import STANDARD_SPEC
    assert "sam" in STANDARD_SPEC.benchmark_only
    assert "F0" in STANDARD_SPEC.benchmark_only
    assert "FF" in STANDARD_SPEC.base_protected
    assert STANDARD_SPEC.semantic_shocks["tariff"] == "taum"
    source = (Path(__file__).parents[1] / "cge_core" / "modern_engine.py").read_text()
    assert "endswith(\"0\")" not in source
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
