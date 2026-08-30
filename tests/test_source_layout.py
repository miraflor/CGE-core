from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_primary_source_layout_is_obvious():
    required = [
        "cge_core/workflow.py",
        "cge_core/solver.py",
        "cge_core/sam.py",
        "cge_core/_engine.py",
        "cge_core/_pycge.py",
        "cge_core/models/simple/model.py",
        "cge_core/models/standard/model.py",
        "cge_core/models/camcge/model.py",
        "cge_core/models/camcge/data",
        "cge_core/models/ifpri/model.py",
        "cge_core/experimental/authoring",
        "cge_core/experimental/spec",
    ]
    for path in required:
        assert (ROOT / path).exists(), path


def test_obsolete_pre_v08_import_surfaces_do_not_return():
    forbidden = [
        "cge_core/_alias.py", "cge_core/compat", "cge_core/api.py",
        "cge_core/engine.py", "cge_core/modern_engine.py", "cge_core/solvers.py",
        "cge_core/samtools.py", "cge_core/practitioner.py", "cge_core/ifpri",
        "cge_core/spec", "cge_core/authoring",
        "cge_core/examples/splcge_model_def.py",
        "cge_core/examples/stdcge_model_def.py", "cam",
    ]
    offenders = [path for path in forbidden if (ROOT / path).exists()]
    assert offenders == []


def test_no_sys_modules_redirect_shims_remain():
    offenders = []
    for path in (ROOT / "cge_core").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "sys.modules[__name__]" in source or "alias_module(__name__" in source:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_real_model_definitions_are_not_stored_as_examples():
    assert (ROOT / "cge_core/models/simple/model.py").stat().st_size > 5000
    assert (ROOT / "cge_core/models/standard/model.py").stat().st_size > 5000
    assert (ROOT / "cge_core/models/camcge/model.py").stat().st_size > 5000


def test_test_names_describe_behavior_not_release_history():
    bad_tokens = ("_v06", "_v070", "compat", "phase6", "review_hardening")
    offenders = [
        p.name for p in (ROOT / "tests").glob("test_*.py")
        if any(token in p.name for token in bad_tokens)
    ]
    assert offenders == []


def test_intentional_lower_level_api_remains_available_at_top_level():
    from cge_core import CGE, PyCGE, SimpleCGE, StandardCGE
    from cge_core._pycge import PyCGE as EnginePyCGE

    assert PyCGE is EnginePyCGE
    assert CGE is not None
    assert SimpleCGE is not None
    assert StandardCGE is not None
