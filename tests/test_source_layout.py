from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_primary_source_layout_is_obvious():
    required = [
        "cge_core/workflow.py",
        "cge_core/solver.py",
        "cge_core/sam.py",
        "cge_core/_engine.py",
        "cge_core/compat/pycge.py",
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

def test_historical_import_paths_are_shims_not_parallel_implementations():
    shims = [
        "cge_core/api.py",
        "cge_core/engine.py",
        "cge_core/modern_engine.py",
        "cge_core/solvers.py",
        "cge_core/samtools.py",
        "cge_core/practitioner.py",
        "cge_core/examples/splcge_model_def.py",
        "cge_core/examples/stdcge_model_def.py",
        "cam/cam_model_def.py",
    ]
    for path in shims:
        file = ROOT / path
        assert file.is_file(), path
        assert file.stat().st_size < 2000, f"{path} grew into a second implementation"

def test_real_model_definitions_are_not_stored_as_examples():
    assert (ROOT / "cge_core/models/simple/model.py").stat().st_size > 5000
    assert (ROOT / "cge_core/models/standard/model.py").stat().st_size > 5000
    assert (ROOT / "cge_core/models/camcge/model.py").stat().st_size > 5000

def test_test_names_describe_behavior_not_release_history():
    bad_tokens = ("_v06", "_v070", "phase6", "review_hardening")
    offenders = [
        p.name for p in (ROOT / "tests").glob("test_*.py")
        if any(token in p.name for token in bad_tokens)
    ]
    assert offenders == []

def test_compatibility_imports_resolve_to_canonical_objects():
    from cge_core import CGE, PyCGE, SimpleCGE, StandardCGE
    from cge_core.api import CGE as OldCGE
    from cge_core.engine import PyCGE as OldPyCGE
    from cge_core.practitioner import SimpleCGE as OldSimpleCGE
    from cge_core.practitioner import StandardCGE as OldStandardCGE
    from cge_core.examples.splcge_model_def import SplModelDef as OldSplModelDef
    from cge_core.examples.stdcge_model_def import StdModelDef as OldStdModelDef
    from cge_core.models.simple.model import SplModelDef
    from cge_core.models.standard.model import StdModelDef

    assert OldCGE is CGE
    assert OldPyCGE is PyCGE
    assert OldSimpleCGE is SimpleCGE
    assert OldStandardCGE is StandardCGE
    assert OldSplModelDef is SplModelDef
    assert OldStdModelDef is StdModelDef
