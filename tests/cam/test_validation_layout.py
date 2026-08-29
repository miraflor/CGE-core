from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_cam_validation_rebuilds_state_instead_of_serializing_engine():
    script = (ROOT / "validation" / "cam" / "replicate_base.py").read_text(
        encoding="utf-8"
    )
    assert "cge_base.dill" not in script
    assert "import dill" not in script


def test_cam_runtime_and_validation_have_distinct_homes():
    assert (ROOT / "cge_core" / "models" / "camcge" / "model.py").is_file()
    assert (ROOT / "cge_core" / "models" / "camcge" / "data").is_dir()
    assert (ROOT / "validation" / "cam" / "replicate_base.py").is_file()
    assert (ROOT / "validation" / "cam" / "replicate_experiments.py").is_file()
